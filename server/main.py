from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv
from pypdf import PdfReader
from io import BytesIO
from datetime import datetime, timedelta
from psycopg2.extras import RealDictCursor
from psycopg2 import pool
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
import os
import json
import requests
import base64
import re
import psycopg2

load_dotenv()

app = FastAPI(title="StackPilot Enterprise API", version="1.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://stack-pilot-agentic.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Firebase Admin Init ──────────────────────────────────
# Reads the full service account JSON from environment variable
_raw_key = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")
if _raw_key:
    _cred_dict = json.loads(_raw_key)
    _cred = credentials.Certificate(_cred_dict)
    firebase_admin.initialize_app(_cred)
    print("Firebase Admin SDK Initialized Successfully.")
else:
    print("WARNING: FIREBASE_SERVICE_ACCOUNT_KEY not set. Token verification disabled.")


# ── Firebase Token Verifier ──────────────────────────────
def verify_firebase_token(id_token: str) -> str:
    """
    Verifies the Firebase ID token sent from the frontend.
    Returns the Firebase UID (uid) if valid.
    Raises HTTP 401 if invalid or expired.
    """
    if not id_token:
        return ""
    try:
        decoded = firebase_auth.verify_id_token(id_token)
        return decoded["uid"]
    except firebase_auth.ExpiredIdTokenError:
        raise HTTPException(status_code=401, detail="Firebase token has expired. Please sign in again.")
    except firebase_auth.InvalidIdTokenError:
        raise HTTPException(status_code=401, detail="Invalid Firebase token.")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")


client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# ── Connection Pool ──────────────────────────────────────
connection_pool = None


def init_pool():
    global connection_pool
    connection_pool = pool.ThreadedConnectionPool(
        minconn=2,
        maxconn=10,
        dsn=os.getenv("DATABASE_URL"),
        cursor_factory=RealDictCursor
    )


def get_db():
    return connection_pool.getconn()


def release_db(conn):
    connection_pool.putconn(conn)


def init_db():
    try:
        init_pool()
        conn = get_db()
        cur = conn.cursor()

        # NOTE: Column is still named clerk_id — no rename needed.
        # Firebase UID is stored here instead. Works identically.
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                clerk_id VARCHAR(255) UNIQUE NOT NULL,
                email VARCHAR(255),
                name VARCHAR(255),
                created_at TIMESTAMP DEFAULT NOW()
            );
            CREATE TABLE IF NOT EXISTS sessions (
                id SERIAL PRIMARY KEY,
                clerk_id VARCHAR(255) NOT NULL,
                tool VARCHAR(100) NOT NULL,
                input_summary TEXT,
                tokens_used INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        conn.commit()

        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_clerk_id ON sessions(clerk_id);
            CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at);
        """)
        conn.commit()

        try:
            cur.execute("ALTER TABLE sessions ADD COLUMN tokens_used INT DEFAULT 0;")
            conn.commit()
            print("Successfully patched DB: Added 'tokens_used' column.")
        except Exception:
            conn.rollback()

        cur.close()
        release_db(conn)
        print("Database Infrastructure Successfully Provisioned.")
    except Exception as e:
        print("Database Provisioning Engine Failure:", e)


init_db()


# ── Request Schemas ──────────────────────────────────────
class DebugRequest(BaseModel):
    code: str = ""
    error: str
    language: str = ""
    id_token: str = ""      # Frontend sends Firebase ID token


class CodeRequest(BaseModel):
    code: str
    language: str = ""
    id_token: str = ""      # Frontend sends Firebase ID token


class RepoRequest(BaseModel):
    repo_url: str
    goal: str = ""
    id_token: str = ""      # Frontend sends Firebase ID token


class UserSyncRequest(BaseModel):
    id_token: str           # Frontend sends Firebase ID token (required for sync)
    email: str = ""
    name: str = ""


# ── Session Logger ───────────────────────────────────────
def log_session(uid: str, tool: str, summary: str, tokens: int = 150):
    if not uid:
        return
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO sessions (clerk_id, tool, input_summary, tokens_used) VALUES (%s, %s, %s, %s)",
            (uid, tool, summary[:200], tokens)
        )
        conn.commit()
        cur.close()
    except Exception as e:
        print("Session Audit Logger Interrupted:", e)
    finally:
        if conn:
            release_db(conn)


# ── Root ─────────────────────────────────────────────────
@app.get("/")
async def root():
    return {"app": "StackPilot Platform Control Engine", "status": "active_operational"}


# ── User Sync ────────────────────────────────────────────
@app.post("/api/sync-user")
async def sync_user(req: UserSyncRequest):
    uid = verify_firebase_token(req.id_token)
    if not uid:
        raise HTTPException(status_code=401, detail="Valid Firebase token required for sync.")

    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (clerk_id, email, name)
            VALUES (%s, %s, %s)
            ON CONFLICT (clerk_id) DO UPDATE
            SET email = EXCLUDED.email, name = EXCLUDED.name
        """, (uid, req.email, req.name))
        conn.commit()
        cur.close()
        return {"status": "synchronized", "uid": uid}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            release_db(conn)


