import pytest
import math
from unittest.mock import patch, MagicMock

from backend.simulation.HVAC import PID, use_hvac


class TestPIDClass:
    """Tests for the PID controller class."""

    def test_pid_initialization(self):
        """
        Tests that PID initializes with correct parameters.
        """
        kp, ki, kd, setpoint = 1.0, 0.5, 0.2, 22.0
        pid = PID(kp, ki, kd, setpoint)
        
        assert pid.Kp == kp
        assert pid.Ki == ki
        assert pid.Kd == kd
        assert pid.setpoint == setpoint
        assert pid.previous_error == 0
        assert pid.integral == 0

    def test_pid_initialization_default_setpoint(self):
        """
        Tests that PID defaults setpoint to 0 if not provided.
        """
        pid = PID(1.0, 0.5, 0.2)
        
        assert pid.setpoint == 0

    def test_pid_initialization_with_negative_gains(self):
        """
        Tests that PID handles negative gain values.
        """
        pid = PID(-1.0, -0.5, -0.2, 20.0)
        
        assert pid.Kp == -1.0
        assert pid.Ki == -0.5
        assert pid.Kd == -0.2

    def test_pid_initialization_with_zero_gains(self):
        """
        Tests that PID handles zero gain values.
        """
        pid = PID(0.0, 0.0, 0.0, 20.0)
        
        assert pid.Kp == 0.0
        assert pid.Ki == 0.0
        assert pid.Kd == 0.0

    def test_pid_update_basic(self):
        """
        Tests basic PID update with typical values.
        """
        pid = PID(Kp=2.0, Ki=0.5, Kd=0.1, setpoint=22.0)
        measurement = 20.0
        dt = 1.0
        
        output = pid.update(measurement, dt)
        
        # Should have non-zero output since measurement != setpoint
        assert output != 0
        # Proportional error: setpoint - measurement = 22 - 20 = 2
        # integral = 2 * 1 = 2
        # derivative = (2 - 0) / 1 = 2
        # Output = Kp*error + Ki*integral + Kd*derivative
        # = 2.0*2 + 0.5*2 + 0.1*2 = 4.0 + 1.0 + 0.2 = 5.2
        assert abs(output - 5.2) < 0.001

    def test_pid_update_zero_error(self):
        """
        Tests PID update when measurement equals setpoint.
        """
        pid = PID(Kp=2.0, Ki=0.5, Kd=0.1, setpoint=22.0)
        measurement = 22.0  # At setpoint
        dt = 1.0
        
        output = pid.update(measurement, dt)
        
        # Error is zero, so output should be zero
        assert output == 0.0

    def test_pid_update_proportional_term(self):
        """
        Tests that proportional term is calculated correctly.
        """
        pid = PID(Kp=10.0, Ki=0.0, Kd=0.0, setpoint=25.0)
        measurement = 20.0
        dt = 1.0
        
        output = pid.update(measurement, dt)
        
        # Proportional term only: Kp * error = 10 * (25-20) = 50
        assert abs(output - 50.0) < 0.001

    def test_pid_update_integral_accumulation(self):
        """
        Tests that integral accumulates over multiple updates.
        """
        pid = PID(Kp=0.0, Ki=1.0, Kd=0.0, setpoint=25.0)
        measurement = 20.0
        dt = 1.0
        
        # First update
        output1 = pid.update(measurement, dt)
        # error = 5, integral = 5*1 = 5, output = 1*5 = 5
        assert abs(output1 - 5.0) < 0.001
        
        # Second update
        output2 = pid.update(measurement, dt)
        # error = 5, integral = 5 + 5*1 = 10, output = 1*10 = 10
        assert abs(output2 - 10.0) < 0.001

    def test_pid_update_derivative_term(self):
        """
        Tests that derivative term responds to error change.
        """
        pid = PID(Kp=0.0, Ki=0.0, Kd=10.0, setpoint=25.0)
        dt = 1.0
        
        # First update with error = 5
        output1 = pid.update(20.0, dt)
        # derivative = (5 - 0) / 1 = 5, output = 10*5 = 50
        assert abs(output1 - 50.0) < 0.001
        
        # Second update with error = 2 (measurement at 23)
        output2 = pid.update(23.0, dt)
        # derivative = (2 - 5) / 1 = -3, output = 10*(-3) = -30
        assert abs(output2 - (-30.0)) < 0.001

    def test_pid_update_zero_dt(self):
        """
        Tests PID update with zero time delta (avoids division by zero).
        """
        pid = PID(Kp=1.0, Ki=1.0, Kd=1.0, setpoint=22.0)
        measurement = 20.0
        dt = 0.0
        
        output = pid.update(measurement, dt)
        
        # Should not crash, derivative should be 0 when dt=0
        # error = 2, integral = 2*0 = 0
        # Output = 1*2 + 1*0 + 0 = 2
        assert abs(output - 2.0) < 0.001

    def test_pid_update_negative_error(self):
        """
        Tests PID with negative error (measurement > setpoint).
        """
        pid = PID(Kp=1.0, Ki=1.0, Kd=1.0, setpoint=20.0)
        measurement = 25.0  # Above setpoint
        dt = 1.0
        
        output = pid.update(measurement, dt)
        
        # error = 20 - 25 = -5
        # integral = -5 * 1 = -5
        # derivative = (-5 - 0) / 1 = -5
        # Output = 1*(-5) + 1*(-5) + 1*(-5) = -15
        assert abs(output - (-15.0)) < 0.001

    def test_pid_update_large_error(self):
        """
        Tests PID with large error values.
        """
        pid = PID(Kp=1.0, Ki=0.1, Kd=0.01, setpoint=20.0)
        measurement = 0.0  # Very far from setpoint
        dt = 1.0
        
        output = pid.update(measurement, dt)
        
        # error = 20
        # Output = 1*20 + 0.1*20 + 0.01*20 = 20 + 2 + 0.2 = 22.2
        assert abs(output - 22.2) < 0.01

    def test_pid_update_small_error(self):
        """
        Tests PID with very small error values.
        """
        pid = PID(Kp=1.0, Ki=1.0, Kd=1.0, setpoint=22.0)
        measurement = 21.999
        dt = 1.0
        
        output = pid.update(measurement, dt)
        
        # error = 0.001
        # integral = 0.001 * 1 = 0.001
        # derivative = (0.001 - 0) / 1 = 0.001
        # Output = 1*0.001 + 1*0.001 + 1*0.001 = 0.003
        assert abs(output - 0.003) < 0.0001

    def test_pid_multiple_sequential_updates(self):
        """
        Tests PID over multiple sequential updates tracking state changes.
        """
        pid = PID(Kp=2.0, Ki=0.5, Kd=1.0, setpoint=22.0)
        dt = 1.0
        measurements = [20.0, 21.0, 21.5, 22.0, 22.5]
        
        outputs = []
        for measurement in measurements:
            output = pid.update(measurement, dt)
            outputs.append(output)
        
        # First output should be highest (largest error)
        assert outputs[0] == max(outputs)
        # Last output should be near zero (at setpoint)
        assert abs(outputs[-1]) < 0.5

    def test_pid_error_history_tracking(self):
        """
        Tests that PID tracks previous error for derivative calculation.
        """
        pid = PID(Kp=1.0, Ki=1.0, Kd=1.0, setpoint=25.0)
        dt = 1.0
        
        # First update
        pid.update(20.0, dt)
        assert pid.previous_error == 5.0
        
        # Second update
        pid.update(23.0, dt)
        assert pid.previous_error == 2.0

    def test_pid_integral_anti_windup_conceptual(self):
        """
        Tests that integral continues accumulating (no anti-windup implemented).
        """
        pid = PID(Kp=0.0, Ki=1.0, Kd=0.0, setpoint=25.0)
        dt = 1.0
        
        # Repeated updates with same error should accumulate integral
        for _ in range(10):
            pid.update(20.0, dt)
        
        # Integral should be 5 * 10 = 50
        assert pid.integral == 50.0

    def test_pid_with_fractional_dt(self):
        """
        Tests PID with fractional time delta.
        """
        pid = PID(Kp=1.0, Ki=1.0, Kd=1.0, setpoint=22.0)
        measurement = 20.0
        dt = 0.5  # Half second
        
        output = pid.update(measurement, dt)
        
        # error = 2
        # integral = 2 * 0.5 = 1
        # derivative = (2 - 0) / 0.5 = 4
        # Output = 1*2 + 1*1 + 1*4 = 7
        assert abs(output - 7.0) < 0.001

    def test_pid_very_small_gains(self):
        """
        Tests PID with very small gain values.
        """
        pid = PID(Kp=0.001, Ki=0.0001, Kd=0.00001, setpoint=22.0)
        measurement = 20.0
        dt = 1.0
        
        output = pid.update(measurement, dt)
        
        # Should produce small output
        assert abs(output) < 0.01

    def test_pid_large_gains(self):
        """
        Tests PID with large gain values.
        """
        pid = PID(Kp=100.0, Ki=50.0, Kd=25.0, setpoint=22.0)
        measurement = 20.0
        dt = 1.0
        
        output = pid.update(measurement, dt)
        
        # error = 2
        # integral = 2 * 1 = 2
        # derivative = (2 - 0) / 1 = 2
        # Output = 100*2 + 50*2 + 25*2 = 200 + 100 + 50 = 350
        assert abs(output - 350.0) < 0.1


