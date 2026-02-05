"""
Daily Action-to-Impact Coach - Streamlit Frontend

A user-friendly interface for tracking daily environmental impact
and receiving personalized recommendations.
"""

import streamlit as st
import requests
import pandas as pd
from datetime import date, timedelta
from typing import Optional

# Configuration
API_BASE_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="Impact Coach",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================================
# API Helper Functions
# ============================================================================

def api_get(endpoint: str, params: Optional[dict] = None) -> Optional[dict]:
    """Make GET request to API."""
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}", params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {e}")
        return None


def api_post(endpoint: str, data: dict) -> Optional[dict]:
    """Make POST request to API."""
    try:
        response = requests.post(f"{API_BASE_URL}{endpoint}", json=data, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {e}")
        return None


def api_delete(endpoint: str) -> bool:
    """Make DELETE request to API."""
    try:
        response = requests.delete(f"{API_BASE_URL}{endpoint}", timeout=10)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException:
        return False


# ============================================================================
# Data Loading Functions
# ============================================================================

@st.cache_data(ttl=300)
def load_factors():
    """Load available factors from API."""
    return api_get("/factors")


def get_factor_options(category: str, factors: dict) -> dict:
    """Get factor options for a category as {display_name: item_key}."""
    if not factors or category not in factors:
        return {}

    options = {}
    for factor in factors[category]:
        display = f"{factor['item'].replace('_', ' ').title()} ({factor['description']})"
        options[display] = factor['item']
    return options


# ============================================================================
# UI Components
# ============================================================================

def render_sidebar():
    """Render the sidebar with navigation and quick stats."""
    with st.sidebar:
        st.title("🌱 Impact Coach")
        st.markdown("---")

        # Navigation
        page = st.radio(
            "Navigate",
            ["💬 Chatbot", "📝 Log Action", "📊 Dashboard", "📈 Weekly Trend", "📄 Reports", "📚 Factor Reference"],
            label_visibility="collapsed"
        )

        st.markdown("---")

        # Quick stats
        coaching = api_get("/coach/daily")
        if coaching:
            st.metric("Today's CO₂e", f"{coaching['impact_summary']['total_co2e_kg']:.2f} kg")
            st.metric("Actions Logged", coaching['impact_summary']['action_count'])
            st.metric("Streak", f"{coaching['streak_days']} days")

        return page


def render_log_action_page():
    """Render the action logging page."""
    st.header("📝 Log Your Action")

    factors = load_factors()
    if not factors:
        st.warning("Could not load factors. Is the API running?")
        st.info("Start the API with: `uvicorn backend.main:app --reload`")
        return

    col1, col2 = st.columns([2, 1])

    with col1:
        # Category selection
        category = st.selectbox(
            "Category",
            ["mobility", "purchase", "home_energy"],
            format_func=lambda x: {
                "mobility": "🚗 Mobility (Transportation)",
                "purchase": "🛒 Purchase (Consumption)",
                "home_energy": "🏠 Home Energy"
            }[x]
        )

        # Item selection based on category
        options = get_factor_options(category, factors)
        if options:
            selected_display = st.selectbox("Item", list(options.keys()))
            item = options[selected_display]
        else:
            item = st.text_input("Item (e.g., taxi_ice, beef_meal)")

        # Amount input
        unit_map = {
            "mobility": "km",
            "home_energy": "kWh/m³",
            "purchase": "units"
        }
        amount = st.number_input(
            f"Amount ({unit_map.get(category, 'units')})",
            min_value=0.1,
            value=1.0,
            step=0.5
        )

        # Optional fields
        with st.expander("Optional Details"):
            if category == "home_energy":
                time_of_day = st.selectbox(
                    "Time of Day",
                    ["standard", "peak", "off_peak"],
                    format_func=lambda x: {
                        "standard": "Standard",
                        "peak": "Peak Hours (Higher Carbon)",
                        "off_peak": "Off-Peak (Lower Carbon)"
                    }[x]
                )
            else:
                time_of_day = "standard"

            location = st.text_input("Location (optional)")
            notes = st.text_area("Notes (optional)", max_chars=500)

        # Submit button
        if st.button("Log Action", type="primary", use_container_width=True):
            action_data = {
                "category": category,
                "item": item,
                "amount": amount,
                "time_of_day": time_of_day,
                "location": location if location else None,
                "notes": notes if notes else None
            }

            result = api_post("/actions", action_data)
            if result:
                st.success(f"Logged! Impact: {result['co2e_kg']:.3f} kg CO₂e, {result['water_l']:.1f} L water")
                st.cache_data.clear()
                st.rerun()

    with col2:
        st.subheader("Today's Actions")
        actions = api_get("/actions")
        if actions:
            for action in actions[:5]:
                with st.container():
                    st.markdown(f"""
                    **{action['item'].replace('_', ' ').title()}**
                    - Amount: {action['amount']}
                    - CO₂e: {action['co2e_kg']:.3f} kg
                    """)
                    if st.button("🗑️", key=f"del_{action['id']}"):
                        if api_delete(f"/actions/{action['id']}"):
                            st.cache_data.clear()
                            st.rerun()
                    st.markdown("---")
        else:
            st.info("No actions logged today")


def render_dashboard_page():
    """Render the main dashboard page."""
    st.header("📊 Today's Impact Dashboard")

    coaching = api_get("/coach/daily")
    if not coaching:
        st.warning("No data available. Start logging actions!")
        return

    # Summary card
    st.info(coaching['summary'])

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total CO₂e", f"{coaching['impact_summary']['total_co2e_kg']:.2f} kg")
    with col2:
        st.metric("Total Water", f"{coaching['impact_summary']['total_water_l']:.0f} L")
    with col3:
        st.metric("Actions", coaching['impact_summary']['action_count'])
    with col4:
        st.metric("Streak", f"{coaching['streak_days']} days")

    st.markdown("---")

    # Category breakdown
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Impact by Category")
        breakdown = coaching['impact_summary']['breakdown_by_category']
        if breakdown:
            df = pd.DataFrame([
                {
                    "Category": cat.replace("_", " ").title(),
                    "CO₂e (kg)": data['co2e_kg'],
                    "Percentage": f"{data['percentage']}%"
                }
                for cat, data in breakdown.items()
            ])
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Simple bar chart
            if len(df) > 0:
                chart_df = pd.DataFrame({
                    "Category": [cat.replace("_", " ").title() for cat in breakdown.keys()],
                    "CO₂e (kg)": [data['co2e_kg'] for data in breakdown.values()]
                })
                st.bar_chart(chart_df.set_index("Category"))
        else:
            st.info("No category data yet")

    with col2:
        st.subheader("Top Contributors")
        contributors = coaching['impact_summary']['top_contributors']
        if contributors:
            for i, contrib in enumerate(contributors, 1):
                st.markdown(f"""
                **{i}. {contrib['item'].replace('_', ' ').title()}**
                - Amount: {contrib['amount']}
                - CO₂e: {contrib['co2e_kg']:.3f} kg
                """)
        else:
            st.info("No contributors yet")

    st.markdown("---")

    # Recommendations
    st.subheader("🎯 Recommended Actions")
    recommendations = coaching['recommendations']
    if recommendations:
        cols = st.columns(len(recommendations))
        for i, (col, rec) in enumerate(zip(cols, recommendations)):
            with col:
                difficulty_emoji = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}[rec['difficulty']]
                st.markdown(f"""
                **{rec['action']}**

                {difficulty_emoji} {rec['difficulty'].title()} | {rec['category'].replace('_', ' ').title()}

                _{rec['rationale']}_

                **Potential Savings:**
                - CO₂e: {rec['estimated_savings_co2e_kg']:.2f} kg
                - Water: {rec['estimated_savings_water_l']:.0f} L
                """)
    else:
        st.info("Log some actions to get personalized recommendations!")


