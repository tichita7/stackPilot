"""
GitHub Source-Retrieval Service for StackPilot Repository Copilot.

Provides bounded, read-only repository inspection via GitHub REST APIs:
- Validates repository URLs with strict security controls.
- Fetches repository metadata, languages, README, and recursive Git tree.
- Deterministically selects up to 3 relevant manifest/source files.
- Strictly bounds API request counts (max 7), file sizes (<= 50 KB),
  and character budgets (<= 3,500 chars per file, <= 2,500 chars README).
- Excludes sensitive, binary, generated, dependency, and lock files.
- In-memory redaction of recognizable credential patterns.
- Returns a bounded, structured RepositoryContext suitable for LLM prompting.
"""

from __future__ import annotations

import base64
import os
import re
import urllib.parse
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

import requests


# ── Strict Budgets & Limits ──────────────────────────────────────────────────
MAX_GITHUB_REQUESTS = 7
MAX_FETCHED_FILES = 3
MAX_FILE_CHARS = 3500
MAX_README_CHARS = 2500
MAX_FILE_SIZE_BYTES = 50 * 1024  # 50 KB
MAX_TOTAL_CONTEXT_CHARS = 20000
REQUEST_TIMEOUT_SECONDS = 8
MAX_TREE_PREVIEW_PATHS = 30


# ── Exclusion Rules ──────────────────────────────────────────────────────────
# Directory segments that must be excluded from inspection
EXCLUDED_DIRECTORY_SEGMENTS: Set[str] = {
    # Dependencies & packages
    "node_modules", "vendor", "site-packages", "packages", "bower_components", "pods",
    # Virtual environments
    "venv", ".venv", "env", ".env", "virtualenv",
    # Build & distribution outputs
    "dist", "build", "out", "target", "bin", "obj", ".next", ".nuxt", ".turbo",
    ".cache", ".parcel-cache", "coverage",
    # Version control & IDE artifacts
    ".git", ".github", ".svn", ".hg", ".idea", ".vscode", ".vs",
    # Language / Compiler caches
    "__pycache__", ".pytest_cache", ".mypy_cache",
}

# Binary, media, archive, and compiled extensions
EXCLUDED_EXTENSIONS: Set[str] = {
    # Binaries & Executables
    ".exe", ".dll", ".so", ".dylib", ".bin", ".app", ".dmg", ".iso", ".wasm",
    # Media & Images
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp", ".bmp", ".tiff",
    ".mp3", ".mp4", ".wav", ".ogg", ".avi", ".mov", ".flv",
    # Documents & Archives
    ".pdf", ".zip", ".tar", ".gz", ".tgz", ".7z", ".rar", ".bz2", ".xz",
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    # Fonts
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    # Compiled bytecode & Objects
    ".pyc", ".pyo", ".pyd", ".class", ".jar", ".war", ".o", ".obj", ".a", ".lib",
    # Minified assets & maps
    ".min.js", ".min.css", ".map",
}

# Dependency lockfiles (redundant, oversized, and low semantic value for architectural prompts)
EXCLUDED_FILENAMES: Set[str] = {
    "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "cargo.lock",
    "poetry.lock", "gemfile.lock", "composer.lock", "go.sum",
}

# Sensitive / Credential file patterns and extensions
SENSITIVE_EXTENSIONS: Set[str] = {
    ".pem", ".key", ".pkcs12", ".pfx", ".crt", ".cer", ".der",
}

SENSITIVE_EXACT_NAMES: Set[str] = {
    ".env", ".npmrc", ".pypirc", ".dockercfg",
    "id_rsa", "id_dsa", "id_ed25519", "id_ecdsa",
    "authorized_keys", "known_hosts",
    "credentials.json", "google-services.json",
}

# Ordered priority for project manifests / configuration files
MANIFEST_PRIORITIES: List[str] = [
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "gemfile",
    "composer.json",
    "dockerfile",
    "tsconfig.json",
    "makefile",
]

# Ordered priority for core entrypoints
ENTRYPOINT_PATTERNS: List[str] = [
    "src/index.ts", "src/index.js", "src/main.ts", "src/main.jsx",
    "src/app.tsx", "src/app.jsx", "main.py", "app.py", "server.py",
    "index.js", "index.ts", "main.go", "src/lib.rs", "src/main.rs",
    "pages/_app.tsx", "app/layout.tsx", "app/page.tsx",
]