# ── Dashboard Analytics ──────────────────────────────────
@app.get("/api/dashboard-analytics/{uid}")
async def get_dashboard_analytics(uid: str):
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            WITH
            recent AS (
                SELECT tool, input_summary, tokens_used,
                       (created_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata') AS created_at
                FROM sessions
                WHERE clerk_id = %s
                ORDER BY created_at DESC
                LIMIT 5
            ),
            weekly AS (
                SELECT
                    DATE(created_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata') AS session_date,
                    COUNT(*) AS total_count
                FROM sessions
                WHERE clerk_id = %s
                  AND (created_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata')
                      >= (NOW() AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata') - INTERVAL '7 days'
                GROUP BY DATE(created_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata')
            ),
            favorite AS (
                SELECT tool, COUNT(*) AS count
                FROM sessions
                WHERE clerk_id = %s
                GROUP BY tool
                ORDER BY count DESC
                LIMIT 1
            )
            SELECT
                (SELECT json_agg(recent) FROM recent) AS recent_sessions,
                (SELECT json_agg(weekly) FROM weekly) AS weekly_metrics,
                (SELECT row_to_json(favorite) FROM favorite) AS favorite_tool
        """, (uid, uid, uid))

        result = cur.fetchone()
        cur.close()

        recent_sessions = result["recent_sessions"] or []
        db_metrics = result["weekly_metrics"] or []
        favorite_res = result["favorite_tool"]

        ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
        today_ist = ist_now.date()
        days_array = [(today_ist - timedelta(days=i)) for i in range(6, -1, -1)]

        chart_data = []
        for day in days_array:
            day_str = str(day)
            match = next(
                (e for e in db_metrics if str(e["session_date"]) == day_str),
                None
            )
            chart_data.append({
                "day": day.strftime("%a"),
                "total": int(match["total_count"]) if match else 0
            })

        if favorite_res and "tool" in favorite_res:
            favorite_assistant = f"{str(favorite_res['tool']).title()} ({favorite_res['count']} runs)"
        else:
            favorite_assistant = "None (0 runs)"

        return {
            "telemetry_stream": recent_sessions,
            "time_series_7d": chart_data,
            "metrics": {
                "favorite_assistant": favorite_assistant,
                "workspace_momentum": "+14% growth vs last cycle",
                "streak_count": "5 Days Active",
            }
        }

    except Exception as e:
        print("Analytics Generation Engine Interrupted Exception:", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            release_db(conn)


# ── Debug ────────────────────────────────────────────────
@app.post("/api/debug-assistant")
async def debug(req: DebugRequest):
    uid = verify_firebase_token(req.id_token)

    system_message = {
        "role": "system",
        "content": """You are an elite debugging engine. Return ONLY valid JSON:
{
  "confidence": 94,
  "rootCause": "...",
  "technicalExplanation": ["Point 1", "Point 2"],
  "fixedCode": "",
  "prevention": ["Tip 1", "Tip 2"]
}
Rules: Return ONLY JSON. confidence = 0-100. fixedCode = compilable code only. No markdown fences."""
    }
    user_content = f"Language: {req.language}\nError:\n{req.error}\nCode:\n{req.code}"
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[system_message, {"role": "user", "content": user_content}]
    )
    content = response.choices[0].message.content.strip()
    if content.startswith("```"):
        content = re.sub(r"```\w*", "", content).replace("```", "").strip()

    # ✅ FIX: Log to database IMMEDIATELY before parsing JSON
    log_session(uid, "debug-assistant", req.error[:100], tokens=240)

    try:
        data = json.loads(content)
        return data
    except Exception:
        return {
            "confidence": 50,
            "rootCause": "Unable to analyze error context due to formatting mismatch.",
            "technicalExplanation": [],
            "fixedCode": "",
            "prevention": []
        }


# ── Code Explain ─────────────────────────────────────────
@app.post("/api/code-explain")
async def explain(req: CodeRequest):
    uid = verify_firebase_token(req.id_token)

    system_message = {
        "role": "system",
        "content": """You are an expert code explainer. Return ONLY valid JSON:
{
  "summary": "Short explanation",
  "breakdown": ["Step 1", "Step 2"],
  "complexity": {"time": "O(n)", "space": "O(1)"},
  "improvements": ["Tip 1", "Tip 2"]
}
Rules: Return ONLY JSON. No markdown. No code fences."""
    }
    user_content = f"Language: {req.language}\nCode:\n{req.code}"
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[system_message, {"role": "user", "content": user_content}]
    )
    content = response.choices[0].message.content.strip()
    if content.startswith("```"):
        content = re.sub(r"```\w*", "", content).replace("```", "").strip()

    # ✅ FIX: Log to database IMMEDIATELY
    log_session(uid, "code-explain", req.code[:100], tokens=180)

    try:
        data = json.loads(content)
        return data
    except Exception:
        return {
            "summary": "Unable to compile structural breakdown",
            "breakdown": [],
            "complexity": {"time": "-", "space": "-"},
            "improvements": []
        }


# ── Resume Review ─────────────────────────────────────────
@app.post("/api/review-resume")
async def review_resume(id_token: str = Form(""), file: UploadFile = File(...)):
    uid = verify_firebase_token(id_token)

    pdf_bytes = await file.read()
    reader = PdfReader(BytesIO(pdf_bytes))
    resume_text = ""
    for page in reader.pages:
        text = page.extract_text()
        if text:
            resume_text += text + "\n"

    system_message = {
        "role": "system",
        "content": """You are an expert ATS Resume Reviewer. Return ONLY valid JSON:
{
  "score": 85,
  "strengths": ["..."],
  "improvements": ["..."],
  "keywords": ["..."]
}
Rules: Return ONLY JSON. No markdown. Score 0-100."""
    }
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[system_message, {"role": "user", "content": resume_text}]
    )
    content = response.choices[0].message.content.strip()
    try:
        log_session(uid, "review-resume", "ATS Upload Optimization Analysis", tokens=310)
        return json.loads(content)
    except Exception:
        return {
            "score": 0,
            "strengths": [],
            "improvements": ["Processing failed cleanly. Retrying required."],
            "keywords": []
        }


# ── Repository Copilot ────────────────────────────────────
@app.post("/api/repository-copilot")
async def repository_copilot(req: RepoRequest):
    uid = verify_firebase_token(req.id_token)

    try:
        match = re.search(r"github\.com/([^/]+)/([^/]+)", req.repo_url)
        if not match:
            return {"error": "Invalid GitHub repository location format. Use https://github.com/owner/repo"}
        owner = match.group(1)
        repo = match.group(2).replace(".git", "")

        headers = {}
        github_token = os.getenv("GITHUB_TOKEN")
        if github_token:
            headers["Authorization"] = f"token {github_token}"

        repo_res = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}",
            headers=headers,
            timeout=10
        )
        if repo_res.status_code in (403, 404):
            raise Exception("GitHub API access denied. The repository is private or rate limited.")

        repo_data = repo_res.json()
        languages = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/languages",
            headers=headers,
            timeout=10
        ).json()

        readme_text = ""
        readme_res = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/readme",
            headers=headers,
            timeout=10
        )
        if readme_res.status_code == 200:
            readme_json = readme_res.json()
            if "content" in readme_json:
                readme_text = base64.b64decode(readme_json["content"]).decode("utf-8", errors="ignore")

        system_message = {
            "role": "system",
            "content": """You are an expert repository analyst. Given repository metadata (name, languages, README content, and the user's goal), return ONLY a valid JSON object with this exact structure:
{
  "overview": "A 3-5 sentence summary of the project's purpose and architecture",
  "tech_stack": ["List", "of", "technologies", "used"],
  "important_files": ["path/to/file1", "path/to/file2"],
  "quick_start": ["git clone ...", "npm install", "npm run dev"],
  "developer_insights": {
    "architecture": "...",
    "routing": "...",
    "state_management": "..."
  },
  "change_plan": {
    "files_to_modify": ["file1", "file2"],
    "steps": ["Step 1...", "Step 2..."]
  }
}
Focus the analysis on the user's stated goal if provided. Return ONLY the JSON object, no markdown, no explanation."""
        }

        user_content = f"Repo: {repo_data.get('name', '')}\nGoal: {req.goal}"

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[system_message, {"role": "user", "content": user_content}],
            temperature=0.1,
            response_format={"type": "json_object"}
        )

        raw_content = response.choices[0].message.content.strip()

        # ✅ FIX: Log to database IMMEDIATELY
        log_session(uid, "repository-copilot", req.repo_url, tokens=450)

        try:
            content_data = json.loads(raw_content)
            return content_data
        except json.JSONDecodeError:
            raise Exception("LLM failed to generate parseable JSON.")

    except HTTPException:
        raise
    except Exception as e:
        return {
            "overview": f"Analysis failed. Reason: {str(e)}",
            "tech_stack": ["Error"],
            "important_files": [],
            "quick_start": [],
            "developer_insights": {},
            "change_plan": {}
        }