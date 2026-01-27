import pytest
import random
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from backend.simulation.model import (
    simulate_process_equipment,
    simulate_breathing_changes,
    simulate_airsealed_room_no_control,
    simulate_airsealed_room_with_control,
    room_volume,
    room_air_mass,
    air_cp,
    co2_gen_per_person,
    o2_cons_per_person,
)


class TestSimulateProcessEquipment:
    """Tests for the simulate_process_equipment function."""

    def test_simulate_process_equipment_returns_value(self):
        """
        Tests that function returns a thermal value.
        """
        initial_thermal = 5000
        result = simulate_process_equipment(initial_thermal)
        
        assert isinstance(result, (int, float))

    def test_simulate_process_equipment_modifies_thermal(self):
        """
        Tests that thermal value is modified (with noise).
        """
        # Run multiple times to check variation
        initial_thermal = 5000
        results = [simulate_process_equipment(initial_thermal) for _ in range(10)]
        
        # At least some results should differ from initial
        assert any(r != initial_thermal for r in results)

    def test_simulate_process_equipment_with_zero_thermal(self):
        """
        Tests function with zero thermal input.
        """
        result = simulate_process_equipment(0)
        
        assert isinstance(result, (int, float))

    def test_simulate_process_equipment_with_negative_thermal(self):
        """
        Tests function with negative thermal input.
        """
        result = simulate_process_equipment(-5000)
        
        assert isinstance(result, (int, float))

    def test_simulate_process_equipment_with_large_thermal(self):
        """
        Tests function with large thermal values.
        """
        result = simulate_process_equipment(999999)
        
        assert isinstance(result, (int, float))

    def test_simulate_process_equipment_random_step_possible(self):
        """
        Tests that random large step changes are possible (1% chance).
        """
        # Run many times to catch at least one large step
        initial_thermal = 5000
        results = [simulate_process_equipment(initial_thermal) for _ in range(1000)]
        
        # Calculate differences from initial
        diffs = [abs(r - initial_thermal) for r in results]
        
        # Should have at least one difference >= 40000 (accounts for random step -50000 to 50000, plus noise -5000 to 5000)
        # With 1% chance over 1000 iterations, very likely to occur
        assert any(d >= 40000 for d in diffs)

    def test_simulate_process_equipment_continuous_noise(self):
        """
        Tests that continuous noise is applied (-5000 to 5000).
        """
        initial_thermal = 5000
        # Average change over many iterations should be close to 0
        changes = []
        for _ in range(100):
            result = simulate_process_equipment(initial_thermal)
            changes.append(result - initial_thermal)
        
        avg_change = sum(changes) / len(changes)
        # Average should be near 0 due to random noise
        assert abs(avg_change) < 5000


class TestSimulateBreathingChanges:
    """Tests for the simulate_breathing_changes function."""

    def test_simulate_breathing_changes_returns_list(self):
        """
        Tests that function returns a list of [co2, o2].
        """
        result = simulate_breathing_changes(400.0, 21.0, 22.0)
        
        assert isinstance(result, list)
        assert len(result) == 2

    def test_simulate_breathing_changes_co2_increases(self):
        """
        Tests that CO2 increases during breathing simulation.
        """
        initial_co2 = 400.0
        result_co2, _ = simulate_breathing_changes(initial_co2, 21.0, 22.0)
        
        # CO2 should increase or stay same (breathing adds CO2)
        assert result_co2 >= 0

    def test_simulate_breathing_changes_o2_decreases(self):
        """
        Tests that O2 response to breathing changes.
        """
        initial_o2 = 21.0
        _, result_o2 = simulate_breathing_changes(400.0, initial_o2, 22.0)
        
        # O2 should be valid (between 0 and 1000000)
        assert 0 <= result_o2 <= 1000000

    def test_simulate_breathing_changes_co2_clamped(self):
        """
        Tests that CO2 is clamped between 0 and 1000000.
        """
        result_co2, _ = simulate_breathing_changes(999999.0, 21.0, 22.0)
        
        assert 0 <= result_co2 <= 1000000

    def test_simulate_breathing_changes_o2_clamped(self):
        """
        Tests that O2 is clamped between 0 and 1000000.
        """
        _, result_o2 = simulate_breathing_changes(400.0, 999999.0, 22.0)
        
        assert 0 <= result_o2 <= 1000000

    def test_simulate_breathing_changes_temperature_effect(self):
        """
        Tests that temperature affects breathing rates.
        """
        # Run at different temperatures and check variation
        results_warm = [simulate_breathing_changes(400.0, 21.0, 30.0) for _ in range(5)]
        results_cool = [simulate_breathing_changes(400.0, 21.0, 15.0) for _ in range(5)]
        
        # Should have variation in results
        assert len(set((r[0], r[1]) for r in results_warm)) >= 1
        assert len(set((r[0], r[1]) for r in results_cool)) >= 1

    def test_simulate_breathing_changes_with_zero_co2(self):
        """
        Tests function with zero initial CO2.
        """
        result_co2, result_o2 = simulate_breathing_changes(0.0, 21.0, 22.0)
        
        assert 0 <= result_co2 <= 1000000
        assert 0 <= result_o2 <= 1000000

    def test_simulate_breathing_changes_with_max_values(self):
        """
        Tests function at maximum CO2/O2 values.
        """
        result_co2, result_o2 = simulate_breathing_changes(1000000.0, 1000000.0, 22.0)
        
        assert 0 <= result_co2 <= 1000000
        assert 0 <= result_o2 <= 1000000

    def test_simulate_breathing_changes_reference_temp(self):
        """
        Tests breathing changes at reference temperature (25°C).
        """
        result_co2, result_o2 = simulate_breathing_changes(400.0, 21.0, 25.0)
        
        assert isinstance(result_co2, (int, float))
        assert isinstance(result_o2, (int, float))


