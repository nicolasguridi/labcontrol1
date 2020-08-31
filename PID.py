from time import time, sleep

class PID:
    def __init__(self, kp=0.2, ki=0.05, kd=0.005, kw=0.3, kn=0.5, v_max=1):
        # PID constants
        self.kp, self.ki, self.kd = kp, ki, kd
        # anti wind up constant
        self.kw = kw
        # derivative filter constant
        self.kn = kn
        # max voltage
        self.v_max = v_max
        # set times
        self.sample_time = 0
        self.current_time = time()
        self.last_time = self.current_time
        # set reference
        self.ref = 0
        # PID outputs
        self.p, self.i, self.d = 0, 0, 0
        # outputs
        self.delta_v = 0
        # derivative filter
        self.substractor = 0

    def update(self, y):
        # set times
        self.current_time = time()
        delta_time = self.current_time - self.last_time
        sleep_time = self.sample_time - delta_time
        self.last_time = self.current_time
        if sleep_time > 0:
            sleep(sleep_time)

        # calculate error
        error = self.ref - y

        # proportional output
        self.p = self.kp * error
        # integral output
        self.i += (self.ki * error + self.kw * self.delta_v) * delta_time
        # derivative output
        if delta_time != 0:
            self.substractor += self.d * delta_time
            self.d = (self.kd * error - self.substractor) * self.kn

        # PID output
        pv = self.p + self.i + self.d
        if pv > self.v_max:
            v = self.v_max
        elif pv < 0:
            v = 0
        else:
            v = pv
        # update v delta
        self.delta_v = v - pv
        return v
