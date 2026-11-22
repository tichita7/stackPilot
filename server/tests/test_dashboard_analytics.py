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


def make_request(path: str, headers: dict = None, raise_app_exceptions: bool = False):
    """Helper to execute synchronous GET request against FastAPI app via httpx."""
    async def _fetch():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app, raise_app_exceptions=raise_app_exceptions),
            base_url="http://testserver"
        ) as client:
            return await client.get(path, headers=headers)
    return asyncio.run(_fetch())


def make_post_request(
    path: str,
    json_data: dict = None,
    files: dict = None,
    data: dict = None,
    headers: dict = None,
    raise_app_exceptions: bool = False
):
    """Helper to execute synchronous POST request against FastAPI app via httpx."""
    kwargs = {}
    if json_data is not None:
        kwargs["json"] = json_data
    if files is not None:
        kwargs["files"] = files
    if data is not None:
        kwargs["data"] = data
    if headers is not None:
        kwargs["headers"] = headers

    async def _fetch():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app, raise_app_exceptions=raise_app_exceptions),
            base_url="http://testserver"
        ) as client:
            return await client.post(path, **kwargs)
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


class TestFix4DashboardMetrics:
    """Tests for Fix 4: Real Execution Latency and Tool Success Rate in dashboard analytics."""

    @patch("main.release_db")
    @patch("main.get_db")
    @patch("main.firebase_admin._apps", {"[DEFAULT]": MagicMock()})
    @patch("main.firebase_auth.verify_id_token")
    def test_pre_migration_compatibility(self, mock_verify, mock_get_db, mock_release_db):
        """When HAS_METRICS_COLUMNS is False, legacy query runs and default '—' is returned."""
        uid = "user_pre_migration"
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

        with patch("main.HAS_METRICS_COLUMNS", False):
            res = make_request(
                f"/api/dashboard-analytics/{uid}",
                headers={"Authorization": "Bearer valid_token"}
            )

        assert res.status_code == 200
        data = res.json()
        assert data["metrics"]["avg_latency"] == "—"
        assert data["metrics"]["optimization_yield"] == "—"

        # Verify query does NOT mention duration_ms or success
        executed_sql = mock_cur.execute.call_args[0][0]
        assert "duration_ms" not in executed_sql
        assert "success" not in executed_sql

    @patch("main.release_db")
    @patch("main.get_db")
    @patch("main.firebase_admin._apps", {"[DEFAULT]": MagicMock()})
    @patch("main.firebase_auth.verify_id_token")
    def test_post_migration_empty_metrics(self, mock_verify, mock_get_db, mock_release_db):
        """When HAS_METRICS_COLUMNS is True but no attempts have been measured, return '—'."""
        uid = "user_post_migration_empty"
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
            "performance_metrics": {
                "avg_duration_ms": None,
                "total_attempts": 0,
                "successful_attempts": 0,
            }
        }

        with patch("main.HAS_METRICS_COLUMNS", True):
            res = make_request(
                f"/api/dashboard-analytics/{uid}",
                headers={"Authorization": "Bearer valid_token"}
            )

        assert res.status_code == 200
        data = res.json()
        assert data["metrics"]["avg_latency"] == "—"
        assert data["metrics"]["optimization_yield"] == "—"

        # Verify query DOES filter by (success IS TRUE OR success IS NULL)
        executed_sql = mock_cur.execute.call_args[0][0]
        assert "success IS TRUE OR success IS NULL" in executed_sql
        assert "perf_metrics" in executed_sql

    @pytest.mark.parametrize("avg_dur,total,successes,expected_latency,expected_yield", [
        (840.4, 10, 10, "840ms", "100%"),
        (650.0, 10, 5, "650ms", "50%"),
        (None, 3, 0, "—", "0%"),
        (421.6, 1000, 946, "422ms", "94.6%"),
    ])
    @patch("main.release_db")
    @patch("main.get_db")
    @patch("main.firebase_admin._apps", {"[DEFAULT]": MagicMock()})
    @patch("main.firebase_auth.verify_id_token")
    def test_post_migration_metrics_calculations(
        self, mock_verify, mock_get_db, mock_release_db,
        avg_dur, total, successes, expected_latency, expected_yield
    ):
        """Verifies calculation and formatting of latency and success rate."""
        uid = "user_calc_test"
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
            "performance_metrics": {
                "avg_duration_ms": avg_dur,
                "total_attempts": total,
                "successful_attempts": successes,
            }
        }

        with patch("main.HAS_METRICS_COLUMNS", True):
            res = make_request(
                f"/api/dashboard-analytics/{uid}",
                headers={"Authorization": "Bearer valid_token"}
            )

        assert res.status_code == 200
        data = res.json()
        assert data["metrics"]["avg_latency"] == expected_latency
        assert data["metrics"]["optimization_yield"] == expected_yield


