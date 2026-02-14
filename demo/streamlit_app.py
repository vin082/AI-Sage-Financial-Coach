"""
AI Sage Financial Coach — Streamlit Demo UI.

Run with: streamlit run demo/streamlit_app.py

This is the customer-facing demo for the stakeholder presentation.
It demonstrates:
  - Real-time chat with the coaching agent
  - Financial health score with pillar breakdown
  - Spending insights dashboard
  - Savings opportunity identification
"""

from __future__ import annotations

import os
import sys

import streamlit as st

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from coaching_agent.agent import CoachingAgent
from coaching_agent.tools.financial_health import compute_health_score
from coaching_agent.tools.transaction_analyser import TransactionAnalyser
from data.mock_transactions import get_demo_customer, get_demo_customer_with_life_events

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="AI Sage Financial Coach",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Brand styling
# ---------------------------------------------------------------------------

st.markdown("""
<style>
    :root {
        --sage-green: #024731;
        --sage-light-green: #006A4E;
        --sage-gold: #C8A951;
        --sage-bg: #F5F5F0;
    }
    .main { background-color: var(--sage-bg); }
    .stChatMessage { border-radius: 12px; }
    .metric-card {
        background: white;
        border-left: 4px solid var(--sage-green);
        border-radius: 8px;
        padding: 16px;
        margin: 8px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.08);
    }
    .score-display {
        font-size: 3.5rem;
        font-weight: bold;
        color: var(--sage-green);
        text-align: center;
    }
    .grade-badge {
        font-size: 1.5rem;
        font-weight: bold;
        padding: 4px 16px;
        border-radius: 20px;
        display: inline-block;
    }
    .grade-A { background: #d4edda; color: #155724; }
    .grade-B { background: #d1ecf1; color: #0c5460; }
    .grade-C { background: #fff3cd; color: #856404; }
    .grade-D { background: #f8d7da; color: #721c24; }
    .header-banner {
        background: linear-gradient(135deg, #024731 0%, #006A4E 100%);
        color: white;
        padding: 20px 24px;
        border-radius: 12px;
        margin-bottom: 24px;
    }
    .fca-notice {
        background: #fff8e1;
        border: 1px solid #f0c040;
        border-radius: 6px;
        padding: 10px 14px;
        font-size: 0.8rem;
        color: #555;
        margin-top: 8px;
    }
    .pillar-row {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 10px 0;
        border-bottom: 1px solid #eee;
    }
    .suggestion-chip {
        background: #E8F5E9;
        border: 1px solid #A5D6A7;
        color: #1B5E20;
        border-radius: 20px;
        padding: 6px 14px;
        font-size: 0.85rem;
        cursor: pointer;
        margin: 4px;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------

if "agent" not in st.session_state:
    st.session_state.demo_mode = "standard"
    profile = get_demo_customer()
    st.session_state.agent = CoachingAgent(profile)
    st.session_state.profile = profile
    st.session_state.messages = []
    st.session_state.insights = None
    st.session_state.health_report = None
    st.session_state.pending_input = None   # holds user message between reruns

agent: CoachingAgent = st.session_state.agent
profile = st.session_state.profile

# ---------------------------------------------------------------------------
# Sidebar — customer snapshot
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 16px 0;'>
        <div style='font-size:3rem;'>🏦</div>
        <div style='font-size:1.2rem; font-weight:bold; color:#024731;'>AI Sage Financial Coach</div>
        <div style='color:#666; font-size:0.85rem;'>Phase 1 MVP — Demo</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Demo profile switcher
    st.markdown("**Demo Profile**")
    demo_mode = st.radio(
        label="demo_profile",
        options=["Standard", "Life Events"],
        index=0 if st.session_state.demo_mode == "standard" else 1,
        horizontal=True,
        label_visibility="collapsed",
        help="'Life Events' injects nursery, property and income-change signals",
    )
    new_mode = "life_events" if demo_mode == "Life Events" else "standard"
    if new_mode != st.session_state.demo_mode:
        st.session_state.demo_mode = new_mode
        new_profile = (
            get_demo_customer_with_life_events()
            if new_mode == "life_events"
            else get_demo_customer()
        )
        st.session_state.profile = new_profile
        st.session_state.agent = CoachingAgent(new_profile)
        st.session_state.messages = []
        st.session_state.insights = None
        st.session_state.health_report = None
        st.session_state.pending_input = None
        st.rerun()

    profile = st.session_state.profile
    agent = st.session_state.agent

    if new_mode == "life_events":
        st.info("Life event signals active: new baby, property purchase, income change")

    st.divider()

    # Customer info
    st.markdown(f"**Customer:** {profile.name}")
    st.markdown(f"**ID:** `{profile.customer_id}`")
    st.markdown(f"**Monthly income:** £{profile.monthly_salary:,.2f}")

    st.divider()

    # Quick action: load insights
    if st.button("Load Spending Insights", use_container_width=True, type="primary"):
        analyser = TransactionAnalyser(profile)
        st.session_state.insights = analyser.get_full_insights(months=3)

    if st.button("Calculate Health Score", use_container_width=True):
        analyser = TransactionAnalyser(profile)
        insights = analyser.get_full_insights(months=3)
        st.session_state.health_report = compute_health_score(insights)

    st.divider()

    st.markdown("""
    <div class='fca-notice'>
    <b>Important:</b> This agent provides financial guidance only, not regulated financial advice.
    For personalised advice, speak to a qualified financial adviser.
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Main content — three tabs
# ---------------------------------------------------------------------------

tab_chat, tab_insights, tab_health = st.tabs(["💬 Your Coach", "📊 Spending Insights", "❤️ Health Score"])


# ============================================================
# TAB 1: CHAT
# ============================================================

with tab_chat:
    st.markdown("""
    <div class='header-banner'>
        <div style='font-size:1.4rem; font-weight:bold;'>AI Sage Financial Coach</div>
        <div style='opacity:0.85; margin-top:4px;'>
            Ask me anything about your spending, savings goals or budgeting.
            Every answer is grounded in your actual transaction data.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Suggested questions
    st.markdown("**Quick questions:**")
    suggestions = [
        "How much am I spending each month?",
        "What's my financial health score?",
        "Where can I save money?",
        "How much do I spend on eating out?",
        "Give me a monthly summary",
        "What is the 50/30/20 rule?",
    ]
    cols = st.columns(3)
    for i, suggestion in enumerate(suggestions):
        if cols[i % 3].button(suggestion, key=f"sug_{i}", use_container_width=True):
            # Store as pending and rerun immediately so the question renders first
            st.session_state.pending_input = suggestion
            st.rerun()

    st.markdown("---")

    # Chat history
    chat_container = st.container(height=420)
    with chat_container:
        if not st.session_state.messages and not st.session_state.pending_input:
            st.markdown("""
            <div style='text-align:center; padding:40px; color:#888;'>
                <div style='font-size:2rem;'>👋</div>
                <div>Hi Alex! I'm AI Sage, your financial coach.<br>
                Ask me about your spending, savings or budgeting.</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Render confirmed messages
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"],
                                     avatar="🏦" if msg["role"] == "assistant" else "👤"):
                    st.markdown(msg["content"])

            # Render pending user message immediately, then call agent
            if st.session_state.pending_input:
                pending = st.session_state.pending_input
                with st.chat_message("user", avatar="👤"):
                    st.markdown(pending)
                with st.chat_message("assistant", avatar="🏦"):
                    with st.spinner("Analysing your data..."):
                        response = agent.chat(pending)
                    st.markdown(response)
                # Commit both messages and clear pending
                st.session_state.messages.append({"role": "user", "content": pending})
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.session_state.pending_input = None

    # Input — store as pending and rerun immediately so message appears at once
    if user_input := st.chat_input("Ask your financial coach..."):
        st.session_state.pending_input = user_input
        st.rerun()


# ============================================================
# TAB 2: SPENDING INSIGHTS
# ============================================================

with tab_insights:
    st.markdown("## Spending Insights")
    st.caption("All figures computed directly from your transaction data — no estimates.")

    if st.session_state.insights is None:
        st.info("Click **Load Spending Insights** in the sidebar to see your spending breakdown.")
    else:
        ins = st.session_state.insights

        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(
                label="Avg Monthly Income",
                value=f"£{ins.average_monthly_income:,.2f}",
            )
        with col2:
            st.metric(
                label="Avg Monthly Spend",
                value=f"£{ins.average_monthly_spend:,.2f}",
                delta=f"{ins.spend_trend}",
                delta_color="inverse",
            )
        with col3:
            st.metric(
                label="Avg Monthly Surplus",
                value=f"£{ins.average_monthly_surplus:,.2f}",
            )
        with col4:
            st.metric(
                label="Current Balance",
                value=f"£{ins.current_balance_estimate:,.2f}",
            )

        st.divider()

        # Category breakdown
        col_left, col_right = st.columns([3, 2])

        with col_left:
            st.markdown("### Spending by Category (last 3 months)")
            if ins.top_categories:
                import pandas as pd
                cat_data = pd.DataFrame([
                    {
                        "Category": c.category.replace("_", " ").title(),
                        "Monthly Avg (£)": float(c.total_spend / ins.analysis_period_months),
                        "Transactions": c.transaction_count,
                    }
                    for c in ins.top_categories
                ])
                st.bar_chart(cat_data.set_index("Category")["Monthly Avg (£)"],
                             color="#024731", height=320)

        with col_right:
            st.markdown("### Monthly Breakdown")
            for s in ins.monthly_summaries:
                import calendar
                month_name = calendar.month_abbr[s.month]
                net_color = "green" if s.net >= 0 else "red"
                st.markdown(f"""
                <div class='metric-card'>
                    <b>{month_name} {s.year}</b><br>
                    Spend: £{s.total_debit:,.2f} &nbsp;|&nbsp;
                    Income: £{s.total_credit:,.2f}<br>
                    <span style='color:{net_color};'>
                        Net: {"+" if s.net >= 0 else ""}£{s.net:,.2f}
                    </span>
                </div>
                """, unsafe_allow_html=True)

        # Savings opportunities
        st.divider()
        st.markdown("### Savings Opportunities")
        analyser = TransactionAnalyser(profile)
        opps = analyser.get_savings_opportunity()

        if opps["opportunity_count"] == 0:
            st.success("Your spending looks well-managed — no major opportunities identified.")
        else:
            for opp in opps["opportunities"]:
                with st.expander(f"💡 {opp['area']} — potential saving {opp.get('potential_monthly_saving', '')} /month"):
                    for k, v in opp.items():
                        if k not in ("area",):
                            st.markdown(f"**{k.replace('_', ' ').title()}:** {v}")


# ============================================================
# TAB 3: FINANCIAL HEALTH SCORE
# ============================================================

with tab_health:
    st.markdown("## Financial Health Score")
    st.caption("Deterministic scoring based on your verified transaction data.")

    if st.session_state.health_report is None:
        st.info("Click **Calculate Health Score** in the sidebar to see your score.")
    else:
        report = st.session_state.health_report

        col_score, col_info = st.columns([1, 2])

        with col_score:
            grade_class = f"grade-{report.overall_grade}"
            score_color = (
                "#155724" if report.overall_grade == "A"
                else "#0c5460" if report.overall_grade == "B"
                else "#856404" if report.overall_grade == "C"
                else "#721c24"
            )
            st.markdown(f"""
            <div style='text-align:center; padding: 24px; background: white;
                        border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);'>
                <div style='font-size:0.9rem; color:#666; margin-bottom:8px;'>Overall Score</div>
                <div class='score-display' style='color:{score_color};'>{report.overall_score}</div>
                <div style='font-size:0.85rem; color:#888;'>out of 100</div>
                <div style='margin-top:12px;'>
                    <span class='grade-badge {grade_class}'>Grade {report.overall_grade}</span>
                </div>
                <div style='margin-top:16px; font-size:0.9rem; color:#444;'>
                    {report.summary}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_info:
            st.markdown("### Score Breakdown")
            for pillar in report.pillars:
                score_pct = pillar.score / pillar.max_score
                bar_color = (
                    "#28a745" if score_pct >= 0.85
                    else "#17a2b8" if score_pct >= 0.70
                    else "#ffc107" if score_pct >= 0.50
                    else "#dc3545"
                )
                st.markdown(f"""
                <div style='margin-bottom:16px; background:white; border-radius:10px;
                            padding:14px; box-shadow:0 1px 4px rgba(0,0,0,0.07);'>
                    <div style='display:flex; justify-content:space-between; margin-bottom:6px;'>
                        <b>{pillar.name}</b>
                        <span style='color:{bar_color}; font-weight:bold;'>
                            {pillar.score}/{pillar.max_score} — Grade {pillar.grade}
                        </span>
                    </div>
                    <div style='background:#eee; border-radius:4px; height:8px; overflow:hidden;'>
                        <div style='background:{bar_color}; width:{score_pct*100:.0f}%;
                                    height:100%; border-radius:4px;'></div>
                    </div>
                    <div style='margin-top:8px; font-size:0.85rem; color:#555;'>
                        {pillar.explanation}
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Key metrics summary
        st.divider()
        col1, col2, col3 = st.columns(3)
        col1.metric("Savings Rate", f"{report.savings_rate_pct}%",
                    delta="Target: 20%",
                    delta_color="off")
        col2.metric("Essentials % of Spend", f"{report.essentials_pct}%",
                    delta="Target: ≤60%",
                    delta_color="off")
        col3.metric("Emergency Buffer", f"{report.months_buffer} months",
                    delta="Target: 3 months",
                    delta_color="off")

        st.markdown("""
        <div class='fca-notice' style='margin-top:16px;'>
            Financial health scores are for guidance only and are based on transaction patterns.
            They do not constitute a credit assessment or regulated financial advice.
        </div>
        """, unsafe_allow_html=True)