# Stopwords for goal keyword extraction
GOAL_STOPWORDS: Set[str] = {
    "the", "and", "for", "with", "from", "that", "this", "how", "what",
    "where", "can", "map", "find", "code", "repo", "repository", "file",
    "files", "project", "analyze", "explain", "understand", "show", "give",
    "list", "want", "need", "like", "into", "over", "about",
}


# ── Credential Redaction Patterns ────────────────────────────────────────────
REDACTION_PATTERNS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\b(sk-[a-zA-Z0-9_-]{20,})\b"), "[REDACTED_API_KEY]"),
    (re.compile(r"\b(gh[pousr]_[A-Za-z0-9_]{36,}|github_pat_[A-Za-z0-9_]{50,})\b"), "[REDACTED_TOKEN]"),
    (re.compile(r"\b(AKIA[0-9A-Z]{16})\b"), "[REDACTED_AWS_KEY]"),
    (re.compile(r"(Bearer\s+)[A-Za-z0-9._~+/-]{20,}", re.IGNORECASE), r"\1[REDACTED_TOKEN]"),
    (re.compile(r"-----BEGIN [A-Z ]+ PRIVATE KEY-----[\s\S]*?-----END [A-Z ]+ PRIVATE KEY-----"), "[REDACTED_PRIVATE_KEY]"),
]


# ── Data Models ──────────────────────────────────────────────────────────────
@dataclass
class RepositoryContext:
    owner: str
    repo: str
    default_branch: str = "main"
    is_empty: bool = False
    rate_limited: bool = False
    access_denied: bool = False
    tree_truncated: bool = False
    total_api_calls: int = 0
    languages: Dict[str, int] = field(default_factory=dict)
    readme_content: str = ""
    directory_tree: List[str] = field(default_factory=list)
    all_file_paths: Set[str] = field(default_factory=set)
    selected_files: Dict[str, str] = field(default_factory=dict)
    error_message: Optional[str] = None
    failure_reason: Optional[str] = None
    upstream_status: Optional[int] = None

    def to_prompt_context(self) -> str:
        """Serializes repository context into a bounded, prompt-safe text block."""
        parts: List[str] = [
            f"<repository_context>",
            f"Repository: {self.owner}/{self.repo}",
            f"Default Branch: {self.default_branch}",
        ]

        if self.is_empty:
            parts.append("Status: Empty repository (no commits or files found).")
            parts.append("</repository_context>")
            return "\n".join(parts)

        if self.languages:
            top_langs = sorted(self.languages.items(), key=lambda x: x[1], reverse=True)[:5]
            lang_str = ", ".join(f"{k} ({v} bytes)" for k, v in top_langs)
            parts.append(f"Languages: {lang_str}")

        if self.directory_tree:
            parts.append("\nTop-Level File Structure:")
            for p in self.directory_tree[:MAX_TREE_PREVIEW_PATHS]:
                parts.append(f"  - {p}")
            if self.tree_truncated:
                parts.append("  [Note: Repository file tree was truncated due to repository size]")

        if self.readme_content:
            parts.append(f"\n--- README.md (Extract) ---\n{self.readme_content}")

        if self.selected_files:
            parts.append("\n--- Selected Code & Configuration Files ---")
            for path, content in self.selected_files.items():
                parts.append(f"\nFile: {path}\n```\n{content}\n```")

        parts.append("</repository_context>")
        rendered = "\n".join(parts)

        # Enforce strict overall context ceiling
        if len(rendered) > MAX_TOTAL_CONTEXT_CHARS:
            rendered = rendered[:MAX_TOTAL_CONTEXT_CHARS] + "\n... [Context truncated to fit budget]\n</repository_context>"

        return rendered