class TestFix4LogSession:
    """Unit tests for log_session behavior across schema configurations."""

    @patch("main.get_db")
    def test_log_session_empty_uid(self, mock_get_db):
        """Empty or None uid must not access database."""
        from main import log_session
        log_session("", "debug-assistant", "error text")
        log_session(None, "debug-assistant", "error text")
        mock_get_db.assert_not_called()

    @patch("main.release_db")
    @patch("main.get_db")
    def test_log_session_legacy_mode(self, mock_get_db, mock_release_db):
        """When HAS_METRICS_COLUMNS is False, 4-column insert is performed."""
        from main import log_session
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur

        with patch("main.HAS_METRICS_COLUMNS", False):
            log_session("user123", "debug-assistant", "test err", tokens=200, duration_ms=450, success=True)

        executed_sql = mock_cur.execute.call_args[0][0]
        params = mock_cur.execute.call_args[0][1]
        assert "duration_ms" not in executed_sql
        assert len(params) == 4
        assert params == ("user123", "debug-assistant", "test err", 200)

    @patch("main.release_db")
    @patch("main.get_db")
    def test_log_session_extended_mode(self, mock_get_db, mock_release_db):
        """When HAS_METRICS_COLUMNS is True, 6-column insert includes duration_ms and success."""
        from main import log_session
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur

        with patch("main.HAS_METRICS_COLUMNS", True):
            log_session("user123", "debug-assistant", "test err", tokens=240, duration_ms=530, success=True)

        executed_sql = mock_cur.execute.call_args[0][0]
        params = mock_cur.execute.call_args[0][1]
        assert "duration_ms" in executed_sql
        assert "success" in executed_sql
        assert len(params) == 6
        assert params == ("user123", "debug-assistant", "test err", 240, 530, True)

    @patch("main.get_db")
    def test_log_session_exception_swallowed(self, mock_get_db):
        """Database error inside log_session must not raise exception."""
        from main import log_session
        mock_get_db.side_effect = Exception("DB connection down")

        # Must not raise
        log_session("user123", "debug-assistant", "test err", duration_ms=100, success=True)


