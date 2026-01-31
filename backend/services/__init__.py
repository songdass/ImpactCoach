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

__all__ = [
    "calculate_impact",
    "get_factor",
    "get_all_factors",
    "get_category_benchmark",
    "compare_to_benchmark",
    "FactorNotFoundError",
    "clear_factor_cache",
    "get_recommendations",
    "get_default_recommendations",
    "generate_daily_summary",
    "get_weekly_insight",
    "calculate_savings",
]