# ── URL Validation ───────────────────────────────────────────────────────────
def parse_github_url(url: str) -> Optional[Tuple[str, str]]:
    """
    Strictly validates and parses a GitHub repository URL.

    Security checks:
    - Scheme must be http or https.
    - Hostname must be strictly github.com or www.github.com.
    - Rejects credentials (user:pass@...).
    - Rejects non-standard ports.
    - Rejects encoded path traversals (%2e%2e, null bytes).
    - Validates owner format: 1-39 chars, alphanumeric with single non-consecutive hyphens.
    - Validates repo format: 1-100 chars, alphanumeric/hyphens/underscores/dots, not '.' or '..'.
    - Strips subpaths (e.g. /tree/main/...) and trailing .git cleanly.

    Returns (owner, repo) tuple if valid, or None if invalid.
    """
    if not url or not isinstance(url, str):
        return None

    cleaned_url = url.strip()
    if not cleaned_url:
        return None

    try:
        parsed = urllib.parse.urlsplit(cleaned_url)
    except Exception:
        return None

    # Scheme check
    if parsed.scheme.lower() not in ("http", "https"):
        return None

    # Reject embedded userinfo/credentials
    if parsed.username or parsed.password or ("@" in (parsed.netloc or "")):
        return None

    # Hostname check
    hostname = (parsed.hostname or "").lower()
    if hostname not in ("github.com", "www.github.com"):
        return None

    # Reject non-standard ports
    if parsed.port is not None and parsed.port not in (80, 443):
        return None

    # Unquote and reject traversal/null characters
    raw_path = parsed.path
    if "\x00" in raw_path:
        return None

    unquoted_path = urllib.parse.unquote(raw_path)
    if "\x00" in unquoted_path:
        return None

    # Check for path traversal elements
    segments = [s.strip() for s in unquoted_path.strip("/").split("/") if s.strip()]
    if len(segments) < 2:
        return None

    owner_candidate = segments[0]
    repo_candidate = segments[1]

    # Traversal checks on segments
    if owner_candidate in (".", "..") or repo_candidate in (".", ".."):
        return None

    # Strip trailing .git extension only from the end of the repo segment
    repo_candidate = re.sub(r"\.git$", "", repo_candidate, flags=re.IGNORECASE)

    # Re-check traversal/empty on repo_candidate after stripping .git
    if not repo_candidate or repo_candidate in (".", ".."):
        return None

    # Validate owner using GitHub username rules: 1-39 chars, alphanumeric, internal single hyphens
    owner_pattern = re.compile(r"^[a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38}$")
    if not owner_pattern.match(owner_candidate):
        return None

    # Validate repo name rules: 1-100 chars, alphanumeric, hyphens, underscores, dots
    repo_pattern = re.compile(r"^[A-Za-z0-9_.-]{1,100}$")
    if not repo_pattern.match(repo_candidate):
        return None

    return owner_candidate, repo_candidate


# ── Credential Redaction & Sanitization ──────────────────────────────────────
def redact_credentials(content: str) -> str:
    """Replaces recognizable API keys and token patterns with redaction placeholders."""
    if not content:
        return ""
    sanitized = content
    for pattern, replacement in REDACTION_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized


def sanitize_and_truncate(content: str, max_chars: int) -> str:
    """Decodes, sanitizes credentials, and truncates content to the specified character limit."""
    if not content:
        return ""
    redacted = redact_credentials(content)
    if len(redacted) > max_chars:
        return redacted[:max_chars] + f"\n... [Truncated at {max_chars} characters]"
    return redacted


# ── File Exclusion & Deterministic Selection ─────────────────────────────────
def is_excluded_file(path: str, size: Optional[int] = None) -> bool:
    """
    Evaluates whether a candidate file path should be excluded based on directory,
    extension, lockfile status, sensitive credentials, or oversized payload.
    """
    if not path or not isinstance(path, str):
        return True

    normalized_path = path.replace("\\", "/").strip().lower()
    path_segments = [seg for seg in normalized_path.split("/") if seg]
    if not path_segments:
        return True

    filename = path_segments[-1]

    # Check directory blocklist
    for seg in path_segments[:-1]:
        if seg in EXCLUDED_DIRECTORY_SEGMENTS:
            return True

    # Check size if available
    if size is not None and size > MAX_FILE_SIZE_BYTES:
        return True

    # Check lockfiles
    if filename in EXCLUDED_FILENAMES:
        return True

    # Check sensitive files & extensions
    if filename in SENSITIVE_EXACT_NAMES:
        return True
    if filename.startswith(".env"):
        return True
    for ext in SENSITIVE_EXTENSIONS:
        if filename.endswith(ext):
            return True
    # Targeted JSON credential filenames
    if filename.endswith(".json") and any(token in filename for token in ("secret", "credential", "serviceaccount")):
        return True

    # Check binary / media / archive / minified extensions
    for ext in EXCLUDED_EXTENSIONS:
        if filename.endswith(ext):
            return True

    return False


