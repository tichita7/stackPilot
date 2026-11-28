"""
Comprehensive Mocked Test Suite for server/github_service.py

Tests:
1. Strict GitHub URL validation and malicious input rejection.
2. File filtering, safety exclusions, and deterministic prioritization.
3. Goal-keyword relevance matching and scoring.
4. Hard ceilings: API request budgets (max 7) and file counts (max 3).
5. Truncation of README, source files, and overall prompt context.
6. In-memory credential and secret redaction.
7. Empty repository and missing README handling.
8. Rate limits, timeouts, access denial, and partial file failures.
9. Truncated Git tree coverage handling.
10. Strict offline verification (no external network calls).
"""

import base64
import os
import sys
from unittest.mock import MagicMock, patch
import pytest
import requests

# Ensure server module can be imported
SERVER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

from github_service import (
    MAX_FETCHED_FILES,
    MAX_FILE_CHARS,
    MAX_GITHUB_REQUESTS,
    MAX_README_CHARS,
    MAX_TOTAL_CONTEXT_CHARS,
    RepositoryContext,
    extract_goal_keywords,
    fetch_repository_context,
    is_excluded_file,
    parse_github_url,
    redact_credentials,
    sanitize_and_truncate,
    select_files_from_tree,
)


# ── 1. URL Validation Tests ──────────────────────────────────────────────────
class TestGitHubUrlValidation:
    """Tests strict URL parsing, normalization, and malicious rejection."""

    @pytest.mark.parametrize("valid_url,expected_owner,expected_repo", [
        ("https://github.com/facebook/react", "facebook", "react"),
        ("https://github.com/tichita7/stackPilot.git", "tichita7", "stackPilot"),
        ("http://github.com/torvalds/linux/", "torvalds", "linux"),
        ("https://www.github.com/pallets/flask", "pallets", "flask"),
        ("https://github.com/owner/repo/tree/main/src", "owner", "repo"),
        ("https://github.com/owner/repo/blob/master/README.md", "owner", "repo"),
        ("https://github.com/owner/repo?tab=readme-ov-file#installation", "owner", "repo"),
        ("https://github.com/owner-with-hyphen/repo_with.dots-and_underscores", "owner-with-hyphen", "repo_with.dots-and_underscores"),
    ])
    def test_valid_github_urls(self, valid_url, expected_owner, expected_repo):
        result = parse_github_url(valid_url)
        assert result is not None
        owner, repo = result
        assert owner == expected_owner
        assert repo == expected_repo

    @pytest.mark.parametrize("malicious_or_invalid_url", [
        # Credentials / Userinfo
        "https://user:pass@github.com/owner/repo",
        "https://token@github.com/owner/repo",
        # Non-standard ports
        "https://github.com:8443/owner/repo",
        "http://github.com:8080/owner/repo",
        # Non-GitHub domains
        "https://gitlab.com/owner/repo",
        "https://bitbucket.org/owner/repo",
        "https://attacker.com/github.com/owner/repo",
        "https://notgithub.com/owner/repo",
        # Path traversal and null bytes
        "https://github.com/../evil",
        "https://github.com/owner/../evil",
        "https://github.com/%2e%2e/%2e%2e",
        "https://github.com/owner/repo\x00evil",
        # Trailing .git normalization edge cases
        "https://github.com/owner/..git",
        "https://github.com/owner/.git",
        "https://github.com/..git/repo",
        "https://github.com/.git/repo",
        # Missing components
        "https://github.com/",
        "https://github.com/onlyowner",
        "https://github.com",
        "",
        None,
        # Invalid characters in owner or repo
        "https://github.com/owner$/repo",
        "https://github.com/-invalidowner/repo",
        "https://github.com/owner/repo;rm -rf",
        "ftp://github.com/owner/repo",
    ])
    def test_invalid_and_malicious_urls_rejected(self, malicious_or_invalid_url):
        assert parse_github_url(malicious_or_invalid_url) is None


