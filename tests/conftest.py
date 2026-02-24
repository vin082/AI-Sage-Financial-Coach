"""
Shared pytest fixtures for AI Sage Financial Coach test suite.
"""
import os
import pytest

# Force demo mode so API endpoints skip auth and use mock data
os.environ.setdefault("DEMO_MODE", "true")


@pytest.fixture(scope="session")
def demo_profile():
    """A reproducible demo CustomerProfile (12 months of mock transactions)."""
    from data.mock_transactions import get_demo_customer
    return get_demo_customer()


@pytest.fixture(scope="session")
def demo_analyser(demo_profile):
    """TransactionAnalyser pre-loaded with demo data."""
    from coaching_agent.tools.transaction_analyser import TransactionAnalyser
    return TransactionAnalyser(demo_profile)


@pytest.fixture(scope="session")
def demo_insights(demo_analyser):
    """Pre-computed SpendingInsights (3-month window) — expensive to compute once."""
    return demo_analyser.get_full_insights(months=3)


@pytest.fixture(scope="session")
def demo_health_report(demo_insights):
    """Pre-computed FinancialHealthReport from demo data."""
    from coaching_agent.tools.financial_health import compute_health_score
    return compute_health_score(demo_insights)


@pytest.fixture
def fresh_session():
    """A blank SessionMemory for each test."""
    from coaching_agent.memory import SessionMemory
    return SessionMemory(session_id="TEST_SESSION_001", customer_id="CUST_TEST")


@pytest.fixture
def fresh_customer():
    """A blank CustomerMemory for each test."""
    from coaching_agent.memory import CustomerMemory
    return CustomerMemory(customer_id="CUST_TEST", name="Test User")


@pytest.fixture(scope="module")
def api_client():
    """FastAPI TestClient — no live server required."""
    from fastapi.testclient import TestClient
    from api.main import app
    return TestClient(app)