class TestFix4EndpointTimingAndLogging:
    """Tests for timing and best-effort outcome logging on all four AI endpoints."""

    @patch("main.log_session")
    @patch("main.client.chat.completions.create")
    @patch("main.verify_firebase_token", return_value="user_dbg")
    def test_debug_assistant_success(self, mock_verify, mock_llm, mock_log):
        mock_choice = MagicMock()
        mock_choice.message.content = '{"confidence": 95, "rootCause": "nil pointer", "technicalExplanation": [], "fixedCode": "", "prevention": []}'
        mock_llm.return_value = MagicMock(choices=[mock_choice])

        res = make_post_request("/api/debug-assistant", json_data={"id_token": "token", "error": "NullPointerException", "code": "", "language": "java"})

        assert res.status_code == 200
        assert res.json()["confidence"] == 95
        mock_log.assert_called_once()
        args, kwargs = mock_log.call_args
        assert args[0] == "user_dbg"
        assert args[1] == "debug-assistant"
        assert kwargs["success"] is True
        assert isinstance(kwargs["duration_ms"], int)
        assert kwargs["duration_ms"] >= 0

    @patch("main.log_session")
    @patch("main.client.chat.completions.create")
    @patch("main.verify_firebase_token", return_value="user_dbg")
    def test_debug_assistant_format_mismatch_failure(self, mock_verify, mock_llm, mock_log):
        mock_choice = MagicMock()
        mock_choice.message.content = 'Not valid json text'
        mock_llm.return_value = MagicMock(choices=[mock_choice])

        res = make_post_request("/api/debug-assistant", json_data={"id_token": "token", "error": "crash", "code": "", "language": "python"})

        assert res.status_code == 200
        assert res.json()["confidence"] == 50
        mock_log.assert_called_once()
        args, kwargs = mock_log.call_args
        assert kwargs["success"] is False
        assert isinstance(kwargs["duration_ms"], int)

    @patch("main.log_session")
    @patch("main.client.chat.completions.create")
    @patch("main.verify_firebase_token", return_value="user_exp")
    def test_code_explain_success(self, mock_verify, mock_llm, mock_log):
        mock_choice = MagicMock()
        mock_choice.message.content = '{"summary": "Fibonacci function", "breakdown": [], "complexity": {"time": "O(n)", "space": "O(1)"}, "improvements": []}'
        mock_llm.return_value = MagicMock(choices=[mock_choice])

        res = make_post_request("/api/code-explain", json_data={"id_token": "token", "code": "def fib(n): pass", "language": "python"})

        assert res.status_code == 200
        assert res.json()["summary"] == "Fibonacci function"
        mock_log.assert_called_once()
        args, kwargs = mock_log.call_args
        assert args[1] == "code-explain"
        assert kwargs["success"] is True
        assert kwargs["duration_ms"] >= 0

    @patch("main.log_session")
    @patch("main.PdfReader")
    @patch("main.client.chat.completions.create")
    @patch("main.verify_firebase_token", return_value="user_resume")
    def test_review_resume_success(self, mock_verify, mock_llm, mock_pdf, mock_log):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Experienced Software Engineer"
        mock_pdf.return_value = MagicMock(pages=[mock_page])

        mock_choice = MagicMock()
        mock_choice.message.content = '{"score": 90, "strengths": ["Clear format"], "improvements": [], "keywords": ["Python"]}'
        mock_llm.return_value = MagicMock(choices=[mock_choice])

        res = make_post_request(
            "/api/review-resume",
            files={"file": ("resume.pdf", b"%PDF-dummy-content", "application/pdf")},
            data={"id_token": "token"}
        )

        assert res.status_code == 200
        assert res.json()["score"] == 90
        mock_log.assert_called_once()
        args, kwargs = mock_log.call_args
        assert args[1] == "review-resume"
        assert kwargs["success"] is True
        assert kwargs["duration_ms"] >= 0

    @patch("main.log_session")
    @patch("main.requests.get")
    @patch("main.client.chat.completions.create")
    @patch("main.verify_firebase_token", return_value="user_repo")
    def test_repository_copilot_success(self, mock_verify, mock_llm, mock_get, mock_log):
        mock_repo = MagicMock(status_code=200)
        mock_repo.json.return_value = {"name": "stackPilot"}
        mock_langs = MagicMock(status_code=200)
        mock_langs.json.return_value = {"Python": 1000}
        mock_readme = MagicMock(status_code=200)
        mock_readme.json.return_value = {"content": "IyBzdGFja1BpbG90"}
        mock_get.side_effect = [mock_repo, mock_langs, mock_readme]

        mock_choice = MagicMock()
        mock_choice.message.content = '{"overview": "A cool tool", "tech_stack": ["Python"], "important_files": [], "quick_start": [], "developer_insights": {}, "change_plan": {}}'
        mock_llm.return_value = MagicMock(choices=[mock_choice])

        res = make_post_request(
            "/api/repository-copilot",
            json_data={"id_token": "token", "repo_url": "https://github.com/owner/stackPilot", "goal": "Analyze"}
        )

        assert res.status_code == 200
        assert res.json()["overview"] == "A cool tool"
        mock_log.assert_called_once()
        args, kwargs = mock_log.call_args
        assert args[1] == "repository-copilot"
        assert kwargs["success"] is True
        assert kwargs["duration_ms"] >= 0

    @patch("main.log_session")
    @patch("main.verify_firebase_token", return_value="user_repo")
    def test_repository_copilot_invalid_url_excludes_logging(self, mock_verify, mock_log):
        """Input validation failure on invalid repo url returns error and excludes logging."""
        res = make_post_request(
            "/api/repository-copilot",
            json_data={"id_token": "token", "repo_url": "invalid-url", "goal": "Analyze"}
        )

        assert res.status_code == 200
        assert "Invalid GitHub repository location format" in res.json().get("error", "")
        mock_log.assert_not_called()

    @patch("main.log_session")
    @patch("main.client.chat.completions.create")
    @patch("main.verify_firebase_token", return_value="user_resilience")
    def test_logging_failure_does_not_break_response(self, mock_verify, mock_llm, mock_log):
        """If log_session throws an exception, the AI endpoint response still succeeds."""
        mock_choice = MagicMock()
        mock_choice.message.content = '{"confidence": 92, "rootCause": "OK", "technicalExplanation": [], "fixedCode": "", "prevention": []}'
        mock_llm.return_value = MagicMock(choices=[mock_choice])
        mock_log.side_effect = Exception("Database disk full during session log")

        res = make_post_request("/api/debug-assistant", json_data={"id_token": "token", "error": "test", "code": "", "language": "python"})

        assert res.status_code == 200
        assert res.json()["confidence"] == 92

    @patch("main.log_session")
    @patch("main.firebase_admin._apps", {})
    def test_auth_failure_excludes_logging(self, mock_log):
        """When authentication fails (401), log_session is never invoked."""
        res = make_post_request("/api/debug-assistant", json_data={"id_token": "bad_token", "error": "test"})

        assert res.status_code == 401
        mock_log.assert_not_called()