def render_weekly_trend_page():
    """Render the weekly trend page."""
    st.header("📈 Weekly Trend")

    trend = api_get("/impact/weekly")
    if not trend or all(v == 0 for v in trend['co2e_values']):
        st.info("Not enough data for weekly trends. Keep logging!")
        return

    # Insight
    insight = api_get("/coach/insight")
    if insight:
        st.info(insight['insight'])

    # Weekly averages
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Daily Average CO₂e", f"{trend['daily_averages']['co2e_kg']:.2f} kg")
    with col2:
        st.metric("Daily Average Water", f"{trend['daily_averages']['water_l']:.0f} L")

    st.markdown("---")

    # Trend charts
    df = pd.DataFrame({
        "Date": [date.fromisoformat(d) if isinstance(d, str) else d for d in trend['dates']],
        "CO₂e (kg)": trend['co2e_values'],
        "Water (L)": trend['water_values']
    })

    st.subheader("CO₂e Emissions Over Time")
    st.line_chart(df.set_index("Date")["CO₂e (kg)"])

    st.subheader("Water Footprint Over Time")
    st.line_chart(df.set_index("Date")["Water (L)"])

    # Data table
    with st.expander("View Raw Data"):
        st.dataframe(df, use_container_width=True, hide_index=True)

    # Export
    st.markdown("---")
    st.subheader("Export Data")
    if st.button("Download Weekly Data as CSV"):
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"impact_weekly_{date.today().isoformat()}.csv",
            mime="text/csv"
        )


