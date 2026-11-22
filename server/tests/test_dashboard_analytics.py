import sys
import os
import asyncio
from unittest.mock import MagicMock, patch
import pytest
import httpx

# Ensure server module can be imported
SERVER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

from main import app
from firebase_admin import auth as firebase_auth


def make_request(path: str, headers: dict = None):
    """Helper to execute synchronous GET request against FastAPI app via httpx."""
    async def _fetch():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver"
        ) as client:
            return await client.get(path, headers=headers)
    return asyncio.run(_fetch())


class TestDashboardAnalyticsAuthorization:
    """Regression test suite for GET /api/dashboard-analytics/{uid} authorization."""

    @patch("main.get_db")
    def test_missing_authorization_header(self, mock_get_db):
        """Request without Authorization header must return 401 and never touch the database."""
        res = make_request("/api/dashboard-analytics/user_123")

        assert res.status_code == 401
        assert "Authorization header is required" in res.json().get("detail", "")
        mock_get_db.assert_not_called()

    @pytest.mark.parametrize("malformed_header", [
        "Bearer",
        "Bearer   ",
        "Basic token123",
        "Token token123",
        "Bearer token1 token2",
        "InvalidFormat",
    ])
    @patch("main.get_db")
    def test_malformed_authorization_header(self, mock_get_db, malformed_header):
        """Malformed Authorization header must return 401 and never touch the database."""
        res = make_request(
            "/api/dashboard-analytics/user_123",
            headers={"Authorization": malformed_header}
        )

        assert res.status_code == 401
        mock_get_db.assert_not_called()

    @patch("main.get_db")
    @patch("main.firebase_admin._apps", {"[DEFAULT]": MagicMock()})
    @patch("main.firebase_auth.verify_id_token")
    def test_invalid_firebase_token(self, mock_verify, mock_get_db):
        """Invalid token must return 401 and never touch the database."""
        mock_verify.side_effect = firebase_auth.InvalidIdTokenError("Invalid token")

        res = make_request(
            "/api/dashboard-analytics/user_123",
            headers={"Authorization": "Bearer invalid_token_xyz"}
        )

        assert res.status_code == 401
        assert "Invalid Firebase token" in res.json().get("detail", "")
        mock_get_db.assert_not_called()
        # Verify no token is leaked in response
        assert "invalid_token_xyz" not in res.text

    @patch("main.get_db")
    @patch("main.firebase_admin._apps", {"[DEFAULT]": MagicMock()})
    @patch("main.firebase_auth.verify_id_token")
    def test_expired_firebase_token(self, mock_verify, mock_get_db):
        """Expired token must return 401 and never touch the database."""
        mock_verify.side_effect = firebase_auth.ExpiredIdTokenError("Token expired", None)

        res = make_request(
            "/api/dashboard-analytics/user_123",
            headers={"Authorization": "Bearer expired_token_xyz"}
        )

        assert res.status_code == 401
        assert "expired" in res.json().get("detail", "").lower()
        mock_get_db.assert_not_called()
        assert "expired_token_xyz" not in res.text

    @patch("main.get_db")
    @patch("main.firebase_admin._apps", {})
    def test_verification_unavailable_when_no_firebase_app(self, mock_get_db):
        """When Firebase SDK is uninitialized, return 401 without database access."""
        res = make_request(
            "/api/dashboard-analytics/user_123",
            headers={"Authorization": "Bearer some_token"}
        )

        assert res.status_code == 401
        assert "unavailable" in res.json().get("detail", "").lower()
        mock_get_db.assert_not_called()

    @patch("main.get_db")
    @patch("main.firebase_admin._apps", {"[DEFAULT]": MagicMock()})
    @patch("main.firebase_auth.verify_id_token")
    def test_verification_fails_with_unexpected_error(self, mock_verify, mock_get_db):
        """Internal verification failure must return 401 without exposing exception details."""
        mock_verify.side_effect = RuntimeError("Sensitive internal certificate error")

        res = make_request(
            "/api/dashboard-analytics/user_123",
            headers={"Authorization": "Bearer some_token"}
        )

        assert res.status_code == 401
        # Confirm internal exception details are NOT leaked
        assert "Sensitive internal certificate error" not in res.text
        assert res.json().get("detail") == "Token verification failed."
        mock_get_db.assert_not_called()

    @patch("main.get_db")
    @patch("main.firebase_admin._apps", {"[DEFAULT]": MagicMock()})
    @patch("main.firebase_auth.verify_id_token")
    def test_uid_mismatch_forbidden(self, mock_verify, mock_get_db):
        """When token UID does not match URL UID, return 403 Forbidden without database query."""
        mock_verify.return_value = {"uid": "user_attacker"}

        res = make_request(
            "/api/dashboard-analytics/user_victim",
            headers={"Authorization": "Bearer valid_attacker_token"}
        )

        assert res.status_code == 403
        assert "mismatch" in res.json().get("detail", "").lower()
        mock_get_db.assert_not_called()

    @patch("main.release_db")
    @patch("main.get_db")
    @patch("main.firebase_admin._apps", {"[DEFAULT]": MagicMock()})
    @patch("main.firebase_auth.verify_id_token")
    def test_authenticated_matching_uid_success(self, mock_verify, mock_get_db, mock_release_db):
        """When token UID matches URL UID, execute database query and return 200 with analytics."""
        target_uid = "user_legitimate_123"
        mock_verify.return_value = {"uid": target_uid}

        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur

        mock_cur.fetchone.return_value = {
            "recent_sessions": [
                {
                    "tool": "debug-assistant",
                    "input_summary": "Null pointer check",
                    "tokens_used": 150,
                    "created_at": "2026-11-22T10:00:00"
                }
            ],
            "weekly_metrics": [
                {
                    "session_date": "2026-11-22",
                    "total_count": 3
                }
            ],
            "favorite_tool": {
                "tool": "debug-assistant",
                "count": 5
            }
        }

        res = make_request(
            f"/api/dashboard-analytics/{target_uid}",
            headers={"Authorization": "Bearer valid_user_token"}
        )

        assert res.status_code == 200
        data = res.json()
        assert "telemetry_stream" in data
        assert "time_series_7d" in data
        assert "metrics" in data
        assert len(data["telemetry_stream"]) == 1
        assert data["metrics"]["favorite_assistant"] == "Debug-Assistant (5 runs)"

        # Verify DB query was executed with target_uid
        mock_get_db.assert_called_once()
        mock_cur.execute.assert_called_once()
        query_args = mock_cur.execute.call_args[0][1]
        assert query_args == (target_uid, target_uid, target_uid)
        mock_release_db.assert_called_once_with(mock_conn)