def extract_goal_keywords(goal: str) -> Set[str]:
    """Extracts lowercase keywords from the user's goal string, filtering common stopwords."""
    if not goal or not isinstance(goal, str):
        return set()
    tokens = re.findall(r"[a-zA-Z0-9]{3,}", goal.lower())
    return {t for t in tokens if t not in GOAL_STOPWORDS}


def select_files_from_tree(
    tree_entries: List[dict],
    goal: str = "",
    max_files: int = MAX_FETCHED_FILES
) -> List[str]:
    """
    Deterministically selects up to max_files (default 3) relevant source or configuration
    files from a Git tree using a 3-tier priority heuristic:
    1. Key project manifests / configuration.
    2. Goal-relevant source files matching keywords.
    3. Core architectural entrypoints.
    """
    if not tree_entries or max_files <= 0:
        return []

    # Filter eligible blobs
    candidate_map: Dict[str, int] = {}
    for entry in tree_entries:
        if entry.get("type") != "blob":
            continue
        path = entry.get("path", "")
        size = entry.get("size")
        if is_excluded_file(path, size=size):
            continue
        candidate_map[path] = size if size is not None else 0

    if not candidate_map:
        return []

    selected: List[str] = []
    goal_keywords = extract_goal_keywords(goal)

    # ── Tier 1: Project Manifests (Pick at most 1) ──
    for manifest in MANIFEST_PRIORITIES:
        if len(selected) >= max_files:
            break
        # Look for root-level or shallow manifests
        matches = [p for p in candidate_map if p.lower() == manifest or p.lower().endswith(f"/{manifest}")]
        matches.sort(key=lambda p: (p.count("/"), len(p), p))
        for m in matches:
            if m not in selected:
                selected.append(m)
                break  # Take at most one manifest in Tier 1
        if selected:
            break

    # ── Tier 2: Goal-Relevant Files (Pick up to 1-2) ──
    if goal_keywords and len(selected) < max_files:
        scored_candidates: List[Tuple[int, str]] = []
        for path in candidate_map:
            if path in selected:
                continue
            lower_path = path.lower()
            base_name = lower_path.split("/")[-1].split(".")[0]
            base_parts = re.findall(r"[a-z0-9]+", base_name)
            path_parts = re.findall(r"[a-z0-9]+", lower_path)

            score = 0
            for kw in goal_keywords:
                # Exact base filename or part match
                if kw == base_name or kw in base_parts:
                    score += 15
                elif any(len(p) >= 3 and (p in kw or kw in p) for p in base_parts):
                    # Stem/prefix match like auth <-> authentication, route <-> router
                    score += 10
                elif kw in path_parts or any(len(p) >= 3 and (p in kw or kw in p) for p in path_parts):
                    score += 6
                elif kw in lower_path:
                    score += 3

            if score > 0:
                # Add shallow depth bonus
                depth = lower_path.count("/")
                score += max(0, 5 - depth)
                scored_candidates.append((score, path))

        # Sort by score desc, then depth asc, then path asc (deterministic)
        scored_candidates.sort(key=lambda item: (-item[0], item[1].count("/"), item[1]))
        for _, path in scored_candidates:
            if len(selected) >= max_files:
                break
            selected.append(path)

    # ── Tier 3: Core Entrypoints (Fill remaining slots) ──
    if len(selected) < max_files:
        for entrypoint in ENTRYPOINT_PATTERNS:
            if len(selected) >= max_files:
                break
            matches = [p for p in candidate_map if p.lower() == entrypoint or p.lower().endswith(f"/{entrypoint}")]
            matches.sort(key=lambda p: (p.count("/"), len(p), p))
            for m in matches:
                if m not in selected:
                    selected.append(m)
                    if len(selected) >= max_files:
                        break

    # ── Tier 4: Fallback to Shallow Source Files (if budget remains) ──
    if len(selected) < max_files:
        remaining = [p for p in candidate_map if p not in selected]
        remaining.sort(key=lambda p: (p.count("/"), len(p), p))
        for p in remaining:
            if len(selected) >= max_files:
                break
            selected.append(p)

    return selected[:max_files]


