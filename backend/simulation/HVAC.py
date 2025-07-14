class PID:

    def __init__(self, Kp, Ki, Kd, setpoint=0):
        self.Kp = Kp  # Proportional gain
        self.Ki = Ki  # Integral gain
        self.Kd = Kd  # Derivative gain
        self.setpoint = setpoint

        self.previous_error = 0
        self.integral = 0

    def update(self, measurement, dt):

        # Difference between setpoint and measurement
        error = self.setpoint - measurement
        
        # Integral
        self.integral += error * dt
        
        # Derivative
        derivative = (error - self.previous_error) / dt if dt > 0 else 0
        
        # PID output
        output = self.Kp * error + self.Ki * self.integral + self.Kd * derivative

        # Save error for next calc
        self.previous_error = error

        return output


def use_hvac(data, pid_temp, pid_co2, pid_o2):

    time,temp,co2,o2,thermal = data

    temp = pid_temp.update(temp,1)
    co2 = pid_co2.update(co2,1)
    o2 = pid_o2.update(o2,1)

    return [time,temp,co2,o2,thermal], pid_temp, pid_co2, pid_o2

    
