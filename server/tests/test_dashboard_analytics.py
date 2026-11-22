import sys
import os
import asyncio
from datetime import datetime, timedelta
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


def get_current_ist_date():
    """Returns today's date in Asia/Kolkata (UTC+05:30)."""
    return (datetime.utcnow() + timedelta(hours=5, minutes=30)).date()


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

        today_ist = get_current_ist_date()

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
                    "created_at": f"{today_ist}T10:00:00"
                }
            ],
            "weekly_metrics": [
                {
                    "session_date": str(today_ist),
                    "total_count": 3
                }
            ],
            "favorite_tool": {
                "tool": "debug-assistant",
                "count": 5
            },
            "prev_cycle_count": 2,
            "active_days": [str(today_ist)]
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
        assert data["metrics"]["streak_count"] == "1 Day Active"
        assert "+50% growth vs last cycle" in data["metrics"]["workspace_momentum"]

        mock_get_db.assert_called_once()
        mock_cur.execute.assert_called_once()
        query_args = mock_cur.execute.call_args[0][1]
        assert query_args[0] == target_uid
        assert query_args[1] == target_uid
        assert query_args[4] == target_uid
        assert query_args[5] == target_uid
        assert query_args[8] == target_uid
        mock_release_db.assert_called_once_with(mock_conn)