# ── Safe GitHub API Client & Orchestrator ─────────────────────────────────────
class GitHubApiClient:
    """
    Enforces request budgeting, timeout safety, SSRF protection,
    and graceful error handling across GitHub API calls.
    """

    def __init__(self, github_token: Optional[str] = None):
        self.github_token = github_token
        self.request_count = 0
        self.last_failure_type: Optional[str] = None

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "StackPilot-RepositoryCopilot",
        }
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
        return headers

    def safe_get(self, url: str) -> Optional[requests.Response]:
        """Executes a bounded GET request respecting the request budget and security boundaries."""
        self.last_failure_type = None

        if self.request_count >= MAX_GITHUB_REQUESTS:
            self.last_failure_type = "budget_exhausted"
            return None

        # Verify target URL is strictly on api.github.com
        try:
            parsed = urllib.parse.urlsplit(url)
            if (parsed.hostname or "").lower() != "api.github.com":
                self.last_failure_type = "invalid_url"
                return None
            if parsed.scheme.lower() != "https":
                self.last_failure_type = "invalid_url"
                return None
        except Exception:
            self.last_failure_type = "invalid_url"
            return None

        self.request_count += 1
        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=REQUEST_TIMEOUT_SECONDS,
                allow_redirects=False  # Prevent redirecting away from api.github.com
            )
            return response
        except requests.Timeout:
            self.last_failure_type = "timeout"
            return None
        except requests.RequestException:
            self.last_failure_type = "network_error"
            return None
        except Exception:
            self.last_failure_type = "network_error"
            return None