class TestUseHvacFunction:
    """Tests for the use_hvac function."""

    def test_use_hvac_basic(self):
        """
        Tests basic use_hvac function call.
        """
        pid_temp = PID(Kp=1.0, Ki=0.1, Kd=0.01, setpoint=22.0)
        pid_co2 = PID(Kp=1.0, Ki=0.1, Kd=0.01, setpoint=400.0)
        pid_o2 = PID(Kp=1.0, Ki=0.1, Kd=0.01, setpoint=21.0)
        
        data = [1, 20.0, 401.0, 20.5, 5000.0]
        
        result_data, result_pid_temp, result_pid_co2, result_pid_o2 = use_hvac(
            data, pid_temp, pid_co2, pid_o2
        )
        
        # Should return modified data
        assert len(result_data) == 5
        assert result_data[0] == 1  # Time unchanged
        assert result_data[4] == 5000.0  # Thermal unchanged
        
        # PIDs should be updated
        assert result_pid_temp is pid_temp
        assert result_pid_co2 is pid_co2
        assert result_pid_o2 is pid_o2

    def test_use_hvac_temperature_control(self):
        """
        Tests that temperature is adjusted by PID controller.
        """
        pid_temp = PID(Kp=2.0, Ki=0.0, Kd=0.0, setpoint=22.0)
        pid_co2 = PID(Kp=0.0, Ki=0.0, Kd=0.0, setpoint=400.0)
        pid_o2 = PID(Kp=0.0, Ki=0.0, Kd=0.0, setpoint=21.0)
        
        data = [1, 20.0, 401.0, 20.5, 5000.0]
        
        result_data, _, _, _ = use_hvac(data, pid_temp, pid_co2, pid_o2)
        
        # Temperature is replaced with PID output
        # error = 22.0 - 20.0 = 2
        # integral = 2 * 1 = 2
        # derivative = (2 - 0) / 1 = 2
        # PID output = 2.0*2 + 0*2 + 0*2 = 4.0
        # New temp = 4.0
        assert abs(result_data[1] - 4.0) < 0.001

    def test_use_hvac_co2_control(self):
        """
        Tests that CO2 is adjusted by PID controller.
        """
        pid_temp = PID(Kp=0.0, Ki=0.0, Kd=0.0, setpoint=22.0)
        pid_co2 = PID(Kp=1.0, Ki=0.0, Kd=0.0, setpoint=400.0)
        pid_o2 = PID(Kp=0.0, Ki=0.0, Kd=0.0, setpoint=21.0)
        
        data = [1, 20.0, 405.0, 20.5, 5000.0]
        
        result_data, _, _, _ = use_hvac(data, pid_temp, pid_co2, pid_o2)
        
        # CO2 is replaced with PID output
        # error = 400.0 - 405.0 = -5
        # integral = -5 * 1 = -5
        # derivative = (-5 - 0) / 1 = -5
        # PID output = 1.0*(-5) + 0*(-5) + 0*(-5) = -5.0
        # New CO2 = -5.0
        assert abs(result_data[2] - (-5.0)) < 0.001

    def test_use_hvac_o2_control(self):
        """
        Tests that O2 is adjusted by PID controller.
        """
        pid_temp = PID(Kp=0.0, Ki=0.0, Kd=0.0, setpoint=22.0)
        pid_co2 = PID(Kp=0.0, Ki=0.0, Kd=0.0, setpoint=400.0)
        pid_o2 = PID(Kp=2.0, Ki=0.0, Kd=0.0, setpoint=21.0)
        
        data = [1, 20.0, 401.0, 20.0, 5000.0]
        
        result_data, _, _, _ = use_hvac(data, pid_temp, pid_co2, pid_o2)
        
        # O2 is replaced with PID output
        # error = 21.0 - 20.0 = 1
        # integral = 1 * 1 = 1
        # derivative = (1 - 0) / 1 = 1
        # PID output = 2.0*1 + 0*1 + 0*1 = 2.0
        # New O2 = 2.0
        assert abs(result_data[3] - 2.0) < 0.001

    def test_use_hvac_all_controlled(self):
        """
        Tests that all parameters are controlled simultaneously.
        """
        pid_temp = PID(Kp=1.0, Ki=0.0, Kd=0.0, setpoint=22.0)
        pid_co2 = PID(Kp=1.0, Ki=0.0, Kd=0.0, setpoint=400.0)
        pid_o2 = PID(Kp=1.0, Ki=0.0, Kd=0.0, setpoint=21.0)
        
        data = [1, 20.0, 405.0, 20.0, 5000.0]
        
        result_data, _, _, _ = use_hvac(data, pid_temp, pid_co2, pid_o2)
        
        # All should be adjusted
        assert result_data[1] != 20.0  # Temperature changed
        assert result_data[2] != 405.0  # CO2 changed
        assert result_data[3] != 20.0  # O2 changed

    def test_use_hvac_time_unchanged(self):
        """
        Tests that time value remains unchanged.
        """
        pid_temp = PID(Kp=1.0, Ki=0.0, Kd=0.0, setpoint=22.0)
        pid_co2 = PID(Kp=1.0, Ki=0.0, Kd=0.0, setpoint=400.0)
        pid_o2 = PID(Kp=1.0, Ki=0.0, Kd=0.0, setpoint=21.0)
        
        data = [42, 20.0, 400.0, 21.0, 5000.0]
        
        result_data, _, _, _ = use_hvac(data, pid_temp, pid_co2, pid_o2)
        
        # Time should be first element
        assert result_data[0] == 42

    def test_use_hvac_thermal_unchanged(self):
        """
        Tests that thermal value remains unchanged.
        """
        pid_temp = PID(Kp=1.0, Ki=0.0, Kd=0.0, setpoint=22.0)
        pid_co2 = PID(Kp=1.0, Ki=0.0, Kd=0.0, setpoint=400.0)
        pid_o2 = PID(Kp=1.0, Ki=0.0, Kd=0.0, setpoint=21.0)
        
        data = [1, 20.0, 400.0, 21.0, 7500.0]
        
        result_data, _, _, _ = use_hvac(data, pid_temp, pid_co2, pid_o2)
        
        # Thermal should be last element
        assert result_data[4] == 7500.0

    def test_use_hvac_returns_pid_instances(self):
        """
        Tests that use_hvac returns the same PID instances (not copies).
        """
        pid_temp = PID(Kp=1.0, Ki=0.1, Kd=0.01, setpoint=22.0)
        pid_co2 = PID(Kp=1.0, Ki=0.1, Kd=0.01, setpoint=400.0)
        pid_o2 = PID(Kp=1.0, Ki=0.1, Kd=0.01, setpoint=21.0)
        
        data = [1, 20.0, 401.0, 20.5, 5000.0]
        
        result_data, ret_pid_temp, ret_pid_co2, ret_pid_o2 = use_hvac(
            data, pid_temp, pid_co2, pid_o2
        )
        
        # Should return same instances
        assert ret_pid_temp is pid_temp
        assert ret_pid_co2 is pid_co2
        assert ret_pid_o2 is pid_o2

    def test_use_hvac_pid_state_updated(self):
        """
        Tests that PID state is updated (previous_error, integral).
        """
        pid_temp = PID(Kp=1.0, Ki=1.0, Kd=0.0, setpoint=22.0)
        initial_integral = pid_temp.integral
        
        data = [1, 20.0, 401.0, 20.5, 5000.0]
        _, updated_pid, _, _ = use_hvac(data, pid_temp, PID(1, 1, 0, 400), PID(1, 1, 0, 21))
        
        # PID state should be updated
        assert updated_pid.previous_error != 0
        assert updated_pid.integral != initial_integral

    def test_use_hvac_data_list_structure(self):
        """
        Tests that use_hvac returns data in correct list structure.
        """
        pid_temp = PID(Kp=0.1, Ki=0.01, Kd=0.001, setpoint=22.0)
        pid_co2 = PID(Kp=0.1, Ki=0.01, Kd=0.001, setpoint=400.0)
        pid_o2 = PID(Kp=0.1, Ki=0.01, Kd=0.001, setpoint=21.0)
        
        data = [10, 20.5, 402.0, 20.8, 5100.0]
        
        result_data, _, _, _ = use_hvac(data, pid_temp, pid_co2, pid_o2)
        
        # Should be a list with 5 elements
        assert isinstance(result_data, list)
        assert len(result_data) == 5

    def test_use_hvac_with_zero_pid_gains(self):
        """
        Tests use_hvac with zero gains (no control applied).
        """
        pid_temp = PID(Kp=0.0, Ki=0.0, Kd=0.0, setpoint=22.0)
        pid_co2 = PID(Kp=0.0, Ki=0.0, Kd=0.0, setpoint=400.0)
        pid_o2 = PID(Kp=0.0, Ki=0.0, Kd=0.0, setpoint=21.0)
        
        data = [1, 20.0, 401.0, 20.5, 5000.0]
        
        result_data, _, _, _ = use_hvac(data, pid_temp, pid_co2, pid_o2)
        
        # Values should be zero with zero gains (PID output = 0)
        assert result_data[1] == 0.0
        assert result_data[2] == 0.0
        assert result_data[3] == 0.0

    def test_use_hvac_negative_values(self):
        """
        Tests use_hvac with negative sensor values.
        """
        pid_temp = PID(Kp=1.0, Ki=0.0, Kd=0.0, setpoint=22.0)
        pid_co2 = PID(Kp=1.0, Ki=0.0, Kd=0.0, setpoint=400.0)
        pid_o2 = PID(Kp=1.0, Ki=0.0, Kd=0.0, setpoint=21.0)
        
        data = [1, -5.0, -100.0, -10.0, 5000.0]
        
        result_data, _, _, _ = use_hvac(data, pid_temp, pid_co2, pid_o2)
        
        # Should handle negative values
        assert isinstance(result_data, list)
        assert len(result_data) == 5

    def test_use_hvac_large_values(self):
        """
        Tests use_hvac with large sensor values.
        """
        pid_temp = PID(Kp=0.01, Ki=0.001, Kd=0.0001, setpoint=22.0)
        pid_co2 = PID(Kp=0.01, Ki=0.001, Kd=0.0001, setpoint=400.0)
        pid_o2 = PID(Kp=0.01, Ki=0.001, Kd=0.0001, setpoint=21.0)
        
        data = [1, 1000.0, 100000.0, 10000.0, 999999.0]
        
        result_data, _, _, _ = use_hvac(data, pid_temp, pid_co2, pid_o2)
        
        # Should handle large values
        assert isinstance(result_data, list)
        assert result_data[4] == 999999.0  # Thermal unchanged

    def test_use_hvac_float_values(self):
        """
        Tests use_hvac with decimal/float values.
        """
        pid_temp = PID(Kp=1.5, Ki=0.5, Kd=0.2, setpoint=22.5)
        pid_co2 = PID(Kp=1.5, Ki=0.5, Kd=0.2, setpoint=400.5)
        pid_o2 = PID(Kp=1.5, Ki=0.5, Kd=0.2, setpoint=21.5)
        
        data = [1.5, 20.7, 401.2, 20.3, 5000.8]
        
        result_data, _, _, _ = use_hvac(data, pid_temp, pid_co2, pid_o2)
        
        # Should handle floats correctly
        assert isinstance(result_data[1], (int, float))
        assert isinstance(result_data[2], (int, float))
        assert isinstance(result_data[3], (int, float))

    def test_use_hvac_multiple_consecutive_calls(self):
        """
        Tests calling use_hvac multiple times with same PIDs.
        """
        pid_temp = PID(Kp=1.0, Ki=0.1, Kd=0.01, setpoint=22.0)
        pid_co2 = PID(Kp=1.0, Ki=0.1, Kd=0.01, setpoint=400.0)
        pid_o2 = PID(Kp=1.0, Ki=0.1, Kd=0.01, setpoint=21.0)
        
        data1 = [1, 20.0, 401.0, 20.5, 5000.0]
        data2 = [2, 21.0, 400.0, 20.8, 5100.0]
        
        result1, pid_temp, pid_co2, pid_o2 = use_hvac(data1, pid_temp, pid_co2, pid_o2)
        result2, pid_temp, pid_co2, pid_o2 = use_hvac(data2, pid_temp, pid_co2, pid_o2)
        
        # Both should complete successfully
        assert len(result1) == 5
        assert len(result2) == 5
        # Times should be preserved
        assert result1[0] == 1
        assert result2[0] == 2