# ── 2. File Exclusion Tests ──────────────────────────────────────────────────
class TestFileExclusion:
    """Verifies that sensitive, binary, dependency, and lock files are blocked without over-exclusion."""

    @pytest.mark.parametrize("blocked_path", [
        # Dependencies / vendor
        "node_modules/express/index.js",
        "vendor/autoload.php",
        "site-packages/requests/api.py",
        "packages/core/dist/index.js",
        ".venv/lib/python3.12/site.py",
        "venv/bin/activate",
        # Build outputs
        "dist/bundle.js",
        "build/static/js/main.js",
        "target/debug/app",
        ".next/server/pages/index.js",
        "coverage/lcov.info",
        # Version control & IDE
        ".git/config",
        ".github/workflows/ci.yml",
        ".vscode/settings.json",
        ".idea/workspace.xml",
        "__pycache__/main.cpython-312.pyc",
        # Sensitive credentials & keys
        ".env",
        ".env.local",
        ".env.production",
        "credentials.json",
        "serviceAccountKey.json",
        "client_secret.json",
        "client_secret_oauth.json",
        "credentials.dev.json",
        "config/serviceaccount.json",
        "id_rsa",
        "server.key",
        "cert.pem",
        # Binary & media
        "assets/logo.png",
        "image.jpg",
        "favicon.ico",
        "docs/whitepaper.pdf",
        "archive.zip",
        "driver.exe",
        "library.so",
        # Lockfiles
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "Cargo.lock",
        "poetry.lock",
        # Minified & maps
        "bundle.min.js",
        "styles.min.css",
        "main.js.map",
    ])
    def test_blocked_files(self, blocked_path):
        assert is_excluded_file(blocked_path) is True

    def test_oversized_file_is_excluded(self):
        assert is_excluded_file("src/data.json", size=55 * 1024) is True
        assert is_excluded_file("src/data.json", size=45 * 1024) is False

    @pytest.mark.parametrize("legitimate_source_file", [
        "src/auth/token_service.py",
        "keyboard.py",
        "lib/security/crypto_utils.go",
        "components/TokenModal.tsx",
        "src/jwt_validator.ts",
        "package.json",
        "pyproject.toml",
        "requirements.txt",
        "main.py",
        "src/App.jsx",
        "Dockerfile",
    ])
    def test_legitimate_source_files_not_excluded(self, legitimate_source_file):
        """Ensures ordinary legitimate code files (even containing 'token' or 'crypto') are not overbroadly blocked."""
        assert is_excluded_file(legitimate_source_file, size=1000) is False


# ── 3. File Selection & Prioritization Tests ─────────────────────────────────
class TestFileSelection:
    """Tests deterministic selection of manifests, entrypoints, and goal-relevant files."""

    def test_manifest_priority_selection(self):
        tree = [
            {"path": "package.json", "type": "blob", "size": 1200},
            {"path": "src/components/Header.jsx", "type": "blob", "size": 800},
            {"path": "src/utils/math.js", "type": "blob", "size": 500},
            {"path": "src/index.js", "type": "blob", "size": 1500},
        ]
        selected = select_files_from_tree(tree, goal="", max_files=3)
        assert len(selected) <= 3
        # Manifest package.json and entrypoint src/index.js must be selected
        assert "package.json" in selected
        assert "src/index.js" in selected

    def test_goal_relevance_matching(self):
        tree = [
            {"path": "package.json", "type": "blob", "size": 1200},
            {"path": "src/routes/auth_routes.py", "type": "blob", "size": 2000},
            {"path": "src/routes/users.py", "type": "blob", "size": 1800},
            {"path": "src/database/schema.sql", "type": "blob", "size": 1500},
            {"path": "src/utils/calculator.py", "type": "blob", "size": 600},
        ]
        goal = "Map the authentication router and login endpoints"
        selected = select_files_from_tree(tree, goal=goal, max_files=3)
        assert "src/routes/auth_routes.py" in selected

    def test_max_files_ceiling_strictly_enforced(self):
        tree = [
            {"path": f"src/file_{i}.py", "type": "blob", "size": 500}
            for i in range(20)
        ]
        selected = select_files_from_tree(tree, goal="", max_files=MAX_FETCHED_FILES)
        assert len(selected) == MAX_FETCHED_FILES

    def test_deterministic_output(self):
        tree = [
            {"path": "b.py", "type": "blob", "size": 500},
            {"path": "a.py", "type": "blob", "size": 500},
            {"path": "c.py", "type": "blob", "size": 500},
        ]
        sel1 = select_files_from_tree(tree, goal="", max_files=2)
        sel2 = select_files_from_tree(tree, goal="", max_files=2)
        assert sel1 == sel2


