"""
Tests for the Impact Engine module.

Run with: pytest tests/test_impact_engine.py -v
"""

import pytest
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from services.impact_engine import (
    calculate_impact,
    get_factor,
    get_all_factors,
    load_emission_factors,
    load_product_factors,
    get_category_benchmark,
    compare_to_benchmark,
    FactorNotFoundError,
    clear_factor_cache,
)


class TestFactorLoading:
    """Tests for factor loading functionality."""

    def test_load_emission_factors(self):
        """Test that emission factors load correctly."""
        clear_factor_cache()
        factors = load_emission_factors()

        assert factors is not None
        assert "mobility" in factors
        assert "home_energy" in factors
        assert "metadata" in factors

    def test_load_product_factors(self):
        """Test that product factors load correctly."""
        clear_factor_cache()
        factors = load_product_factors()

        assert factors is not None
        assert "purchase" in factors
        assert "metadata" in factors

    def test_emission_factors_have_required_items(self):
        """Test that key emission factors exist."""
        factors = load_emission_factors()

        mobility = factors["mobility"]
        assert "taxi_ice" in mobility
        assert "taxi_ev" in mobility
        assert "bus" in mobility
        assert "subway" in mobility

        energy = factors["home_energy"]
        assert "electricity_kwh" in energy

    def test_product_factors_have_required_items(self):
        """Test that key product factors exist."""
        factors = load_product_factors()

        purchase = factors["purchase"]
        assert "food" in purchase
        assert "fashion" in purchase

        assert "beef_meal" in purchase["food"]
        assert "tshirt_fastfashion" in purchase["fashion"]


class TestGetFactor:
    """Tests for the get_factor function."""

    def test_get_mobility_factor(self):
        """Test getting a mobility factor."""
        factor = get_factor("mobility", "taxi_ice")

        assert factor["co2e_per_unit"] == 0.21
        assert factor["unit"] == "km"
        assert "description" in factor

    def test_get_home_energy_factor(self):
        """Test getting a home energy factor."""
        factor = get_factor("home_energy", "electricity_kwh")

        assert factor["co2e_per_unit"] == 0.459
        assert factor["unit"] == "kWh"

    def test_get_purchase_factor_with_subcategory(self):
        """Test getting a purchase factor with subcategory."""
        factor = get_factor("purchase", "beef_meal", subcategory="food")

        assert factor["co2e_per_unit"] == 6.5
        assert factor["water_per_unit"] == 1850

    def test_get_purchase_factor_without_subcategory(self):
        """Test getting a purchase factor without specifying subcategory."""
        factor = get_factor("purchase", "tshirt_fastfashion")

        assert factor["co2e_per_unit"] == 5.5
        assert factor["water_per_unit"] == 2700

    def test_factor_not_found_raises_error(self):
        """Test that missing factors raise FactorNotFoundError."""
        with pytest.raises(FactorNotFoundError):
            get_factor("mobility", "nonexistent_item")

    def test_factor_case_insensitive(self):
        """Test that factor lookup is case-insensitive."""
        factor1 = get_factor("mobility", "taxi_ice")
        factor2 = get_factor("mobility", "TAXI_ICE")
        factor3 = get_factor("mobility", "Taxi_Ice")

        assert factor1["co2e_per_unit"] == factor2["co2e_per_unit"]
        assert factor1["co2e_per_unit"] == factor3["co2e_per_unit"]


