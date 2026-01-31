"""Services package for the Daily Action-to-Impact Coach."""

from .impact_engine import (
    calculate_impact,
    get_factor,
    get_all_factors,
    get_category_benchmark,
    compare_to_benchmark,
    FactorNotFoundError,
    clear_factor_cache,
)

from .recommendation import (
    get_recommendations,
    get_default_recommendations,
    generate_daily_summary,
    get_weekly_insight,
    calculate_savings,
)

from .chatbot import (
    parse_message,
    generate_response,
    get_chat_suggestions,
    ChatSession,
    ParsedAction,
)

from .report import (
    generate_text_report,
    generate_html_report,
    generate_markdown_report,
    generate_json_report,
    create_report_data,
    ReportData,
)

__all__ = [
    # Impact Engine
    "calculate_impact",
    "get_factor",
    "get_all_factors",
    "get_category_benchmark",
    "compare_to_benchmark",
    "FactorNotFoundError",
    "clear_factor_cache",
    # Recommendation
    "get_recommendations",
    "get_default_recommendations",
    "generate_daily_summary",
    "get_weekly_insight",
    "calculate_savings",
    # Chatbot
    "parse_message",
    "generate_response",
    "get_chat_suggestions",
    "ChatSession",
    "ParsedAction",
    # Report
    "generate_text_report",
    "generate_html_report",
    "generate_markdown_report",
    "generate_json_report",
    "create_report_data",
    "ReportData",
]