def render_factor_reference_page():
    """Render the factor reference page."""
    st.header("📚 Emission & Product Factors")

    factors = load_factors()
    if not factors:
        st.warning("Could not load factors")
        return

    tabs = st.tabs(["🚗 Mobility", "🛒 Purchases", "🏠 Home Energy"])

    with tabs[0]:
        st.subheader("Mobility Factors")
        if factors.get("mobility"):
            df = pd.DataFrame([
                {
                    "Item": f['item'].replace('_', ' ').title(),
                    "CO₂e/km (kg)": f['co2e_per_unit'],
                    "Water/km (L)": f['water_per_unit'],
                    "Description": f['description']
                }
                for f in factors["mobility"]
            ])
            st.dataframe(df, use_container_width=True, hide_index=True)

    with tabs[1]:
        st.subheader("Purchase Factors")
        if factors.get("purchase"):
            # Group by subcategory
            by_subcat = {}
            for f in factors["purchase"]:
                subcat = f.get('subcategory', 'other')
                if subcat not in by_subcat:
                    by_subcat[subcat] = []
                by_subcat[subcat].append(f)

            for subcat, items in by_subcat.items():
                st.markdown(f"**{subcat.title()}**")
                df = pd.DataFrame([
                    {
                        "Item": f['item'].replace('_', ' ').title(),
                        "CO₂e/unit (kg)": f['co2e_per_unit'],
                        "Water/unit (L)": f['water_per_unit'],
                        "Unit": f['unit'],
                        "Description": f['description']
                    }
                    for f in items
                ])
                st.dataframe(df, use_container_width=True, hide_index=True)

    with tabs[2]:
        st.subheader("Home Energy Factors")
        if factors.get("home_energy"):
            df = pd.DataFrame([
                {
                    "Item": f['item'].replace('_', ' ').title(),
                    "CO₂e/unit (kg)": f['co2e_per_unit'],
                    "Unit": f['unit'],
                    "Description": f['description']
                }
                for f in factors["home_energy"]
            ])
            st.dataframe(df, use_container_width=True, hide_index=True)


# ============================================================================
# Chatbot Page
# ============================================================================

def render_chatbot_page():
    """Render the chatbot interface page."""
    st.header("💬 Impact Coach Chatbot")
    st.markdown("자연어로 오늘의 활동을 입력하세요. 영향을 자동으로 계산합니다!")

    # Initialize chat history in session state
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    # Get suggestions
    suggestions = api_get("/chat/suggestions")

    # Display example suggestions
    with st.expander("💡 Example inputs / 예시 입력"):
        if suggestions:
            cols = st.columns(2)
            for i, suggestion in enumerate(suggestions.get("suggestions", [])):
                with cols[i % 2]:
                    if st.button(suggestion, key=f"sug_{i}"):
                        st.session_state.pending_message = suggestion

    st.markdown("---")

    # Chat container
    chat_container = st.container()

    # Display chat history
    with chat_container:
        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("오늘 뭘 하셨나요? (예: 택시로 5km 이동했어)"):
        # Add user message to history
        st.session_state.chat_messages.append({"role": "user", "content": prompt})

        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)

            # Send to API
            with st.chat_message("assistant"):
                with st.spinner("분석 중..."):
                    result = api_post("/chat", {"message": prompt})

                if result:
                    response = result.get("response", "죄송합니다. 처리 중 오류가 발생했습니다.")
                    st.markdown(response)

                    # Show parsed actions if any
                    if result.get("actions"):
                        with st.expander("📋 Parsed Actions"):
                            for action in result["actions"]:
                                st.write(f"- {action['item']}: {action['amount']} (confidence: {action['confidence']:.0%})")

                    st.session_state.chat_messages.append({"role": "assistant", "content": response})
                else:
                    error_msg = "API 연결 오류. 서버가 실행 중인지 확인하세요."
                    st.error(error_msg)
                    st.session_state.chat_messages.append({"role": "assistant", "content": error_msg})

    # Handle suggestion button clicks
    if "pending_message" in st.session_state:
        pending = st.session_state.pending_message
        del st.session_state.pending_message

        st.session_state.chat_messages.append({"role": "user", "content": pending})

        result = api_post("/chat", {"message": pending})
        if result:
            st.session_state.chat_messages.append({"role": "assistant", "content": result.get("response", "")})

        st.rerun()

    # Clear chat button
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_messages = []
            st.rerun()


