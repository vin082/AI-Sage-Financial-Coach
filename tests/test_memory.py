"""
Tests for coaching_agent/memory.py

Covers:
  - GoalRecord creation and ID generation
  - CustomerMemory goal deduplication (add_or_update_goal)
  - Health score tracking
  - Session summary capping
  - CustomerMemory JSON persistence (save / load roundtrip)
  - SessionMemory — history, tool calls, trace, grounded amounts
  - Session store (create_session / get_session)
"""
import os
import pytest

from coaching_agent.memory import (
    CustomerMemory,
    CustomerPreferences,
    GoalRecord,
    SessionMemory,
    SessionSummary,
    create_session,
    get_session,
    load_customer_store,
    save_customer_store,
)


# ---------------------------------------------------------------------------
# GoalRecord
# ---------------------------------------------------------------------------

class TestGoalRecord:

    def test_goal_id_generated_on_add(self, fresh_customer):
        goal = fresh_customer.add_goal("Save £5,000 for house deposit")
        assert goal.goal_id.startswith("GOAL_")

    def test_goal_ids_are_unique(self, fresh_customer):
        g1 = fresh_customer.add_goal("Goal A")
        g2 = fresh_customer.add_goal("Goal B")
        assert g1.goal_id != g2.goal_id

    def test_default_status_is_active(self, fresh_customer):
        goal = fresh_customer.add_goal("Emergency fund")
        assert goal.status == "active"

    def test_goal_stored_in_goals_list(self, fresh_customer):
        fresh_customer.add_goal("Save for car")
        assert len(fresh_customer.goals) == 1

    def test_goal_optional_fields_default_to_none(self, fresh_customer):
        goal = fresh_customer.add_goal("Vague saving goal")
        assert goal.target_amount is None
        assert goal.target_date is None

    def test_goal_with_amount_and_date(self, fresh_customer):
        goal = fresh_customer.add_goal("Holiday", target_amount=2000.0, target_date="2025-06-30")
        assert goal.target_amount == 2000.0
        assert goal.target_date == "2025-06-30"


# ---------------------------------------------------------------------------
# Goal deduplication — add_or_update_goal
# ---------------------------------------------------------------------------

class TestGoalDeduplication:

    def test_creates_new_goal_for_novel_description(self, fresh_customer):
        goal, created = fresh_customer.add_or_update_goal("Save for a holiday to Spain")
        assert created is True
        assert len(fresh_customer.goals) == 1

    def test_deduplicates_same_topic_keyword(self, fresh_customer):
        fresh_customer.add_or_update_goal("Build a holiday savings pot")
        _, created = fresh_customer.add_or_update_goal("Save for holiday")
        assert created is False
        assert len(fresh_customer.goals) == 1

    def test_deduplicates_house_deposit(self, fresh_customer):
        fresh_customer.add_or_update_goal("Save for house deposit")
        _, created = fresh_customer.add_or_update_goal("Build my house deposit fund")
        assert created is False
        assert len(fresh_customer.goals) == 1

    def test_deduplicates_emergency_fund(self, fresh_customer):
        fresh_customer.add_or_update_goal("Emergency fund", target_amount=1000)
        goal, created = fresh_customer.add_or_update_goal("Emergency fund goal", target_amount=2000)
        assert created is False
        assert goal.target_amount == 2000

    def test_distinct_topics_create_separate_goals(self, fresh_customer):
        fresh_customer.add_or_update_goal("Save for a car")
        fresh_customer.add_or_update_goal("Pay off credit card debt")
        assert len(fresh_customer.goals) == 2

    def test_longer_description_wins_on_update(self, fresh_customer):
        fresh_customer.add_or_update_goal("Holiday", target_amount=3000)
        goal, _ = fresh_customer.add_or_update_goal(
            "Save £3,000 for a holiday to Italy by summer",
            target_amount=3000,
        )
        assert "Italy" in goal.description

    def test_shorter_description_does_not_overwrite(self, fresh_customer):
        fresh_customer.add_or_update_goal("Save £5,000 for a deposit on a house in London")
        goal, _ = fresh_customer.add_or_update_goal("house deposit")
        # Longer existing description should be kept
        assert "London" in goal.description or "£5,000" in goal.description

    def test_update_preserves_goal_id(self, fresh_customer):
        g, _ = fresh_customer.add_or_update_goal("Emergency fund", target_amount=500)
        original_id = g.goal_id
        g2, _ = fresh_customer.add_or_update_goal("Emergency savings fund", target_amount=1000)
        assert g2.goal_id == original_id


