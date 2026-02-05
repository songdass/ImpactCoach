"""
Report Generator Service

Generates formatted reports (text, HTML, PDF-ready) for daily and weekly impacts.
"""

from datetime import date, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
import json


@dataclass
class ReportData:
    """Data structure for report generation."""
    report_date: date
    period: str  # "daily" or "weekly"
    total_co2e_kg: float
    total_water_l: float
    action_count: int
    breakdown_by_category: Dict[str, Dict]
    top_contributors: List[Dict]
    recommendations: List[Dict]
    comparison: Optional[Dict] = None
    streak_days: int = 0


def generate_text_report(data: ReportData) -> str:
    """Generate a plain text report."""
    lines = []

    # Header
    lines.append("=" * 60)
    lines.append(f"🌱 Daily Impact Coach - {data.period.title()} Report")
    lines.append(f"📅 Date: {data.report_date.isoformat()}")
    lines.append("=" * 60)
    lines.append("")

    # Summary
    lines.append("📊 IMPACT SUMMARY")
    lines.append("-" * 40)
    lines.append(f"Total CO₂e Emissions: {data.total_co2e_kg:.3f} kg")
    lines.append(f"Total Water Footprint: {data.total_water_l:.1f} L")
    lines.append(f"Actions Logged: {data.action_count}")
    if data.streak_days > 0:
        lines.append(f"Current Streak: {data.streak_days} days 🔥")
    lines.append("")

    # Category Breakdown
    if data.breakdown_by_category:
        lines.append("📈 BREAKDOWN BY CATEGORY")
        lines.append("-" * 40)
        for category, values in data.breakdown_by_category.items():
            emoji = {"mobility": "🚗", "purchase": "🛒", "home_energy": "🏠"}.get(category, "📌")
            lines.append(f"{emoji} {category.replace('_', ' ').title()}:")
            lines.append(f"   CO₂e: {values.get('co2e_kg', 0):.3f} kg ({values.get('percentage', 0):.1f}%)")
            if values.get('water_l', 0) > 0:
                lines.append(f"   Water: {values.get('water_l', 0):.1f} L")
        lines.append("")

    # Top Contributors
    if data.top_contributors:
        lines.append("🏆 TOP IMPACT CONTRIBUTORS")
        lines.append("-" * 40)
        for i, contrib in enumerate(data.top_contributors[:5], 1):
            lines.append(f"{i}. {contrib['item'].replace('_', ' ').title()}")
            lines.append(f"   Amount: {contrib['amount']} | CO₂e: {contrib['co2e_kg']:.3f} kg")
        lines.append("")

    # Recommendations
    if data.recommendations:
        lines.append("🎯 RECOMMENDED ACTIONS")
        lines.append("-" * 40)
        for i, rec in enumerate(data.recommendations[:3], 1):
            difficulty = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}.get(rec.get('difficulty', 'medium'), "⚪")
            lines.append(f"{i}. {rec['action']}")
            lines.append(f"   {difficulty} {rec.get('difficulty', 'medium').title()} | Saves: {rec.get('estimated_savings_co2e_kg', 0):.2f} kg CO₂e")
            lines.append(f"   {rec.get('rationale', '')}")
        lines.append("")

    # Comparison (if available)
    if data.comparison:
        lines.append("📉 COMPARISON")
        lines.append("-" * 40)
        if 'vs_yesterday' in data.comparison:
            change = data.comparison['vs_yesterday']
            direction = "↑" if change > 0 else "↓" if change < 0 else "→"
            lines.append(f"vs Yesterday: {direction} {abs(change):.1f}%")
        if 'vs_weekly_avg' in data.comparison:
            change = data.comparison['vs_weekly_avg']
            direction = "↑" if change > 0 else "↓" if change < 0 else "→"
            lines.append(f"vs Weekly Avg: {direction} {abs(change):.1f}%")
        lines.append("")

    # Footer
    lines.append("=" * 60)
    lines.append("🌍 Every action counts! Keep making sustainable choices.")
    lines.append("=" * 60)

    return "\n".join(lines)


