"""
Daily Action-to-Impact Coach - FastAPI Backend

A minimal MVP for tracking daily environmental impact and receiving
personalized recommendations for reducing carbon footprint.
"""

from datetime import date, timedelta
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from models import (
    ActionLogCreate,
    ActionLogResponse,
    ActionLogBulkCreate,
    ImpactSummary,
    WeeklyTrend,
    DailyCoachResponse,
    Recommendation,
    FactorListResponse,
    HealthCheck,
    ActionCategory,
)
from db import (
    init_database,
    insert_action_log,
    get_actions_by_date,
    get_actions_date_range,
    get_daily_totals,
    get_weekly_totals,
    get_top_contributors,
    get_streak_days,
    delete_action_log,
)
from services import (
    calculate_impact,
    get_all_factors,
    get_recommendations,
    generate_daily_summary,
    get_weekly_insight,
    FactorNotFoundError,
    # Chatbot
    parse_message,
    generate_response,
    get_chat_suggestions,
    # Report
    generate_text_report,
    generate_html_report,
    generate_markdown_report,
    generate_json_report,
    create_report_data,
)


# Initialize FastAPI app
app = FastAPI(
    title="Daily Action-to-Impact Coach",
    description="Track your daily environmental impact and get personalized recommendations",
    version="1.0.0",
)

# CORS middleware for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_database()


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health", response_model=HealthCheck, tags=["System"])
async def health_check():
    """Check API health status."""
    return HealthCheck(
        status="healthy",
        version="1.0.0",
        database="sqlite"
    )


# ============================================================================
# Action Logging Endpoints
# ============================================================================

@app.post("/actions", response_model=ActionLogResponse, tags=["Actions"])
async def create_action(action: ActionLogCreate):
    """
    Log a new action and calculate its environmental impact.

    Categories:
    - **mobility**: Transportation (taxi, bus, subway, car, etc.)
    - **purchase**: Consumption (food, fashion, electronics, etc.)
    - **home_energy**: Energy use (electricity, gas, heating)
    """
    try:
        # Calculate impact
        co2e_kg, water_l = calculate_impact(
            category=action.category.value,
            item=action.item,
            amount=action.amount,
            subcategory=action.subcategory,
            time_of_day=action.time_of_day.value if action.time_of_day else None
        )

        # Insert into database
        action_id = insert_action_log(
            date_val=date.today(),
            category=action.category.value,
            item=action.item,
            amount=action.amount,
            co2e_kg=co2e_kg,
            water_l=water_l,
            subcategory=action.subcategory,
            time_of_day=action.time_of_day.value if action.time_of_day else "standard",
            location=action.location,
            notes=action.notes
        )

        return ActionLogResponse(
            id=action_id,
            date=date.today(),
            category=action.category,
            item=action.item,
            amount=action.amount,
            subcategory=action.subcategory,
            time_of_day=action.time_of_day,
            location=action.location,
            notes=action.notes,
            co2e_kg=co2e_kg,
            water_l=water_l,
            created_at=date.today()
        )

    except FactorNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/actions/bulk", response_model=List[ActionLogResponse], tags=["Actions"])
async def create_actions_bulk(bulk: ActionLogBulkCreate):
    """Log multiple actions at once."""
    results = []
    for action in bulk.actions:
        try:
            result = await create_action(action)
            results.append(result)
        except HTTPException:
            continue  # Skip invalid actions
    return results


@app.get("/actions", response_model=List[ActionLogResponse], tags=["Actions"])
async def get_actions(
    target_date: Optional[date] = Query(None, description="Date to query (defaults to today)"),
    start_date: Optional[date] = Query(None, description="Start of date range"),
    end_date: Optional[date] = Query(None, description="End of date range")
):
    """Get logged actions for a specific date or date range."""
    if start_date and end_date:
        actions = get_actions_date_range(start_date, end_date)
    else:
        query_date = target_date or date.today()
        actions = get_actions_by_date(query_date)

    return [
        ActionLogResponse(
            id=a["id"],
            date=a["date"] if isinstance(a["date"], date) else date.fromisoformat(a["date"]),
            category=ActionCategory(a["category"]),
            item=a["item"],
            amount=a["amount"],
            subcategory=a["subcategory"],
            time_of_day=a["time_of_day"],
            location=a["location"],
            notes=a["notes"],
            co2e_kg=a["co2e_kg"],
            water_l=a["water_l"],
            created_at=a["created_at"]
        )
        for a in actions
    ]


@app.delete("/actions/{action_id}", tags=["Actions"])
async def remove_action(action_id: int):
    """Delete an action log entry."""
    if delete_action_log(action_id):
        return {"message": "Action deleted successfully"}
    raise HTTPException(status_code=404, detail="Action not found")


# ============================================================================
# Impact Summary Endpoints
# ============================================================================

