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
import os
import json
import requests
import base64
import re
import psycopg2

load_dotenv()

app = FastAPI(title="StackPilot Enterprise API", version="1.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# ── Connection Pool (replaces open/close every request) ──
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

        # Index for fast clerk_id lookups
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_clerk_id ON sessions(clerk_id);
            CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at);
        """)
        conn.commit()

        # Safely patch existing databases with new columns
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
    clerk_id: str = ""


class CodeRequest(BaseModel):
    code: str
    language: str = ""
    clerk_id: str = ""


class RepoRequest(BaseModel):
    repo_url: str
    goal: str = ""
    clerk_id: str = ""


class UserSyncRequest(BaseModel):
    clerk_id: str
    email: str = ""
    name: str = ""


# ── Session Logger ───────────────────────────────────────
def log_session(clerk_id: str, tool: str, summary: str, tokens: int = 150):
    if not clerk_id:
        return
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO sessions (clerk_id, tool, input_summary, tokens_used) VALUES (%s, %s, %s, %s)",
            (clerk_id, tool, summary[:200], tokens)
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
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (clerk_id, email, name)
            VALUES (%s, %s, %s)
            ON CONFLICT (clerk_id) DO UPDATE
            SET email = EXCLUDED.email, name = EXCLUDED.name
        """, (req.clerk_id, req.email, req.name))
        conn.commit()
        cur.close()
        return {"status": "synchronized"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            release_db(conn)


# ── Dashboard Analytics ──────────────────────────────────
@app.get("/api/dashboard-analytics/{clerk_id}")
async def get_dashboard_analytics(clerk_id: str):
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()

        # Single query fetches everything at once — no sequential round trips
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
        """, (clerk_id, clerk_id, clerk_id))

        result = cur.fetchone()
        cur.close()

        recent_sessions = result["recent_sessions"] or []
        db_metrics = result["weekly_metrics"] or []
        favorite_res = result["favorite_tool"]

        # Build 7-day chart array
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
    try:
        data = json.loads(content)
        log_session(req.clerk_id, "debug-assistant", req.error[:100], tokens=240)
        return data
    except Exception:
        return {
            "confidence": 50,
            "rootCause": "Unable to analyze error context",
            "technicalExplanation": [],
            "fixedCode": "",
            "prevention": []
        }


# ── Code Explain ─────────────────────────────────────────
@app.post("/api/explain")
async def explain(req: CodeRequest):
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
    try:
        data = json.loads(content)
        log_session(req.clerk_id, "code-explain", req.code[:100], tokens=180)
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
async def review_resume(clerk_id: str = Form(""), file: UploadFile = File(...)):
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
        log_session(clerk_id, "review-resume", "ATS Upload Optimization Analysis", tokens=310)
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
    try:
        match = re.search(r"github\.com/([^/]+)/([^/]+)", req.repo_url)
        if not match:
            return {"error": "Invalid GitHub repository location format. Use https://github.com/owner/repo"}
        owner = match.group(1)
        repo = match.group(2).replace(".git", "")

        repo_res = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}",
            timeout=10
        )
        if repo_res.status_code in (403, 404):
            raise Exception("GitHub API access denied. The repository is private or rate limited.")

        repo_data = repo_res.json()
        languages = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/languages",
            timeout=10
        ).json()

        readme_text = ""
        readme_res = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/readme",
            timeout=10
        )
        if readme_res.status_code == 200:
            readme_json = readme_res.json()
            if "content" in readme_json:
                readme_text = base64.b64decode(readme_json["content"]).decode("utf-8", errors="ignore")

        system_message = {
            "role": "system",
            "content": """Analyze the repository data and return a JSON object matching this exact structure:
{
  "overview": "Clear high-level overview string",
  "tech_stack": ["Tech1", "Tech2"],
  "important_files": ["file1.js", "folder/"],
  "quick_start": ["command 1", "command 2"],
  "developer_insights": {
    "architecture": "Explanation",
    "routing": "Explanation",
    "authentication": "Explanation"
  },
  "change_plan": {
    "files_to_modify": ["file1.js"],
    "commands": ["npm test"],
    "steps": ["Step 1", "Step 2"]
  }
}"""
        }

        user_content = (
            f"Repo: {repo_data.get('name', '')}\n"
            f"Description: {repo_data.get('description', '')}\n"
            f"Languages: {languages}\n"
            f"README:\n{readme_text[:12000]}\n"
            f"Goal: {req.goal}"
        )

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[system_message, {"role": "user", "content": user_content}],
            temperature=0.1,
            response_format={"type": "json_object"}
        )

        raw_content = response.choices[0].message.content.strip()

        try:
            content_data = json.loads(raw_content)
        except json.JSONDecodeError as json_err:
            print(f"JSON DECODE ERROR: {json_err}\nRaw Output:\n{raw_content}")
            raise Exception("LLM failed to generate parseable JSON despite forced mode.")

        log_session(req.clerk_id, "repository-copilot", req.repo_url, tokens=450)
        return content_data

    except Exception as e:
        print(f"REPO COPILOT CRASH CAUSE: {str(e)}")
        return {
            "overview": f"Analysis failed. Reason: {str(e)}",
            "tech_stack": ["Error"],
            "important_files": [],
            "quick_start": ["Check terminal console"],
            "developer_insights": {
                "architecture": "Internal failure.",
                "routing": "N/A",
                "authentication": "N/A"
            },
            "change_plan": {
                "files_to_modify": [],
                "commands": [],
                "steps": []
            }
        }