def generate_html_report(data: ReportData) -> str:
    """Generate an HTML report suitable for email or web display."""
    html = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily Impact Report - {data.report_date.isoformat()}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background: white;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 2px solid #22c55e;
            padding-bottom: 16px;
            margin-bottom: 24px;
        }}
        .header h1 {{
            color: #22c55e;
            margin: 0;
            font-size: 24px;
        }}
        .header .date {{
            color: #666;
            font-size: 14px;
            margin-top: 8px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }}
        .metric {{
            text-align: center;
            padding: 16px;
            background: #f0fdf4;
            border-radius: 8px;
        }}
        .metric-value {{
            font-size: 24px;
            font-weight: bold;
            color: #16a34a;
        }}
        .metric-label {{
            font-size: 12px;
            color: #666;
            margin-top: 4px;
        }}
        .section {{
            margin-bottom: 24px;
        }}
        .section h2 {{
            font-size: 16px;
            color: #333;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .category-bar {{
            display: flex;
            align-items: center;
            margin-bottom: 8px;
        }}
        .category-name {{
            width: 120px;
            font-size: 14px;
        }}
        .category-bar-fill {{
            height: 20px;
            background: linear-gradient(90deg, #22c55e, #16a34a);
            border-radius: 4px;
            min-width: 4px;
        }}
        .category-value {{
            margin-left: 8px;
            font-size: 12px;
            color: #666;
        }}
        .recommendation {{
            background: #f8fafc;
            border-left: 4px solid #22c55e;
            padding: 12px;
            margin-bottom: 8px;
            border-radius: 0 8px 8px 0;
        }}
        .recommendation-title {{
            font-weight: 600;
            color: #333;
        }}
        .recommendation-detail {{
            font-size: 13px;
            color: #666;
            margin-top: 4px;
        }}
        .footer {{
            text-align: center;
            padding-top: 16px;
            border-top: 1px solid #eee;
            color: #666;
            font-size: 12px;
        }}
        .streak {{
            display: inline-block;
            background: #fef3c7;
            color: #d97706;
            padding: 4px 12px;
            border-radius: 16px;
            font-size: 14px;
            margin-top: 8px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌱 Daily Impact Report</h1>
            <div class="date">{data.report_date.strftime('%Y년 %m월 %d일')}</div>
            {"<div class='streak'>🔥 " + str(data.streak_days) + " days streak!</div>" if data.streak_days > 1 else ""}
        </div>

        <div class="summary">
            <div class="metric">
                <div class="metric-value">{data.total_co2e_kg:.2f}</div>
                <div class="metric-label">kg CO₂e</div>
            </div>
            <div class="metric">
                <div class="metric-value">{data.total_water_l:.0f}</div>
                <div class="metric-label">L Water</div>
            </div>
            <div class="metric">
                <div class="metric-value">{data.action_count}</div>
                <div class="metric-label">Actions</div>
            </div>
        </div>
"""

    # Category breakdown
    if data.breakdown_by_category:
        max_co2e = max((v.get('co2e_kg', 0) for v in data.breakdown_by_category.values()), default=1) or 1
        html += """
        <div class="section">
            <h2>📊 Impact by Category</h2>
"""
        for category, values in data.breakdown_by_category.items():
            emoji = {"mobility": "🚗", "purchase": "🛒", "home_energy": "🏠"}.get(category, "📌")
            bar_width = (values.get('co2e_kg', 0) / max_co2e) * 100
            html += f"""
            <div class="category-bar">
                <span class="category-name">{emoji} {category.replace('_', ' ').title()}</span>
                <div class="category-bar-fill" style="width: {bar_width}%"></div>
                <span class="category-value">{values.get('co2e_kg', 0):.2f} kg ({values.get('percentage', 0):.0f}%)</span>
            </div>
"""
        html += "</div>"

    # Recommendations
    if data.recommendations:
        html += """
        <div class="section">
            <h2>🎯 Recommended Actions</h2>
"""
        for rec in data.recommendations[:3]:
            difficulty = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}.get(rec.get('difficulty', 'medium'), "⚪")
            html += f"""
            <div class="recommendation">
                <div class="recommendation-title">{difficulty} {rec['action']}</div>
                <div class="recommendation-detail">
                    Potential savings: {rec.get('estimated_savings_co2e_kg', 0):.2f} kg CO₂e
                </div>
            </div>
"""
        html += "</div>"

    html += """
        <div class="footer">
            🌍 Every action counts! Keep making sustainable choices.<br>
            Generated by Daily Impact Coach
        </div>
    </div>
</body>
</html>
"""
    return html


def generate_markdown_report(data: ReportData) -> str:
    """Generate a Markdown report."""
    lines = []

    lines.append(f"# 🌱 Daily Impact Report")
    lines.append(f"**Date:** {data.report_date.isoformat()}")
    lines.append("")

    # Summary table
    lines.append("## 📊 Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total CO₂e | {data.total_co2e_kg:.3f} kg |")
    lines.append(f"| Total Water | {data.total_water_l:.1f} L |")
    lines.append(f"| Actions | {data.action_count} |")
    if data.streak_days > 0:
        lines.append(f"| Streak | {data.streak_days} days 🔥 |")
    lines.append("")

    # Category breakdown
    if data.breakdown_by_category:
        lines.append("## 📈 By Category")
        lines.append("")
        lines.append("| Category | CO₂e (kg) | % | Water (L) |")
        lines.append("|----------|-----------|---|-----------|")
        for category, values in data.breakdown_by_category.items():
            lines.append(
                f"| {category.replace('_', ' ').title()} | "
                f"{values.get('co2e_kg', 0):.3f} | "
                f"{values.get('percentage', 0):.1f}% | "
                f"{values.get('water_l', 0):.1f} |"
            )
        lines.append("")

    # Top contributors
    if data.top_contributors:
        lines.append("## 🏆 Top Contributors")
        lines.append("")
        for i, contrib in enumerate(data.top_contributors[:5], 1):
            lines.append(
                f"{i}. **{contrib['item'].replace('_', ' ').title()}** - "
                f"{contrib['amount']} units → {contrib['co2e_kg']:.3f} kg CO₂e"
            )
        lines.append("")

    # Recommendations
    if data.recommendations:
        lines.append("## 🎯 Recommendations")
        lines.append("")
        for rec in data.recommendations[:3]:
            difficulty = {"easy": "🟢 Easy", "medium": "🟡 Medium", "hard": "🔴 Hard"}.get(
                rec.get('difficulty', 'medium'), "⚪"
            )
            lines.append(f"### {rec['action']}")
            lines.append(f"- **Difficulty:** {difficulty}")
            lines.append(f"- **Potential Savings:** {rec.get('estimated_savings_co2e_kg', 0):.2f} kg CO₂e")
            lines.append(f"- {rec.get('rationale', '')}")
            lines.append("")

    lines.append("---")
    lines.append("*Generated by Daily Impact Coach* 🌍")

    return "\n".join(lines)


def generate_json_report(data: ReportData) -> str:
    """Generate a JSON report for API consumption."""
    report = {
        "report_date": data.report_date.isoformat(),
        "period": data.period,
        "generated_at": date.today().isoformat(),
        "summary": {
            "total_co2e_kg": round(data.total_co2e_kg, 3),
            "total_water_l": round(data.total_water_l, 1),
            "action_count": data.action_count,
            "streak_days": data.streak_days
        },
        "breakdown_by_category": data.breakdown_by_category,
        "top_contributors": data.top_contributors,
        "recommendations": data.recommendations,
        "comparison": data.comparison
    }
    return json.dumps(report, indent=2, ensure_ascii=False)


def create_report_data(
    target_date: date,
    period: str,
    daily_totals: Dict,
    top_contributors: List[Dict],
    recommendations: List[Dict],
    streak_days: int = 0,
    comparison: Optional[Dict] = None
) -> ReportData:
    """Create ReportData from raw data."""
    total_co2e = sum(cat.get('total_co2e', 0) for cat in daily_totals.values())
    total_water = sum(cat.get('total_water', 0) for cat in daily_totals.values())
    action_count = sum(cat.get('action_count', 0) for cat in daily_totals.values())

    breakdown = {}
    for category, values in daily_totals.items():
        co2e = values.get('total_co2e', 0)
        breakdown[category] = {
            "co2e_kg": co2e,
            "water_l": values.get('total_water', 0),
            "action_count": values.get('action_count', 0),
            "percentage": (co2e / total_co2e * 100) if total_co2e > 0 else 0
        }

    return ReportData(
        report_date=target_date,
        period=period,
        total_co2e_kg=total_co2e,
        total_water_l=total_water,
        action_count=action_count,
        breakdown_by_category=breakdown,
        top_contributors=top_contributors,
        recommendations=recommendations,
        streak_days=streak_days,
        comparison=comparison
    )