@app.get("/impact/daily", response_model=ImpactSummary, tags=["Impact"])
async def get_daily_impact(target_date: Optional[date] = Query(None)):
    """Get daily impact summary with category breakdown."""
    query_date = target_date or date.today()

    # Get category totals
    category_totals = get_daily_totals(query_date)

    # Calculate overall totals
    total_co2e = sum(c.get("total_co2e", 0) for c in category_totals.values())
    total_water = sum(c.get("total_water", 0) for c in category_totals.values())
    total_actions = sum(c.get("action_count", 0) for c in category_totals.values())

    # Get top contributors
    top = get_top_contributors(query_date, limit=3)

    # Build breakdown with percentages
    breakdown = {}
    for cat, data in category_totals.items():
        cat_co2e = data.get("total_co2e", 0)
        breakdown[cat] = {
            "co2e_kg": cat_co2e,
            "water_l": data.get("total_water", 0),
            "action_count": data.get("action_count", 0),
            "percentage": round((cat_co2e / total_co2e * 100) if total_co2e > 0 else 0, 1)
        }

    return ImpactSummary(
        date=query_date,
        total_co2e_kg=round(total_co2e, 4),
        total_water_l=round(total_water, 2),
        breakdown_by_category=breakdown,
        top_contributors=top,
        action_count=total_actions
    )


@app.get("/impact/weekly", response_model=WeeklyTrend, tags=["Impact"])
async def get_weekly_trend(end_date: Optional[date] = Query(None)):
    """Get weekly trend data for the past 7 days."""
    query_end = end_date or date.today()
    weekly_data = get_weekly_totals(query_end)

    # Fill in missing dates with zeros
    start_date = query_end - timedelta(days=6)
    dates = []
    co2e_values = []
    water_values = []

    data_by_date = {
        (d["date"] if isinstance(d["date"], date) else date.fromisoformat(d["date"])): d
        for d in weekly_data
    }

    for i in range(7):
        d = start_date + timedelta(days=i)
        dates.append(d)
        if d in data_by_date:
            co2e_values.append(round(data_by_date[d].get("total_co2e", 0), 4))
            water_values.append(round(data_by_date[d].get("total_water", 0), 2))
        else:
            co2e_values.append(0)
            water_values.append(0)

    # Calculate averages (excluding zero days)
    non_zero_co2e = [v for v in co2e_values if v > 0]
    non_zero_water = [v for v in water_values if v > 0]

    return WeeklyTrend(
        dates=dates,
        co2e_values=co2e_values,
        water_values=water_values,
        daily_averages={
            "co2e_kg": round(sum(non_zero_co2e) / len(non_zero_co2e), 2) if non_zero_co2e else 0,
            "water_l": round(sum(non_zero_water) / len(non_zero_water), 2) if non_zero_water else 0
        }
    )


# ============================================================================
# Coaching Endpoints
# ============================================================================

@app.get("/coach/daily", response_model=DailyCoachResponse, tags=["Coaching"])
async def get_daily_coaching(target_date: Optional[date] = Query(None)):
    """Get complete daily coaching response with summary and recommendations."""
    query_date = target_date or date.today()

    # Get today's actions
    actions = get_actions_by_date(query_date)

    # Get impact summary
    impact = await get_daily_impact(query_date)

    # Get recommendations based on actions
    recommendations = get_recommendations(actions, max_recommendations=3)

    # Generate summary
    summary = generate_daily_summary(
        total_co2e_kg=impact.total_co2e_kg,
        total_water_l=impact.total_water_l,
        top_contributors=impact.top_contributors
    )

    # Get streak
    streak = get_streak_days()

    return DailyCoachResponse(
        date=query_date,
        summary=summary,
        impact_summary=impact,
        recommendations=[
            Recommendation(
                priority=r["priority"],
                category=ActionCategory(r["category"]),
                action=r["action"],
                rationale=r["rationale"],
                estimated_savings_co2e_kg=r["estimated_savings_co2e_kg"],
                estimated_savings_water_l=r["estimated_savings_water_l"],
                difficulty=r["difficulty"]
            )
            for r in recommendations
        ],
        streak_days=streak
    )


@app.get("/coach/insight", tags=["Coaching"])
async def get_weekly_coaching_insight():
    """Get weekly insight message."""
    weekly_data = get_weekly_totals(date.today())
    insight = get_weekly_insight(weekly_data)
    return {"insight": insight}


# ============================================================================
# Factor Reference Endpoints
# ============================================================================

@app.get("/factors", response_model=FactorListResponse, tags=["Reference"])
async def list_factors():
    """Get all available emission and product factors."""
    factors = get_all_factors()
    return FactorListResponse(
        mobility=factors["mobility"],
        purchase=factors["purchase"],
        home_energy=factors["home_energy"]
    )


@app.get("/factors/{category}", tags=["Reference"])
async def list_factors_by_category(category: ActionCategory):
    """Get factors for a specific category."""
    factors = get_all_factors()
    return factors.get(category.value, [])


# ============================================================================
# Chatbot Endpoints
# ============================================================================