# ── 4. Credential Redaction & Truncation Tests ───────────────────────────────
class TestRedactionAndTruncation:
    """Verifies that API keys and secrets are redacted in-memory and content is safely truncated."""

    def test_credential_redaction(self):
        content = (
            "OPENAI_API_KEY = 'sk-abcdef1234567890abcdef12345678'\n"
            "GH_TOKEN = 'ghp_123456789012345678901234567890123456'\n"
            "AWS_KEY = 'AKIA1234567890ABCDEF'\n"
            "auth = 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.sig'\n"
            "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA...\n-----END RSA PRIVATE KEY-----"
        )
        redacted = redact_credentials(content)
        assert "sk-abcdef" not in redacted
        assert "[REDACTED_API_KEY]" in redacted
        assert "ghp_123456" not in redacted
        assert "[REDACTED_TOKEN]" in redacted
        assert "AKIA1234" not in redacted
        assert "[REDACTED_AWS_KEY]" in redacted
        assert "[REDACTED_PRIVATE_KEY]" in redacted

    def test_content_truncation(self):
        long_content = "x" * (MAX_FILE_CHARS + 500)
        truncated = sanitize_and_truncate(long_content, MAX_FILE_CHARS)
        assert len(truncated) <= MAX_FILE_CHARS + 100
        assert "Truncated" in truncated

    def test_prompt_context_overall_ceiling(self):
        ctx = RepositoryContext(owner="test", repo="test")
        ctx.selected_files = {
            f"file_{i}.txt": "a" * 8000 for i in range(5)
        }
        prompt_str = ctx.to_prompt_context()
        assert len(prompt_str) <= MAX_TOTAL_CONTEXT_CHARS + 200
        assert "<repository_context>" in prompt_str
        assert "</repository_context>" in prompt_str