class TestFix4FailurePathsAndExclusions:
    """Mocked regression tests for Fix 4 failure paths and exclusion verification."""

    # 1. Groq API exceptions in Debug Assistant
    @patch("main.log_session")
    @patch("main.client.chat.completions.create")
    @patch("main.verify_firebase_token", return_value="user_dbg_err")
    def test_debug_assistant_groq_api_exception(self, mock_verify, mock_llm, mock_log):
        """Groq API exception in debug assistant logs success=False with positive duration and returns 500."""
        mock_llm.side_effect = RuntimeError("Groq API rate limit or outage")

        res = make_post_request(
            "/api/debug-assistant",
            json_data={"id_token": "token", "error": "IndexError", "code": "arr[10]", "language": "python"}
        )

        assert res.status_code == 500
        mock_log.assert_called_once()
        args, kwargs = mock_log.call_args
        assert args[0] == "user_dbg_err"
        assert args[1] == "debug-assistant"
        assert kwargs["success"] is False
        assert isinstance(kwargs["duration_ms"], int)
        assert kwargs["duration_ms"] >= 0

    # 2. Groq API exceptions in Code Explain
    @patch("main.log_session")
    @patch("main.client.chat.completions.create")
    @patch("main.verify_firebase_token", return_value="user_exp_err")
    def test_code_explain_groq_api_exception(self, mock_verify, mock_llm, mock_log):
        """Groq API exception in code explain logs success=False with positive duration and returns 500."""
        mock_llm.side_effect = RuntimeError("Groq API timeout")

        res = make_post_request(
            "/api/code-explain",
            json_data={"id_token": "token", "code": "def foo(): pass", "language": "python"}
        )

        assert res.status_code == 500
        mock_log.assert_called_once()
        args, kwargs = mock_log.call_args
        assert args[0] == "user_exp_err"
        assert args[1] == "code-explain"
        assert kwargs["success"] is False
        assert isinstance(kwargs["duration_ms"], int)
        assert kwargs["duration_ms"] >= 0

    # 3. GitHub API 403 and 404 failures in Repository Copilot
    @patch("main.log_session")
    @patch("main.requests.get")
    @patch("main.verify_firebase_token", return_value="user_repo_err")
    def test_repository_copilot_github_403_failure(self, mock_verify, mock_get, mock_log):
        """GitHub API 403 in repo copilot logs success=False, preserves error format, returns 200 with error overview."""
        mock_res = MagicMock(status_code=403)
        mock_get.return_value = mock_res

        res = make_post_request(
            "/api/repository-copilot",
            json_data={"id_token": "token", "repo_url": "https://github.com/private/repo", "goal": "Analyze"}
        )

        assert res.status_code == 200
        data = res.json()
        assert "GitHub API access denied" in data.get("overview", "")
        assert data.get("tech_stack") == ["Error"]
        assert data.get("important_files") == []
        mock_log.assert_called_once()
        args, kwargs = mock_log.call_args
        assert args[0] == "user_repo_err"
        assert args[1] == "repository-copilot"
        assert kwargs["success"] is False
        assert isinstance(kwargs["duration_ms"], int)
        assert kwargs["duration_ms"] >= 0

    @patch("main.log_session")
    @patch("main.requests.get")
    @patch("main.verify_firebase_token", return_value="user_repo_err")
    def test_repository_copilot_github_404_failure(self, mock_verify, mock_get, mock_log):
        """GitHub API 404 in repo copilot logs success=False, preserves error format, returns 200 with error overview."""
        mock_res = MagicMock(status_code=404)
        mock_get.return_value = mock_res

        res = make_post_request(
            "/api/repository-copilot",
            json_data={"id_token": "token", "repo_url": "https://github.com/missing/repo", "goal": "Analyze"}
        )

        assert res.status_code == 200
        data = res.json()
        assert "GitHub API access denied" in data.get("overview", "")
        assert data.get("tech_stack") == ["Error"]
        mock_log.assert_called_once()
        args, kwargs = mock_log.call_args
        assert args[0] == "user_repo_err"
        assert args[1] == "repository-copilot"
        assert kwargs["success"] is False
        assert isinstance(kwargs["duration_ms"], int)
        assert kwargs["duration_ms"] >= 0

    # 4. Corrupt PDF parsing failure in Resume Review
    @patch("main.log_session")
    @patch("main.PdfReader")
    @patch("main.verify_firebase_token", return_value="user_resume_err")
    def test_review_resume_corrupt_pdf_failure(self, mock_verify, mock_pdf, mock_log):
        """Corrupt PDF in resume review logs success=False with positive duration and returns 500."""
        mock_pdf.side_effect = Exception("Corrupt PDF stream or invalid trailer")

        res = make_post_request(
            "/api/review-resume",
            files={"file": ("corrupt.pdf", b"corrupt-data", "application/pdf")},
            data={"id_token": "token"}
        )

        assert res.status_code == 500
        mock_log.assert_called_once()
        args, kwargs = mock_log.call_args
        assert args[0] == "user_resume_err"
        assert args[1] == "review-resume"
        assert kwargs["success"] is False
        assert isinstance(kwargs["duration_ms"], int)
        assert kwargs["duration_ms"] >= 0

    # 5. Database query failure in get_dashboard_analytics
    @patch("main.release_db")
    @patch("main.get_db")
    @patch("main.firebase_admin._apps", {"[DEFAULT]": MagicMock()})
    @patch("main.firebase_auth.verify_id_token")
    def test_dashboard_analytics_database_query_failure(self, mock_verify, mock_get_db, mock_release_db):
        """Database failure during analytics generation returns HTTP 500 and releases connection."""
        uid = "user_db_failure"
        mock_verify.return_value = {"uid": uid}

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        mock_cur.execute.side_effect = Exception("Database timeout on sessions query")

        res = make_request(
            f"/api/dashboard-analytics/{uid}",
            headers={"Authorization": "Bearer valid_token"}
        )

        assert res.status_code == 500
        assert "Database timeout on sessions query" in res.json().get("detail", "")
        mock_release_db.assert_called_once_with(mock_conn)

    # 6. Verification that auth and input validation failures remain excluded from execution statistics
    @patch("main.log_session")
    @patch("main.firebase_admin._apps", {})
    def test_auth_failures_excluded_across_all_tools(self, mock_log):
        """Authentication failures on all endpoints must return 401 and never invoke log_session."""
        # Code explain
        res_exp = make_post_request("/api/code-explain", json_data={"id_token": "bad", "code": "pass"})
        assert res_exp.status_code == 401

        # Resume review
        res_res = make_post_request("/api/review-resume", files={"file": ("r.pdf", b"pdf", "application/pdf")}, data={"id_token": "bad"})
        assert res_res.status_code == 401

        # Repository copilot
        res_repo = make_post_request("/api/repository-copilot", json_data={"id_token": "bad", "repo_url": "https://github.com/a/b"})
        assert res_repo.status_code == 401

        mock_log.assert_not_called()

    @patch("main.log_session")
    @patch("main.verify_firebase_token", return_value="user_val")
    def test_validation_failures_excluded_across_all_tools(self, mock_verify, mock_log):
        """Malformed payloads on all endpoints must return 422 and never invoke log_session."""
        # Debug assistant missing error field
        res_dbg = make_post_request("/api/debug-assistant", json_data={"id_token": "token"})
        assert res_dbg.status_code == 422

        # Code explain missing code field
        res_exp = make_post_request("/api/code-explain", json_data={"id_token": "token"})
        assert res_exp.status_code == 422

        # Resume review missing file
        res_res = make_post_request("/api/review-resume", data={"id_token": "token"})
        assert res_res.status_code == 422

        mock_log.assert_not_called()