class TestDashboardActivityMetrics:
    """Test suite for real PostgreSQL metric calculations (Fix 3)."""

    @patch("main.release_db")
    @patch("main.get_db")
    @patch("main.firebase_admin._apps", {"[DEFAULT]": MagicMock()})
    @patch("main.firebase_auth.verify_id_token")
    def test_new_user_zero_sessions(self, mock_verify, mock_get_db, mock_release_db):
        """New user with 0 sessions has zero growth and zero active days."""
        uid = "user_new"
        mock_verify.return_value = {"uid": uid}

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur

        mock_cur.fetchone.return_value = {
            "recent_sessions": None,
            "weekly_metrics": None,
            "favorite_tool": None,
            "prev_cycle_count": 0,
            "active_days": None,
        }

        res = make_request(
            f"/api/dashboard-analytics/{uid}",
            headers={"Authorization": "Bearer valid_token"}
        )

        assert res.status_code == 200
        data = res.json()
        assert data["metrics"]["workspace_momentum"] == "+0% growth vs last cycle"
        assert data["metrics"]["streak_count"] == "0 Days Active"
        assert data["metrics"]["favorite_assistant"] == "None (0 runs)"

    @patch("main.release_db")
    @patch("main.get_db")
    @patch("main.firebase_admin._apps", {"[DEFAULT]": MagicMock()})
    @patch("main.firebase_auth.verify_id_token")
    def test_first_activity_new_activity_label(self, mock_verify, mock_get_db, mock_release_db):
        """When previous cycle count = 0 and current cycle > 0, return 'New activity'."""
        uid = "user_first_activity"
        mock_verify.return_value = {"uid": uid}

        today_ist = get_current_ist_date()

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur

        mock_cur.fetchone.return_value = {
            "recent_sessions": None,
            "weekly_metrics": [{"session_date": str(today_ist), "total_count": 4}],
            "favorite_tool": {"tool": "code-explain", "count": 4},
            "prev_cycle_count": 0,
            "active_days": [str(today_ist)],
        }

        res = make_request(
            f"/api/dashboard-analytics/{uid}",
            headers={"Authorization": "Bearer valid_token"}
        )

        assert res.status_code == 200
        data = res.json()
        assert data["metrics"]["workspace_momentum"] == "New activity"
        assert data["metrics"]["streak_count"] == "1 Day Active"

    @patch("main.release_db")
    @patch("main.get_db")
    @patch("main.firebase_admin._apps", {"[DEFAULT]": MagicMock()})
    @patch("main.firebase_auth.verify_id_token")
    def test_positive_growth_percentage(self, mock_verify, mock_get_db, mock_release_db):
        """Current 6 vs previous 4 yields +50% growth."""
        uid = "user_positive"
        mock_verify.return_value = {"uid": uid}

        today_ist = get_current_ist_date()

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur

        mock_cur.fetchone.return_value = {
            "recent_sessions": None,
            "weekly_metrics": [{"session_date": str(today_ist), "total_count": 6}],
            "favorite_tool": {"tool": "debug-assistant", "count": 6},
            "prev_cycle_count": 4,
            "active_days": [str(today_ist)],
        }

        res = make_request(
            f"/api/dashboard-analytics/{uid}",
            headers={"Authorization": "Bearer valid_token"}
        )

        assert res.status_code == 200
        data = res.json()
        assert data["metrics"]["workspace_momentum"] == "+50% growth vs last cycle"

    @patch("main.release_db")
    @patch("main.get_db")
    @patch("main.firebase_admin._apps", {"[DEFAULT]": MagicMock()})
    @patch("main.firebase_auth.verify_id_token")
    def test_negative_growth_percentage(self, mock_verify, mock_get_db, mock_release_db):
        """Current 2 vs previous 4 yields -50% growth."""
        uid = "user_negative"
        mock_verify.return_value = {"uid": uid}

        today_ist = get_current_ist_date()

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur

        mock_cur.fetchone.return_value = {
            "recent_sessions": None,
            "weekly_metrics": [{"session_date": str(today_ist), "total_count": 2}],
            "favorite_tool": {"tool": "debug-assistant", "count": 2},
            "prev_cycle_count": 4,
            "active_days": [str(today_ist)],
        }

        res = make_request(
            f"/api/dashboard-analytics/{uid}",
            headers={"Authorization": "Bearer valid_token"}
        )

        assert res.status_code == 200
        data = res.json()
        assert data["metrics"]["workspace_momentum"] == "-50% growth vs last cycle"

    @patch("main.release_db")
    @patch("main.get_db")
    @patch("main.firebase_admin._apps", {"[DEFAULT]": MagicMock()})
    @patch("main.firebase_auth.verify_id_token")
    def test_zero_growth_equal_cycles(self, mock_verify, mock_get_db, mock_release_db):
        """Current 8 vs previous 8 yields +0% growth."""
        uid = "user_equal"
        mock_verify.return_value = {"uid": uid}

        today_ist = get_current_ist_date()

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur

        mock_cur.fetchone.return_value = {
            "recent_sessions": None,
            "weekly_metrics": [{"session_date": str(today_ist), "total_count": 8}],
            "favorite_tool": {"tool": "debug-assistant", "count": 8},
            "prev_cycle_count": 8,
            "active_days": [str(today_ist)],
        }

        res = make_request(
            f"/api/dashboard-analytics/{uid}",
            headers={"Authorization": "Bearer valid_token"}
        )

        assert res.status_code == 200
        data = res.json()
        assert data["metrics"]["workspace_momentum"] == "+0% growth vs last cycle"

    @patch("main.release_db")
    @patch("main.get_db")
    @patch("main.firebase_admin._apps", {"[DEFAULT]": MagicMock()})
    @patch("main.firebase_auth.verify_id_token")
    def test_consecutive_days_streak(self, mock_verify, mock_get_db, mock_release_db):
        """Active today and previous 3 consecutive days yields '4 Days Active'."""
        uid = "user_consecutive_streak"
        mock_verify.return_value = {"uid": uid}

        today_ist = get_current_ist_date()
        day_1 = today_ist - timedelta(days=1)
        day_2 = today_ist - timedelta(days=2)
        day_3 = today_ist - timedelta(days=3)

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur

        mock_cur.fetchone.return_value = {
            "recent_sessions": None,
            "weekly_metrics": [
                {"session_date": str(today_ist), "total_count": 2},
                {"session_date": str(day_1), "total_count": 3},
                {"session_date": str(day_2), "total_count": 1},
                {"session_date": str(day_3), "total_count": 4},
            ],
            "favorite_tool": {"tool": "debug-assistant", "count": 10},
            "prev_cycle_count": 0,
            "active_days": [str(today_ist), str(day_1), str(day_2), str(day_3)],
        }

        res = make_request(
            f"/api/dashboard-analytics/{uid}",
            headers={"Authorization": "Bearer valid_token"}
        )

        assert res.status_code == 200
        data = res.json()
        assert data["metrics"]["streak_count"] == "4 Days Active"

    @patch("main.release_db")
    @patch("main.get_db")
    @patch("main.firebase_admin._apps", {"[DEFAULT]": MagicMock()})
    @patch("main.firebase_auth.verify_id_token")
    def test_yesterday_continuity_streak(self, mock_verify, mock_get_db, mock_release_db):
        """When not yet active today, but active yesterday and 2 days ago, streak continues from yesterday."""
        uid = "user_yesterday_streak"
        mock_verify.return_value = {"uid": uid}

        today_ist = get_current_ist_date()
        day_1 = today_ist - timedelta(days=1)
        day_2 = today_ist - timedelta(days=2)

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur

        mock_cur.fetchone.return_value = {
            "recent_sessions": None,
            "weekly_metrics": [
                {"session_date": str(day_1), "total_count": 3},
                {"session_date": str(day_2), "total_count": 2},
            ],
            "favorite_tool": {"tool": "code-explain", "count": 5},
            "prev_cycle_count": 0,
            "active_days": [str(day_1), str(day_2)],
        }

        res = make_request(
            f"/api/dashboard-analytics/{uid}",
            headers={"Authorization": "Bearer valid_token"}
        )

        assert res.status_code == 200
        data = res.json()
        assert data["metrics"]["streak_count"] == "2 Days Active"

    @patch("main.release_db")
    @patch("main.get_db")
    @patch("main.firebase_admin._apps", {"[DEFAULT]": MagicMock()})
    @patch("main.firebase_auth.verify_id_token")
    def test_broken_streak_with_gap(self, mock_verify, mock_get_db, mock_release_db):
        """Active today, missed yesterday, active 2 days ago yields only '1 Day Active'."""
        uid = "user_broken_streak"
        mock_verify.return_value = {"uid": uid}

        today_ist = get_current_ist_date()
        day_2 = today_ist - timedelta(days=2)

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur

        mock_cur.fetchone.return_value = {
            "recent_sessions": None,
            "weekly_metrics": [
                {"session_date": str(today_ist), "total_count": 2},
                {"session_date": str(day_2), "total_count": 5},
            ],
            "favorite_tool": {"tool": "debug-assistant", "count": 7},
            "prev_cycle_count": 0,
            "active_days": [str(today_ist), str(day_2)],
        }

        res = make_request(
            f"/api/dashboard-analytics/{uid}",
            headers={"Authorization": "Bearer valid_token"}
        )

        assert res.status_code == 200
        data = res.json()
        assert data["metrics"]["streak_count"] == "1 Day Active"

    @patch("main.release_db")
    @patch("main.get_db")
    @patch("main.firebase_admin._apps", {"[DEFAULT]": MagicMock()})
    @patch("main.firebase_auth.verify_id_token")
    def test_neither_today_nor_yesterday_active(self, mock_verify, mock_get_db, mock_release_db):
        """Activity 2 days ago but neither today nor yesterday yields '0 Days Active'."""
        uid = "user_inactive_streak"
        mock_verify.return_value = {"uid": uid}

        today_ist = get_current_ist_date()
        day_2 = today_ist - timedelta(days=2)
        day_3 = today_ist - timedelta(days=3)

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur

        mock_cur.fetchone.return_value = {
            "recent_sessions": None,
            "weekly_metrics": [
                {"session_date": str(day_2), "total_count": 2},
                {"session_date": str(day_3), "total_count": 5},
            ],
            "favorite_tool": {"tool": "debug-assistant", "count": 7},
            "prev_cycle_count": 0,
            "active_days": [str(day_2), str(day_3)],
        }

        res = make_request(
            f"/api/dashboard-analytics/{uid}",
            headers={"Authorization": "Bearer valid_token"}
        )

        assert res.status_code == 200
        data = res.json()
        assert data["metrics"]["streak_count"] == "0 Days Active"