def fetch_repository_context(
    owner: str,
    repo: str,
    goal: str = "",
    github_token: Optional[str] = None
) -> RepositoryContext:
    """
    Orchestrates the retrieval of repository metadata, languages, README,
    file tree, and up to 3 selected source files within the 7-request limit.
    """
    context = RepositoryContext(owner=owner, repo=repo)
    client = GitHubApiClient(github_token=github_token)

    # 1. Fetch Repository Metadata (Call 1)
    repo_url = f"https://api.github.com/repos/{owner}/{repo}"
    repo_res = client.safe_get(repo_url)
    context.total_api_calls = client.request_count

    if repo_res is None:
        if client.last_failure_type == "timeout":
            context.failure_reason = "timeout"
            context.error_message = "GitHub API request timed out."
        elif client.last_failure_type == "budget_exhausted":
            context.failure_reason = "upstream_error"
            context.error_message = "GitHub API request budget exceeded."
        else:
            context.failure_reason = "network_error"
            context.error_message = "GitHub API request timed out or network connection failed."
        return context

    context.upstream_status = repo_res.status_code

    if repo_res.status_code == 429:
        context.rate_limited = True
        context.failure_reason = "rate_limited"
        context.error_message = "GitHub API rate limit exceeded. Please configure GITHUB_TOKEN or retry later."
        return context

    if repo_res.status_code in (401, 403):
        remaining = ""
        if hasattr(repo_res, "headers") and isinstance(repo_res.headers, dict):
            remaining = str(repo_res.headers.get("X-RateLimit-Remaining", ""))
        body_text = repo_res.text if hasattr(repo_res, "text") and isinstance(repo_res.text, str) else ""
        if remaining == "0" or "rate limit" in body_text.lower():
            context.rate_limited = True
            context.failure_reason = "rate_limited"
            context.error_message = "GitHub API rate limit exceeded. Please configure GITHUB_TOKEN or retry later."
        elif repo_res.status_code == 401:
            context.failure_reason = "upstream_error"
            context.error_message = "GitHub API authentication failed."
        else:
            context.access_denied = True
            context.failure_reason = "access_denied"
            context.error_message = "GitHub API access denied. The repository is private or access is restricted."
        return context

    if repo_res.status_code == 404:
        context.access_denied = True
        context.failure_reason = "not_found"
        context.error_message = "GitHub repository not found or is private."
        return context

    if repo_res.status_code >= 500:
        context.failure_reason = "upstream_error"
        context.error_message = f"GitHub API responded with unexpected status code: {repo_res.status_code}."
        return context

    if repo_res.status_code != 200:
        context.failure_reason = "upstream_error"
        context.error_message = f"GitHub API responded with unexpected status code: {repo_res.status_code}."
        return context

    try:
        repo_data = repo_res.json()
    except Exception:
        context.failure_reason = "malformed_response"
        context.error_message = "Malformed JSON received from GitHub API."
        return context

    if not isinstance(repo_data, dict):
        context.failure_reason = "malformed_response"
        context.error_message = "Malformed repository metadata received from GitHub API."
        return context

    # Check essential metadata (name or full_name or id or default_branch)
    if not any(k in repo_data for k in ("name", "full_name", "id", "default_branch")):
        context.failure_reason = "malformed_response"
        context.error_message = "Missing essential repository metadata."
        return context

    raw_branch = repo_data.get("default_branch")
    default_branch = raw_branch if isinstance(raw_branch, str) and raw_branch.strip() else "main"
    context.default_branch = default_branch

    raw_size = repo_data.get("size")
    # size must be an integer, not a boolean, and non-negative
    if isinstance(raw_size, bool) or not isinstance(raw_size, int) or raw_size < 0:
        context.failure_reason = "malformed_response"
        context.error_message = "Invalid repository size in metadata."
        return context

    repo_size = raw_size

    # Check for empty repository
    if repo_size == 0:
        context.is_empty = True
        return context

    # 2. Fetch Languages (Call 2)
    langs_url = f"https://api.github.com/repos/{owner}/{repo}/languages"
    langs_res = client.safe_get(langs_url)
    if langs_res and langs_res.status_code == 200:
        try:
            parsed_langs = langs_res.json()
            if isinstance(parsed_langs, dict):
                context.languages = parsed_langs
        except Exception:
            context.languages = {}

    # 3. Fetch README (Call 3)
    readme_url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    readme_res = client.safe_get(readme_url)
    if readme_res and readme_res.status_code == 200:
        try:
            readme_data = readme_res.json()
            if isinstance(readme_data, dict) and "content" in readme_data and isinstance(readme_data["content"], str):
                decoded_readme = base64.b64decode(readme_data["content"]).decode("utf-8", errors="ignore")
                context.readme_content = sanitize_and_truncate(decoded_readme, MAX_README_CHARS)
        except Exception:
            context.readme_content = ""

    # 4. Fetch Git Tree (Call 4)
    quoted_branch = urllib.parse.quote(default_branch, safe="")
    tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{quoted_branch}?recursive=1"
    tree_res = client.safe_get(tree_url)

    if tree_res and tree_res.status_code == 409:
        # 409 Conflict: Git Repository is empty
        context.is_empty = True
        context.total_api_calls = client.request_count
        return context

    tree_entries: List[dict] = []
    if tree_res and tree_res.status_code == 200:
        try:
            tree_data = tree_res.json()
            if isinstance(tree_data, dict):
                context.tree_truncated = bool(tree_data.get("truncated", False))
                raw_tree = tree_data.get("tree", [])
                if isinstance(raw_tree, list):
                    tree_entries = [e for e in raw_tree if isinstance(e, dict)]
                    blob_paths = [e["path"] for e in tree_entries if e.get("type") == "blob" and isinstance(e.get("path"), str)]
                    context.directory_tree = blob_paths[:MAX_TREE_PREVIEW_PATHS]
                    context.all_file_paths = set(blob_paths)
        except Exception:
            tree_entries = []

    # Pre-emptive rate limit check: Stop if remaining calls are exhausted
    if tree_res and hasattr(tree_res, "headers") and isinstance(tree_res.headers, dict):
        rem_header = tree_res.headers.get("X-RateLimit-Remaining")
        if isinstance(rem_header, str) and rem_header.isdigit() and int(rem_header) < 2:
            context.total_api_calls = client.request_count
            return context

    # 5. Deterministic File Selection & Bounded Content Retrieval (Calls 5 to 7, max 3 files)
    selected_paths = select_files_from_tree(tree_entries, goal=goal, max_files=MAX_FETCHED_FILES)

    for path in selected_paths:
        if client.request_count >= MAX_GITHUB_REQUESTS:
            break
        # Safe URL construction from validated components
        quoted_path = urllib.parse.quote(path)
        content_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{quoted_path}?ref={quoted_branch}"
        file_res = client.safe_get(content_url)
        if file_res and file_res.status_code == 200:
            try:
                file_data = file_res.json()
                if isinstance(file_data, dict) and "content" in file_data and isinstance(file_data["content"], str) and file_data.get("encoding") == "base64":
                    decoded_file = base64.b64decode(file_data["content"]).decode("utf-8", errors="ignore")
                    context.selected_files[path] = sanitize_and_truncate(decoded_file, MAX_FILE_CHARS)
            except Exception:
                continue

    context.total_api_calls = client.request_count
    return context