# ── 5. End-to-End Orchestrator (Mocked GitHub) Tests ─────────────────────────
class TestFetchRepositoryContext:
    """End-to-end tests for fetch_repository_context with zero external network access."""

    @patch("github_service.requests.get")
    def test_successful_complete_fetch(self, mock_get):
        # 1. Repo metadata
        mock_repo = MagicMock(status_code=200)
        mock_repo.json.return_value = {"name": "react", "default_branch": "main", "size": 1000}
        # 2. Languages
        mock_langs = MagicMock(status_code=200)
        mock_langs.json.return_value = {"JavaScript": 50000, "TypeScript": 30000}
        # 3. README
        mock_readme = MagicMock(status_code=200)
        mock_readme.json.return_value = {
            "content": base64.b64encode(b"# React\nA declarative UI library.").decode()
        }
        # 4. Git Tree
        mock_tree = MagicMock(status_code=200)
        mock_tree.json.return_value = {
            "truncated": False,
            "tree": [
                {"path": "package.json", "type": "blob", "size": 1500},
                {"path": "src/index.js", "type": "blob", "size": 2000},
                {"path": "src/App.jsx", "type": "blob", "size": 1800},
            ]
        }
        # 5-7. File contents
        mock_file1 = MagicMock(status_code=200)
        mock_file1.json.return_value = {
            "encoding": "base64",
            "content": base64.b64encode(b'{"name": "react", "scripts": {"dev": "vite"}}').decode()
        }
        mock_file2 = MagicMock(status_code=200)
        mock_file2.json.return_value = {
            "encoding": "base64",
            "content": base64.b64encode(b'console.log("entry");').decode()
        }
        mock_file3 = MagicMock(status_code=200)
        mock_file3.json.return_value = {
            "encoding": "base64",
            "content": base64.b64encode(b'export default function App() {}').decode()
        }

        mock_get.side_effect = [mock_repo, mock_langs, mock_readme, mock_tree, mock_file1, mock_file2, mock_file3]

        ctx = fetch_repository_context("facebook", "react", goal="find entrypoint")

        assert ctx.owner == "facebook"
        assert ctx.repo == "react"
        assert ctx.default_branch == "main"
        assert ctx.is_empty is False
        assert ctx.rate_limited is False
        assert ctx.access_denied is False
        assert "JavaScript" in ctx.languages
        assert "React" in ctx.readme_content
        assert len(ctx.selected_files) >= 1
        assert len(ctx.all_file_paths) == 3
        assert "src/App.jsx" in ctx.all_file_paths
        assert ctx.total_api_calls <= MAX_GITHUB_REQUESTS

    @patch("github_service.requests.get")
    def test_strict_api_request_budget_enforcement(self, mock_get):
        """Verifies that under no circumstances can API requests exceed 7 calls."""
        mock_repo = MagicMock(status_code=200)
        mock_repo.json.return_value = {"default_branch": "main", "size": 1000}
        mock_langs = MagicMock(status_code=200)
        mock_langs.json.return_value = {}
        mock_readme = MagicMock(status_code=200)
        mock_readme.json.return_value = {"content": base64.b64encode(b"README").decode()}
        # Tree with 20 files
        mock_tree = MagicMock(status_code=200)
        mock_tree.json.return_value = {
            "truncated": False,
            "tree": [{"path": f"src/f{i}.py", "type": "blob", "size": 100} for i in range(20)]
        }
        # File contents
        file_mock = MagicMock(status_code=200)
        file_mock.json.return_value = {"encoding": "base64", "content": base64.b64encode(b"code").decode()}

        # Provide endless responses
        mock_get.side_effect = [mock_repo, mock_langs, mock_readme, mock_tree] + [file_mock] * 20

        ctx = fetch_repository_context("owner", "repo")
        assert ctx.total_api_calls <= MAX_GITHUB_REQUESTS
        assert mock_get.call_count <= MAX_GITHUB_REQUESTS

    @patch("github_service.requests.get")
    def test_empty_repository_handling(self, mock_get):
        """Verifies that an empty repository (size 0 or 409 Conflict) is handled cleanly."""
        # Case A: Size 0 in metadata
        mock_repo = MagicMock(status_code=200)
        mock_repo.json.return_value = {"default_branch": "main", "size": 0}
        mock_get.return_value = mock_repo

        ctx = fetch_repository_context("empty", "repo")
        assert ctx.is_empty is True
        assert ctx.total_api_calls == 1

        # Case B: 409 Conflict on tree API
        mock_repo2 = MagicMock(status_code=200)
        mock_repo2.json.return_value = {"default_branch": "main", "size": 10}
        mock_langs = MagicMock(status_code=200)
        mock_langs.json.return_value = {}
        mock_readme = MagicMock(status_code=404)
        mock_tree_409 = MagicMock(status_code=409)

        mock_get.side_effect = [mock_repo2, mock_langs, mock_readme, mock_tree_409]
        ctx2 = fetch_repository_context("empty", "repo2")
        assert ctx2.is_empty is True

    @patch("github_service.requests.get")
    def test_missing_readme_does_not_abort_flow(self, mock_get):
        """Missing README (404) degrades gracefully without failing the analysis."""
        mock_repo = MagicMock(status_code=200)
        mock_repo.json.return_value = {"default_branch": "main", "size": 100}
        mock_langs = MagicMock(status_code=200)
        mock_langs.json.return_value = {}
        mock_readme = MagicMock(status_code=404)
        mock_tree = MagicMock(status_code=200)
        mock_tree.json.return_value = {"tree": [{"path": "main.py", "type": "blob", "size": 50}]}
        mock_file = MagicMock(status_code=200)
        mock_file.json.return_value = {"encoding": "base64", "content": base64.b64encode(b"print(1)").decode()}

        mock_get.side_effect = [mock_repo, mock_langs, mock_readme, mock_tree, mock_file]
        ctx = fetch_repository_context("owner", "repo")
        assert ctx.readme_content == ""
        assert "main.py" in ctx.selected_files
        assert ctx.access_denied is False

    @patch("github_service.requests.get")
    def test_rate_limit_exceeded_detection(self, mock_get):
        """HTTP 403 with X-RateLimit-Remaining: 0 correctly triggers rate_limited flag."""
        mock_res = MagicMock(status_code=403, text="API rate limit exceeded")
        mock_res.headers = {"X-RateLimit-Remaining": "0"}
        mock_get.return_value = mock_res

        ctx = fetch_repository_context("owner", "repo")
        assert ctx.rate_limited is True
        assert "rate limit exceeded" in ctx.error_message.lower()

    @patch("github_service.requests.get")
    def test_access_denied_detection(self, mock_get):
        """HTTP 403 or 404 for private repository triggers access_denied flag."""
        mock_res = MagicMock(status_code=404)
        mock_get.return_value = mock_res

        ctx = fetch_repository_context("private", "repo")
        assert ctx.access_denied is True
        assert "not found or is private" in ctx.error_message.lower()

    @patch("github_service.requests.get")
    def test_network_timeout_resilience(self, mock_get):
        """Network timeout or connection error is caught without unhandled exceptions."""
        mock_get.side_effect = requests.Timeout("Connection timed out")
        ctx = fetch_repository_context("timeout", "repo")
        assert "timed out" in ctx.error_message.lower()
        assert ctx.total_api_calls == 1

    @patch("github_service.requests.get")
    def test_truncated_tree_handling(self, mock_get):
        """Truncated Git tree is recorded and reflected in prompt context."""
        mock_repo = MagicMock(status_code=200)
        mock_repo.json.return_value = {"default_branch": "main", "size": 1000}
        mock_langs = MagicMock(status_code=200)
        mock_langs.json.return_value = {}
        mock_readme = MagicMock(status_code=200)
        mock_readme.json.return_value = {"content": base64.b64encode(b"README").decode()}
        mock_tree = MagicMock(status_code=200)
        mock_tree.json.return_value = {
            "truncated": True,
            "tree": [{"path": "main.py", "type": "blob", "size": 100}]
        }
        mock_file = MagicMock(status_code=200)
        mock_file.json.return_value = {"encoding": "base64", "content": base64.b64encode(b"main").decode()}

        mock_get.side_effect = [mock_repo, mock_langs, mock_readme, mock_tree, mock_file]
        ctx = fetch_repository_context("large", "repo")
        assert ctx.tree_truncated is True
        prompt = ctx.to_prompt_context()
        assert "truncated due to repository size" in prompt

    @patch("github_service.requests.get")
    def test_default_branch_with_slashes_and_special_characters(self, mock_get):
        """Default branch with slashes (e.g. release/1.0) is safely percent-encoded in URLs."""
        mock_repo = MagicMock(status_code=200)
        mock_repo.json.return_value = {"default_branch": "release/1.0", "size": 500}
        mock_langs = MagicMock(status_code=200)
        mock_langs.json.return_value = {}
        mock_readme = MagicMock(status_code=404)
        mock_tree = MagicMock(status_code=200)
        mock_tree.json.return_value = {
            "truncated": False,
            "tree": [{"path": "main.py", "type": "blob", "size": 100}]
        }
        mock_file = MagicMock(status_code=200)
        mock_file.json.return_value = {"encoding": "base64", "content": base64.b64encode(b"main").decode()}

        mock_get.side_effect = [mock_repo, mock_langs, mock_readme, mock_tree, mock_file]
        ctx = fetch_repository_context("owner", "repo")

        assert ctx.default_branch == "release/1.0"
        # Verify tree API call URL had encoded branch
        tree_call_url = mock_get.call_args_list[3][0][0]
        assert "trees/release%2F1.0" in tree_call_url
        # Verify content API call URL had encoded ref
        content_call_url = mock_get.call_args_list[4][0][0]
        assert "ref=release%2F1.0" in content_call_url

    @patch("github_service.requests.get")
    def test_partial_retrieval_failure(self, mock_get):
        """When first file returns 404, second file 200 is retained, remaining under 7 calls."""
        mock_repo = MagicMock(status_code=200)
        mock_repo.json.return_value = {"default_branch": "main", "size": 500}
        mock_langs = MagicMock(status_code=200)
        mock_langs.json.return_value = {}
        mock_readme = MagicMock(status_code=404)
        mock_tree = MagicMock(status_code=200)
        mock_tree.json.return_value = {
            "truncated": False,
            "tree": [
                {"path": "a_fail.py", "type": "blob", "size": 100},
                {"path": "b_pass.py", "type": "blob", "size": 200},
            ]
        }
        # First file (a_fail.py) returns 404 (failed fetch)
        mock_file_404 = MagicMock(status_code=404)
        # Second file (b_pass.py) returns 200 (successful fetch)
        mock_file_200 = MagicMock(status_code=200)
        mock_file_200.json.return_value = {
            "encoding": "base64",
            "content": base64.b64encode(b"# Passed file content").decode()
        }

        mock_get.side_effect = [mock_repo, mock_langs, mock_readme, mock_tree, mock_file_404, mock_file_200]
        ctx = fetch_repository_context("owner", "repo")

        assert "a_fail.py" not in ctx.selected_files
        assert "b_pass.py" in ctx.selected_files
        assert "Passed file content" in ctx.selected_files["b_pass.py"]
        assert ctx.total_api_calls <= MAX_GITHUB_REQUESTS
        assert mock_get.call_count <= MAX_GITHUB_REQUESTS