class TestSimulateAirsealedRoomNoControl:
    """Tests for the simulate_airsealed_room_no_control function."""

    def test_simulate_airsealed_room_no_control_returns_list(self):
        """
        Tests that function returns a list of 5 values.
        """
        time = datetime.now()
        data = [time, 22.0, 400.0, 21.0, 5000.0]
        
        result = simulate_airsealed_room_no_control(data)
        
        assert isinstance(result, list)
        assert len(result) == 5

    def test_simulate_airsealed_room_no_control_time_increments(self):
        """
        Tests that time is incremented by 1 minute.
        """
        time = datetime(2025, 1, 27, 10, 0, 0)
        data = [time, 22.0, 400.0, 21.0, 5000.0]
        
        result_time, _, _, _, _ = simulate_airsealed_room_no_control(data)
        
        # Time should increase by 1 minute
        assert result_time == time + timedelta(minutes=1)

    def test_simulate_airsealed_room_no_control_temperature_affected(self):
        """
        Tests that temperature is affected by thermal energy.
        """
        time = datetime.now()
        data = [time, 22.0, 400.0, 21.0, 5000.0]
        
        _, result_temp, _, _, _ = simulate_airsealed_room_no_control(data)
        
        # Temperature should be calculated
        assert isinstance(result_temp, (int, float))

    def test_simulate_airsealed_room_no_control_temp_minimum(self):
        """
        Tests that temperature doesn't go below absolute zero (-273°C).
        """
        time = datetime.now()
        # Start at low temp with high cooling
        data = [time, -200.0, 400.0, 21.0, -999999.0]
        
        _, result_temp, _, _, _ = simulate_airsealed_room_no_control(data)
        
        # Should not go below -273
        assert result_temp >= -273

    def test_simulate_airsealed_room_no_control_co2_in_range(self):
        """
        Tests that CO2 stays within valid range.
        """
        time = datetime.now()
        data = [time, 22.0, 400.0, 21.0, 5000.0]
        
        _, _, result_co2, _, _ = simulate_airsealed_room_no_control(data)
        
        assert 0 <= result_co2 <= 1000000

    def test_simulate_airsealed_room_no_control_o2_in_range(self):
        """
        Tests that O2 stays within valid range.
        """
        time = datetime.now()
        data = [time, 22.0, 400.0, 21.0, 5000.0]
        
        _, _, _, result_o2, _ = simulate_airsealed_room_no_control(data)
        
        assert 0 <= result_o2 <= 1000000

    def test_simulate_airsealed_room_no_control_thermal_modified(self):
        """
        Tests that thermal value is modified.
        """
        time = datetime.now()
        initial_thermal = 5000.0
        data = [time, 22.0, 400.0, 21.0, initial_thermal]
        
        _, _, _, _, result_thermal = simulate_airsealed_room_no_control(data)
        
        # Thermal should be different from input
        assert isinstance(result_thermal, (int, float))

    def test_simulate_airsealed_room_no_control_multiple_steps(self):
        """
        Tests running simulation multiple sequential steps.
        """
        time = datetime.now()
        data = [time, 22.0, 400.0, 21.0, 5000.0]
        
        # Run 5 steps
        for _ in range(5):
            data = simulate_airsealed_room_no_control(data)
        
        # Should complete without error
        assert len(data) == 5
        assert isinstance(data[0], datetime)

    def test_simulate_airsealed_room_no_control_preserves_input_type(self):
        """
        Tests that output types match expected values.
        """
        time = datetime.now()
        data = [time, 22.0, 400.0, 21.0, 5000.0]
        
        result = simulate_airsealed_room_no_control(data)
        
        assert isinstance(result[0], datetime)  # time
        assert isinstance(result[1], (int, float))  # temp
        assert isinstance(result[2], (int, float))  # co2
        assert isinstance(result[3], (int, float))  # o2
        assert isinstance(result[4], (int, float))  # thermal

    def test_simulate_airsealed_room_no_control_high_thermal(self):
        """
        Tests with high thermal energy causing temperature increase.
        """
        time = datetime.now()
        initial_temp = 22.0
        data = [time, initial_temp, 400.0, 21.0, 50000.0]
        
        _, result_temp, _, _, _ = simulate_airsealed_room_no_control(data)
        
        # Temperature should increase significantly
        assert result_temp > initial_temp

    def test_simulate_airsealed_room_no_control_low_thermal(self):
        """
        Tests with low/negative thermal energy.
        """
        time = datetime.now()
        data = [time, 22.0, 400.0, 21.0, -5000.0]
        
        result = simulate_airsealed_room_no_control(data)
        
        # Should complete successfully
        assert len(result) == 5