# ---------------------------------------------------------------------------
# Active goals filter
# ---------------------------------------------------------------------------

class TestActiveGoals:

    def test_active_goals_excludes_cancelled(self, fresh_customer):
        fresh_customer.add_goal("Active goal")
        cancelled = fresh_customer.add_goal("Cancelled goal")
        cancelled.status = "cancelled"
        assert len(fresh_customer.active_goals) == 1

    def test_active_goals_excludes_achieved(self, fresh_customer):
        achieved = fresh_customer.add_goal("Achieved goal")
        achieved.status = "achieved"
        assert len(fresh_customer.active_goals) == 0

    def test_all_active_returned(self, fresh_customer):
        fresh_customer.add_goal("Goal 1")
        fresh_customer.add_goal("Goal 2")
        assert len(fresh_customer.active_goals) == 2


# ---------------------------------------------------------------------------
# Health score tracking
# ---------------------------------------------------------------------------

class TestHealthScoreTracking:

    def test_update_health_score_stores_value(self, fresh_customer):
        fresh_customer.update_health_score(72)
        assert fresh_customer.last_health_score == 72

    def test_update_health_score_stores_iso_date(self, fresh_customer):
        from datetime import date
        fresh_customer.update_health_score(60)
        # Should be parseable as ISO date
        parsed = date.fromisoformat(fresh_customer.last_health_score_date)
        assert parsed is not None

    def test_health_score_defaults_to_none(self, fresh_customer):
        assert fresh_customer.last_health_score is None
        assert fresh_customer.last_health_score_date is None

    def test_health_score_can_be_updated(self, fresh_customer):
        fresh_customer.update_health_score(50)
        fresh_customer.update_health_score(75)
        assert fresh_customer.last_health_score == 75


# ---------------------------------------------------------------------------
# Session summaries
# ---------------------------------------------------------------------------

class TestSessionSummaries:

    def test_summary_added_to_list(self, fresh_customer):
        s = SessionSummary(session_id="S001", date="2025-01-01", summary="Good session.")
        fresh_customer.add_session_summary(s)
        assert len(fresh_customer.previous_sessions) == 1

    def test_summaries_capped_at_five(self, fresh_customer):
        for i in range(7):
            fresh_customer.add_session_summary(SessionSummary(
                session_id=f"S{i:03d}",
                date="2025-01-01",
                summary=f"Session {i}",
            ))
        assert len(fresh_customer.previous_sessions) == 5

    def test_summaries_keeps_most_recent(self, fresh_customer):
        for i in range(7):
            fresh_customer.add_session_summary(SessionSummary(
                session_id=f"S{i:03d}",
                date="2025-01-01",
                summary=f"Session {i}",
            ))
        # Most recent 5 should be sessions 2-6
        ids = [s.session_id for s in fresh_customer.previous_sessions]
        assert "S006" in ids
        assert "S000" not in ids

    def test_conversation_count_increments(self, fresh_customer):
        fresh_customer.add_session_summary(
            SessionSummary(session_id="S001", date="2025-01-01", summary="Done.")
        )
        assert fresh_customer.conversation_count == 1


# ---------------------------------------------------------------------------
# JSON persistence
# ---------------------------------------------------------------------------