# ============================================================================
# Reports Page
# ============================================================================

def render_reports_page():
    """Render the reports generation page."""
    st.header("📄 Impact Reports")
    st.markdown("일일/주간 영향 리포트를 생성하고 다운로드하세요.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Daily Report")
        report_date = st.date_input("Select Date", value=date.today(), key="daily_date")
        daily_format = st.selectbox(
            "Format",
            ["text", "html", "markdown", "json"],
            key="daily_format",
            format_func=lambda x: {
                "text": "📄 Plain Text",
                "html": "🌐 HTML",
                "markdown": "📝 Markdown",
                "json": "🔧 JSON"
            }[x]
        )

        if st.button("Generate Daily Report", type="primary", use_container_width=True):
            with st.spinner("Generating report..."):
                result = api_get("/report/daily", {
                    "target_date": report_date.isoformat(),
                    "format": daily_format
                })

            if result:
                st.success("Report generated!")

                # Display preview
                with st.expander("Preview Report", expanded=True):
                    if daily_format == "html":
                        st.components.v1.html(result["report"], height=600, scrolling=True)
                    elif daily_format == "json":
                        st.json(result["report"])
                    else:
                        st.code(result["report"], language="markdown" if daily_format == "markdown" else None)

                # Download button
                file_ext = {"text": "txt", "html": "html", "markdown": "md", "json": "json"}[daily_format]
                st.download_button(
                    label="📥 Download Report",
                    data=result["report"],
                    file_name=f"impact_report_{report_date.isoformat()}.{file_ext}",
                    mime=result["content_type"]
                )

    with col2:
        st.subheader("Weekly Report")
        end_date = st.date_input("Week Ending", value=date.today(), key="weekly_date")
        weekly_format = st.selectbox(
            "Format",
            ["text", "html", "markdown", "json"],
            key="weekly_format",
            format_func=lambda x: {
                "text": "📄 Plain Text",
                "html": "🌐 HTML",
                "markdown": "📝 Markdown",
                "json": "🔧 JSON"
            }[x]
        )

        if st.button("Generate Weekly Report", type="primary", use_container_width=True):
            with st.spinner("Generating report..."):
                result = api_get("/report/weekly", {
                    "end_date": end_date.isoformat(),
                    "format": weekly_format
                })

            if result:
                st.success(f"Report generated for {result.get('period', 'last 7 days')}!")

                # Display preview
                with st.expander("Preview Report", expanded=True):
                    if weekly_format == "html":
                        st.components.v1.html(result["report"], height=600, scrolling=True)
                    elif weekly_format == "json":
                        st.json(result["report"])
                    else:
                        st.code(result["report"], language="markdown" if weekly_format == "markdown" else None)

                # Download button
                file_ext = {"text": "txt", "html": "html", "markdown": "md", "json": "json"}[weekly_format]
                st.download_button(
                    label="📥 Download Report",
                    data=result["report"],
                    file_name=f"impact_weekly_{end_date.isoformat()}.{file_ext}",
                    mime=result["content_type"]
                )

    st.markdown("---")

    # Quick today's summary
    st.subheader("📊 Quick Summary")
    coaching = api_get("/coach/daily")
    if coaching:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Today's CO₂e", f"{coaching['impact_summary']['total_co2e_kg']:.2f} kg")
        with col2:
            st.metric("Today's Water", f"{coaching['impact_summary']['total_water_l']:.0f} L")
        with col3:
            st.metric("Actions", coaching['impact_summary']['action_count'])


# ============================================================================
# Main Application
# ============================================================================

def main():
    """Main application entry point."""
    # Check API health
    health = api_get("/health")
    if not health:
        st.error("⚠️ Cannot connect to API")
        st.markdown("""
        ### Setup Instructions

        1. Open a new terminal
        2. Navigate to the project directory
        3. Run the API server:
           ```bash
           cd backend
           uvicorn main:app --reload
           ```
        4. Refresh this page
        """)
        return

    # Render sidebar and get selected page
    page = render_sidebar()

    # Render selected page
    if page == "💬 Chatbot":
        render_chatbot_page()
    elif page == "📝 Log Action":
        render_log_action_page()
    elif page == "📊 Dashboard":
        render_dashboard_page()
    elif page == "📈 Weekly Trend":
        render_weekly_trend_page()
    elif page == "📄 Reports":
        render_reports_page()
    elif page == "📚 Factor Reference":
        render_factor_reference_page()


if __name__ == "__main__":
    main()