@app.post("/chat", tags=["Chatbot"])
async def chat_message(message: dict):
    """
    Process a natural language message and return impact analysis.

    Example messages:
    - "오늘 택시로 5km 이동했어"
    - "점심에 소고기 먹었어"
    - "커피 3잔 마셨어"
    """
    user_message = message.get("message", "")
    if not user_message:
        return {"response": "메시지를 입력해주세요.", "actions": [], "impacts": []}

    # Parse the message
    parsed_actions = parse_message(user_message)

    # Calculate impacts for each parsed action
    impacts = []
    saved_actions = []

    for action in parsed_actions:
        try:
            co2e_kg, water_l = calculate_impact(
                category=action.category,
                item=action.item,
                amount=action.amount
            )

            # Save to database
            action_id = insert_action_log(
                date_val=date.today(),
                category=action.category,
                item=action.item,
                amount=action.amount,
                co2e_kg=co2e_kg,
                water_l=water_l
            )

            impacts.append({
                "id": action_id,
                "item": action.item,
                "amount": action.amount,
                "co2e_kg": co2e_kg,
                "water_l": water_l
            })

            saved_actions.append({
                "category": action.category,
                "item": action.item,
                "amount": action.amount,
                "confidence": action.confidence
            })

        except FactorNotFoundError:
            continue

    # Generate response
    response = generate_response(parsed_actions, impacts)

    return {
        "response": response,
        "actions": saved_actions,
        "impacts": impacts
    }


@app.get("/chat/suggestions", tags=["Chatbot"])
async def get_suggestions():
    """Get example chat suggestions for the user."""
    return {"suggestions": get_chat_suggestions()}


# ============================================================================
# Report Generation Endpoints
# ============================================================================

@app.get("/report/daily", tags=["Reports"])
async def get_daily_report(
    target_date: Optional[date] = Query(None),
    format: str = Query("text", description="Report format: text, html, markdown, json")
):
    """Generate a daily impact report in various formats."""
    query_date = target_date or date.today()

    # Get data
    daily_totals = get_daily_totals(query_date)
    top_contributors = get_top_contributors(query_date, limit=5)
    actions = get_actions_by_date(query_date)
    recommendations = get_recommendations(actions, max_recommendations=3)
    streak = get_streak_days()

    # Create report data
    report_data = create_report_data(
        target_date=query_date,
        period="daily",
        daily_totals=daily_totals,
        top_contributors=top_contributors,
        recommendations=recommendations,
        streak_days=streak
    )

    # Generate report in requested format
    if format == "html":
        content = generate_html_report(report_data)
        content_type = "text/html"
    elif format == "markdown":
        content = generate_markdown_report(report_data)
        content_type = "text/markdown"
    elif format == "json":
        content = generate_json_report(report_data)
        content_type = "application/json"
    else:  # text
        content = generate_text_report(report_data)
        content_type = "text/plain"

    return {
        "format": format,
        "content_type": content_type,
        "report": content,
        "date": query_date.isoformat()
    }


@app.get("/report/weekly", tags=["Reports"])
async def get_weekly_report(
    end_date: Optional[date] = Query(None),
    format: str = Query("text", description="Report format: text, html, markdown, json")
):
    """Generate a weekly impact report."""
    query_end = end_date or date.today()
    query_start = query_end - timedelta(days=6)

    # Aggregate weekly data
    weekly_data = get_weekly_totals(query_end)

    # Get all actions for the week
    all_actions = get_actions_date_range(query_start, query_end)

    # Calculate totals
    total_co2e = sum(d.get("total_co2e", 0) for d in weekly_data)
    total_water = sum(d.get("total_water", 0) for d in weekly_data)
    total_actions = sum(d.get("action_count", 0) for d in weekly_data)

    # Group by category
    category_totals = {}
    for action in all_actions:
        cat = action["category"]
        if cat not in category_totals:
            category_totals[cat] = {"total_co2e": 0, "total_water": 0, "action_count": 0}
        category_totals[cat]["total_co2e"] += action.get("co2e_kg", 0)
        category_totals[cat]["total_water"] += action.get("water_l", 0)
        category_totals[cat]["action_count"] += 1

    # Get recommendations
    recommendations = get_recommendations(all_actions, max_recommendations=3)

    # Get top contributors (sort by co2e)
    sorted_actions = sorted(all_actions, key=lambda x: x.get("co2e_kg", 0), reverse=True)
    top_contributors = sorted_actions[:5]

    # Create report data
    report_data = create_report_data(
        target_date=query_end,
        period="weekly",
        daily_totals=category_totals,
        top_contributors=top_contributors,
        recommendations=recommendations,
        streak_days=get_streak_days()
    )

    # Generate report in requested format
    if format == "html":
        content = generate_html_report(report_data)
        content_type = "text/html"
    elif format == "markdown":
        content = generate_markdown_report(report_data)
        content_type = "text/markdown"
    elif format == "json":
        content = generate_json_report(report_data)
        content_type = "application/json"
    else:
        content = generate_text_report(report_data)
        content_type = "text/plain"

    return {
        "format": format,
        "content_type": content_type,
        "report": content,
        "period": f"{query_start.isoformat()} to {query_end.isoformat()}"
    }


# ============================================================================
# Main entry point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