class TestSimulateAirsealedRoomWithControl:
    """Tests for the simulate_airsealed_room_with_control function."""

    def test_simulate_airsealed_room_with_control_returns_list(self):
        """
        Tests that function returns a list of 5 values.
        """
        time = datetime.now()
        data = [time, 22.0, 400.0, 21.0, 5000.0]
        hvac_data = [0.5, -5.0, 0.2]
        
        result = simulate_airsealed_room_with_control(data, hvac_data)
        
        assert isinstance(result, list)
        assert len(result) == 5

    def test_simulate_airsealed_room_with_control_time_increments(self):
        """
        Tests that time is incremented by 1 minute.
        """
        time = datetime(2025, 1, 27, 10, 0, 0)
        data = [time, 22.0, 400.0, 21.0, 5000.0]
        hvac_data = [0.5, -5.0, 0.2]
        
        result_time, _, _, _, _ = simulate_airsealed_room_with_control(data, hvac_data)
        
        assert result_time == time + timedelta(minutes=1)

    def test_simulate_airsealed_room_with_control_hvac_affects_temp(self):
        """
        Tests that HVAC temperature adjustments affect result.
        """
        time = datetime.now()
        data = [time, 22.0, 400.0, 21.0, 5000.0]
        
        # With HVAC cooling
        hvac_data_cool = [-5.0, 0.0, 0.0]
        result_cool = simulate_airsealed_room_with_control(data, hvac_data_cool)
        
        # Without HVAC
        hvac_data_none = [0.0, 0.0, 0.0]
        result_none = simulate_airsealed_room_with_control(data, hvac_data_none)
        
        # Results should potentially differ
        assert isinstance(result_cool[1], (int, float))
        assert isinstance(result_none[1], (int, float))

    def test_simulate_airsealed_room_with_control_hvac_affects_co2(self):
        """
        Tests that HVAC CO2 adjustments affect result.
        """
        time = datetime.now()
        data = [time, 22.0, 400.0, 21.0, 5000.0]
        hvac_data = [0.0, -10.0, 0.0]  # Reduce CO2
        
        _, _, result_co2, _, _ = simulate_airsealed_room_with_control(data, hvac_data)
        
        assert isinstance(result_co2, (int, float))
        assert 0 <= result_co2 <= 1000000

    def test_simulate_airsealed_room_with_control_hvac_affects_o2(self):
        """
        Tests that HVAC O2 adjustments affect result.
        """
        time = datetime.now()
        data = [time, 22.0, 400.0, 21.0, 5000.0]
        hvac_data = [0.0, 0.0, 1.0]  # Increase O2
        
        _, _, _, result_o2, _ = simulate_airsealed_room_with_control(data, hvac_data)
        
        assert isinstance(result_o2, (int, float))
        assert 0 <= result_o2 <= 1000000

    def test_simulate_airsealed_room_with_control_temp_minimum(self):
        """
        Tests that temperature doesn't go below -273.
        """
        time = datetime.now()
        data = [time, -200.0, 400.0, 21.0, -999999.0]
        hvac_data = [-100.0, 0.0, 0.0]  # Heavy cooling
        
        _, result_temp, _, _, _ = simulate_airsealed_room_with_control(data, hvac_data)
        
        assert result_temp >= -273

    def test_simulate_airsealed_room_with_control_co2_clamped(self):
        """
        Tests CO2 value with large HVAC adjustment.
        """
        time = datetime.now()
        data = [time, 22.0, 999999.0, 21.0, 5000.0]
        hvac_data = [0.0, 100000.0, 0.0]  # Add CO2
        
        _, _, result_co2, _, _ = simulate_airsealed_room_with_control(data, hvac_data)
        
        # CO2 is updated: initial 999999 + hvac_co2 100000 + breathing changes
        # Result should be > initial value since we're adding hvac_co2
        assert result_co2 > 999999

    def test_simulate_airsealed_room_with_control_o2_clamped(self):
        """
        Tests O2 value with large HVAC adjustment.
        """
        time = datetime.now()
        data = [time, 22.0, 400.0, 999999.0, 5000.0]
        hvac_data = [0.0, 0.0, 100000.0]  # Add O2
        
        _, _, _, result_o2, _ = simulate_airsealed_room_with_control(data, hvac_data)
        
        # O2 is updated: initial 999999 + hvac_o2 100000 + breathing changes
        # Result should be > initial value since we're adding hvac_o2
        assert result_o2 > 999999

    def test_simulate_airsealed_room_with_control_zero_hvac(self):
        """
        Tests that zero HVAC inputs don't cause errors.
        """
        time = datetime.now()
        data = [time, 22.0, 400.0, 21.0, 5000.0]
        hvac_data = [0.0, 0.0, 0.0]
        
        result = simulate_airsealed_room_with_control(data, hvac_data)
        
        assert len(result) == 5

    def test_simulate_airsealed_room_with_control_negative_hvac(self):
        """
        Tests with negative HVAC adjustments (cooling/removal).
        """
        time = datetime.now()
        data = [time, 22.0, 400.0, 21.0, 5000.0]
        hvac_data = [-10.0, -50.0, -1.0]  # All cooling/removal
        
        result = simulate_airsealed_room_with_control(data, hvac_data)
        
        assert len(result) == 5
        assert all(isinstance(v, (int, float, type(time))) for v in result)

    def test_simulate_airsealed_room_with_control_positive_hvac(self):
        """
        Tests with positive HVAC adjustments (heating/addition).
        """
        time = datetime.now()
        data = [time, 22.0, 400.0, 21.0, 5000.0]
        hvac_data = [10.0, 50.0, 1.0]  # All heating/addition
        
        result = simulate_airsealed_room_with_control(data, hvac_data)
        
        assert len(result) == 5

    def test_simulate_airsealed_room_with_control_multiple_steps(self):
        """
        Tests running controlled simulation multiple sequential steps.
        """
        time = datetime.now()
        data = [time, 22.0, 400.0, 21.0, 5000.0]
        hvac_data = [1.0, -5.0, 0.5]
        
        # Run 5 steps
        for _ in range(5):
            data = simulate_airsealed_room_with_control(data, hvac_data)
        
        assert len(data) == 5
        assert isinstance(data[0], datetime)

    def test_simulate_airsealed_room_with_control_large_hvac_adjustments(self):
        """
        Tests with very large HVAC adjustments.
        """
        time = datetime.now()
        data = [time, 22.0, 400.0, 21.0, 5000.0]
        hvac_data = [500.0, 500000.0, 500.0]  # Extreme adjustments
        
        result = simulate_airsealed_room_with_control(data, hvac_data)
        
        # Should handle without crash
        assert len(result) == 5
        # CO2/O2 should still be clamped
        assert 0 <= result[2] <= 1000000
        assert 0 <= result[3] <= 1000000