class TestCustomerMemoryPersistence:

    def test_save_and_load_roundtrip(self, tmp_path, monkeypatch):
        import coaching_agent.memory as mem_module
        monkeypatch.setattr(mem_module, "_STORE_DIR", str(tmp_path))

        customer = CustomerMemory(customer_id="PERSIST_001", name="Persist User")
        customer.add_goal("Save £1,000 for emergency")
        customer.update_health_score(78)
        customer.preferences.preferred_tone = "concise"
        save_customer_store(customer)

        loaded = load_customer_store("PERSIST_001", "Persist User")
        assert loaded.name == "Persist User"
        assert len(loaded.goals) == 1
        assert loaded.last_health_score == 78
        assert loaded.preferences.preferred_tone == "concise"

    def test_load_returns_fresh_record_if_not_found(self, tmp_path, monkeypatch):
        import coaching_agent.memory as mem_module
        monkeypatch.setattr(mem_module, "_STORE_DIR", str(tmp_path))

        customer = load_customer_store("NONEXISTENT_XYZ", "New User")
        assert customer.customer_id == "NONEXISTENT_XYZ"
        assert customer.name == "New User"
        assert len(customer.goals) == 0

    def test_goals_persist_with_correct_types(self, tmp_path, monkeypatch):
        import coaching_agent.memory as mem_module
        monkeypatch.setattr(mem_module, "_STORE_DIR", str(tmp_path))

        customer = CustomerMemory(customer_id="GOAL_PERSIST", name="User")
        customer.add_goal("Holiday", target_amount=2500.0, target_date="2025-08-01")
        save_customer_store(customer)

        loaded = load_customer_store("GOAL_PERSIST", "User")
        goal = loaded.goals[0]
        assert goal.description == "Holiday"
        assert goal.target_amount == 2500.0
        assert goal.target_date == "2025-08-01"

    def test_save_does_not_raise_on_invalid_dir(self, monkeypatch):
        """Persistence failure must never crash the agent."""
        import coaching_agent.memory as mem_module
        monkeypatch.setattr(mem_module, "_STORE_DIR", "/nonexistent/invalid/path/xyz")
        customer = CustomerMemory(customer_id="X", name="Y")
        # Should not raise
        save_customer_store(customer)


# ---------------------------------------------------------------------------
# SessionMemory
# ---------------------------------------------------------------------------

class TestSessionMemory:

    def test_add_message_increases_count(self, fresh_session):
        fresh_session.add_message("user", "Hello")
        assert len(fresh_session.messages) == 1

    def test_add_multiple_messages(self, fresh_session):
        fresh_session.add_message("user", "Hello")
        fresh_session.add_message("assistant", "Hi there")
        assert len(fresh_session.messages) == 2

    def test_get_history_limited_to_last_10(self, fresh_session):
        for i in range(15):
            fresh_session.add_message("user", f"Message {i}")
        history = fresh_session.get_history()
        assert len(history) == 10

    def test_get_history_returns_most_recent(self, fresh_session):
        for i in range(12):
            fresh_session.add_message("user", f"Message {i}")
        history = fresh_session.get_history()
        # Last message in history should be message 11
        assert history[-1]["content"] == "Message 11"

    def test_register_tool_call_appends(self, fresh_session):
        fresh_session.register_tool_call("get_spending_insights")
        assert "get_spending_insights" in fresh_session.tool_calls_made

    def test_register_multiple_tool_calls(self, fresh_session):
        fresh_session.register_tool_call("tool_a")
        fresh_session.register_tool_call("tool_b")
        assert len(fresh_session.tool_calls_made) == 2

    def test_add_trace_entry(self, fresh_session):
        fresh_session.add_trace_entry("get_spending_insights", {}, "£500 monthly spend")
        assert len(fresh_session.tool_trace) == 1
        entry = fresh_session.tool_trace[0]
        assert entry["tool"] == "get_spending_insights"
        assert entry["result_summary"] == "£500 monthly spend"

    def test_trace_entry_stores_args(self, fresh_session):
        fresh_session.add_trace_entry("some_tool", {"months": 3}, "result")
        assert fresh_session.tool_trace[0]["args"] == {"months": 3}

    def test_grounded_amounts_starts_empty(self, fresh_session):
        assert fresh_session.grounded_amounts == set()

    def test_chart_data_starts_none(self, fresh_session):
        assert fresh_session.chart_data is None

    def test_grounded_amounts_can_be_updated(self, fresh_session):
        fresh_session.grounded_amounts.update({"£100.00", "£200.00"})
        assert "£100.00" in fresh_session.grounded_amounts


# ---------------------------------------------------------------------------
# Session store
# ---------------------------------------------------------------------------

class TestSessionStore:

    def test_create_session_returns_session_memory(self):
        sid = f"TEST_SID_{id(self)}"
        session = create_session(sid, "C001")
        assert isinstance(session, SessionMemory)
        assert session.session_id == sid

    def test_get_session_returns_created_session(self):
        sid = f"TEST_SID_GET_{id(self)}"
        create_session(sid, "C001")
        retrieved = get_session(sid)
        assert retrieved is not None
        assert retrieved.session_id == sid

    def test_get_session_returns_none_for_unknown(self):
        result = get_session("DEFINITELY_DOES_NOT_EXIST_XYZ_999")
        assert result is None

    def test_session_customer_id_set_correctly(self):
        sid = f"TEST_CUST_{id(self)}"
        session = create_session(sid, "CUST_XYZ")
        assert session.customer_id == "CUST_XYZ"