class TestStructuredFailureClassification:
    """Tests for Fix 7C structured failure classification on RepositoryContext."""

    @patch("github_service.requests.get")
    def test_structured_rate_limit_403(self, mock_get):
        mock_res = MagicMock(status_code=403, text="rate limit exceeded")
        mock_res.headers = {"X-RateLimit-Remaining": "0"}
        mock_get.return_value = mock_res

        ctx = fetch_repository_context("owner", "repo")
        assert ctx.failure_reason == "rate_limited"
        assert ctx.upstream_status == 403
        assert ctx.rate_limited is True

    @patch("github_service.requests.get")
    def test_structured_rate_limit_429(self, mock_get):
        mock_res = MagicMock(status_code=429, text="Too Many Requests")
        mock_res.headers = {}
        mock_get.return_value = mock_res

        ctx = fetch_repository_context("owner", "repo")
        assert ctx.failure_reason == "rate_limited"
        assert ctx.upstream_status == 429
        assert ctx.rate_limited is True

    @patch("github_service.requests.get")
    def test_structured_access_denied_403(self, mock_get):
        mock_res = MagicMock(status_code=403, text="Forbidden")
        mock_res.headers = {"X-RateLimit-Remaining": "60"}
        mock_get.return_value = mock_res

        ctx = fetch_repository_context("owner", "repo")
        assert ctx.failure_reason == "access_denied"
        assert ctx.upstream_status == 403
        assert ctx.access_denied is True

    @patch("github_service.requests.get")
    def test_structured_not_found_404(self, mock_get):
        mock_res = MagicMock(status_code=404)
        mock_get.return_value = mock_res

        ctx = fetch_repository_context("owner", "repo")
        assert ctx.failure_reason == "not_found"
        assert ctx.upstream_status == 404
        assert ctx.access_denied is True

    @patch("github_service.requests.get")
    def test_structured_upstream_500(self, mock_get):
        mock_res = MagicMock(status_code=500)
        mock_get.return_value = mock_res

        ctx = fetch_repository_context("owner", "repo")
        assert ctx.failure_reason == "upstream_error"
        assert ctx.upstream_status == 500

    @patch("github_service.requests.get")
    def test_structured_timeout(self, mock_get):
        mock_get.side_effect = requests.Timeout("Gateway timed out")

        ctx = fetch_repository_context("owner", "repo")
        assert ctx.failure_reason == "timeout"
        assert ctx.upstream_status is None

    @patch("github_service.requests.get")
    def test_structured_network_error(self, mock_get):
        mock_get.side_effect = requests.ConnectionError("Connection refused")

        ctx = fetch_repository_context("owner", "repo")
        assert ctx.failure_reason == "network_error"
        assert ctx.upstream_status is None

    @patch("github_service.requests.get")
    def test_structured_malformed_json(self, mock_get):
        mock_res = MagicMock(status_code=200)
        mock_res.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_res

        ctx = fetch_repository_context("owner", "repo")
        assert ctx.failure_reason == "malformed_response"
        assert ctx.upstream_status == 200

    @patch("github_service.requests.get")
    def test_structured_upstream_401(self, mock_get):
        mock_res = MagicMock(status_code=401, text="Bad credentials")
        mock_res.headers = {}
        mock_get.return_value = mock_res

        ctx = fetch_repository_context("owner", "repo")
        assert ctx.failure_reason == "upstream_error"
        assert ctx.upstream_status == 401

    @pytest.mark.parametrize("bad_metadata", [
        None,
        [],
        "string",
        123,
    ])
    @patch("github_service.requests.get")
    def test_structured_malformed_metadata_non_dict(self, mock_get, bad_metadata):
        mock_res = MagicMock(status_code=200)
        mock_res.json.return_value = bad_metadata
        mock_get.return_value = mock_res

        ctx = fetch_repository_context("owner", "repo")
        assert ctx.failure_reason == "malformed_response"
        assert ctx.upstream_status == 200

    @pytest.mark.parametrize("missing_keys_metadata", [
        {},
        {"description": "No name or full_name or id", "size": 100},
    ])
    @patch("github_service.requests.get")
    def test_structured_malformed_metadata_missing_essential_keys(self, mock_get, missing_keys_metadata):
        mock_res = MagicMock(status_code=200)
        mock_res.json.return_value = missing_keys_metadata
        mock_get.return_value = mock_res

        ctx = fetch_repository_context("owner", "repo")
        assert ctx.failure_reason == "malformed_response"
        assert ctx.upstream_status == 200

    @pytest.mark.parametrize("bad_size_metadata", [
        {"name": "repo", "size": True},
        {"name": "repo", "size": False},
        {"name": "repo", "size": "100"},
        {"name": "repo", "size": None},
        {"name": "repo", "size": -5},
    ])
    @patch("github_service.requests.get")
    def test_structured_malformed_metadata_invalid_size(self, mock_get, bad_size_metadata):
        mock_res = MagicMock(status_code=200)
        mock_res.json.return_value = bad_size_metadata
        mock_get.return_value = mock_res

        ctx = fetch_repository_context("owner", "repo")
        assert ctx.failure_reason == "malformed_response"
        assert ctx.upstream_status == 200

    @patch("github_service.requests.get")
    def test_client_last_failure_type_reset(self, mock_get):
        from github_service import GitHubApiClient
        client = GitHubApiClient()
        client.last_failure_type = "network_error"

        mock_res = MagicMock(status_code=200)
        mock_get.return_value = mock_res

        res = client.safe_get("https://api.github.com/repos/owner/repo")
        assert res is not None
        assert client.last_failure_type is None