class TestCalculateImpact:
    """Tests for the calculate_impact function."""

    def test_calculate_taxi_impact(self):
        """Test calculating impact for taxi ride."""
        co2e, water = calculate_impact("mobility", "taxi_ice", 10)

        assert co2e == pytest.approx(2.1, rel=0.01)
        assert water == pytest.approx(5.0, rel=0.01)

    def test_calculate_ev_taxi_impact(self):
        """Test that EV taxi has lower impact than ICE taxi."""
        co2e_ice, _ = calculate_impact("mobility", "taxi_ice", 10)
        co2e_ev, _ = calculate_impact("mobility", "taxi_ev", 10)

        assert co2e_ev < co2e_ice
        assert co2e_ev == pytest.approx(0.5, rel=0.01)

    def test_calculate_beef_impact(self):
        """Test calculating impact for beef meal."""
        co2e, water = calculate_impact("purchase", "beef_meal", 2)

        assert co2e == pytest.approx(13.0, rel=0.01)
        assert water == pytest.approx(3700, rel=0.01)

    def test_calculate_electricity_impact(self):
        """Test calculating impact for electricity usage."""
        co2e, water = calculate_impact("home_energy", "electricity_kwh", 10)

        assert co2e == pytest.approx(4.59, rel=0.01)
        assert water == 0  # No water for energy

    def test_peak_electricity_higher_impact(self):
        """Test that peak electricity has higher carbon intensity."""
        co2e_standard, _ = calculate_impact("home_energy", "electricity_kwh", 10)
        co2e_peak, _ = calculate_impact(
            "home_energy", "electricity_kwh", 10, time_of_day="peak"
        )

        assert co2e_peak > co2e_standard

    def test_off_peak_electricity_lower_impact(self):
        """Test that off-peak electricity has lower carbon intensity."""
        co2e_standard, _ = calculate_impact("home_energy", "electricity_kwh", 10)
        co2e_offpeak, _ = calculate_impact(
            "home_energy", "electricity_kwh", 10, time_of_day="off_peak"
        )

        assert co2e_offpeak < co2e_standard

    def test_zero_emission_modes(self):
        """Test that walking and cycling have zero emissions."""
        co2e_walk, water_walk = calculate_impact("mobility", "walking", 5)
        co2e_bike, water_bike = calculate_impact("mobility", "bicycle", 5)

        assert co2e_walk == 0
        assert co2e_bike == 0
        assert water_walk == 0
        assert water_bike == 0


class TestGetAllFactors:
    """Tests for the get_all_factors function."""

    def test_returns_all_categories(self):
        """Test that all categories are returned."""
        factors = get_all_factors()

        assert "mobility" in factors
        assert "purchase" in factors
        assert "home_energy" in factors

    def test_factors_have_required_fields(self):
        """Test that factors have all required fields."""
        factors = get_all_factors()

        for category in ["mobility", "purchase", "home_energy"]:
            for factor in factors[category]:
                assert "item" in factor
                assert "category" in factor
                assert "co2e_per_unit" in factor
                assert "description" in factor
                assert "unit" in factor

    def test_mobility_has_minimum_items(self):
        """Test that mobility has a minimum number of items."""
        factors = get_all_factors()
        assert len(factors["mobility"]) >= 8

    def test_purchase_has_minimum_items(self):
        """Test that purchase has a minimum number of items."""
        factors = get_all_factors()
        assert len(factors["purchase"]) >= 10


class TestBenchmarks:
    """Tests for benchmark comparison functionality."""

    def test_get_category_benchmark(self):
        """Test getting category benchmarks."""
        mobility = get_category_benchmark("mobility")
        purchase = get_category_benchmark("purchase")
        energy = get_category_benchmark("home_energy")

        assert mobility["avg_daily_co2e_kg"] > 0
        assert purchase["avg_daily_co2e_kg"] > 0
        assert energy["avg_daily_co2e_kg"] > 0

    def test_compare_to_benchmark_above(self):
        """Test comparison when above benchmark."""
        # Assume mobility benchmark is 3.5 kg CO2e
        result = compare_to_benchmark("mobility", 5.0, 10.0)

        assert result["co2e_vs_avg_percent"] > 0  # Above average

    def test_compare_to_benchmark_below(self):
        """Test comparison when below benchmark."""
        result = compare_to_benchmark("mobility", 1.0, 2.0)

        assert result["co2e_vs_avg_percent"] < 0  # Below average


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_invalid_category(self):
        """Test that invalid category raises error."""
        with pytest.raises(FactorNotFoundError):
            get_factor("invalid_category", "some_item")

    def test_whitespace_in_item(self):
        """Test that whitespace is handled correctly."""
        factor = get_factor("mobility", "  taxi_ice  ")
        assert factor["co2e_per_unit"] == 0.21

    def test_small_amounts(self):
        """Test calculation with small amounts."""
        co2e, water = calculate_impact("mobility", "taxi_ice", 0.1)

        assert co2e == pytest.approx(0.021, rel=0.01)
        assert water == pytest.approx(0.05, rel=0.01)

    def test_large_amounts(self):
        """Test calculation with large amounts."""
        co2e, water = calculate_impact("mobility", "taxi_ice", 1000)

        assert co2e == pytest.approx(210, rel=0.01)
        assert water == pytest.approx(500, rel=0.01)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
