import Adafruit_PCA9685
import config
import logging


class LightingDevice:
    def set_state(self, intensity):
        raise NotImplementedError


class LocalLightingDevice(LightingDevice):
    def __init__(self, pwm, channel):
        self._pwm = pwm
        self._pwm_chan = channel

    def set_state(self, intensity):
        intensity &= 0xFF
        logging.debug(f"Setting local light {self._pwm_chan} to {intensity}")
        intensity = (intensity * 16) - 1
        if intensity < 0:
            intensity = 0
        self._pwm.set_pwm(self._pwm_chan, 0, intensity)


class DummyPWM:
    def __init__(self):
        pass

    @staticmethod
    def set_pwm_freq(freq):
        logging.debug(f"Dummy PWM freq set te {freq}")

    @staticmethod
    def set_pwm(chan, on, off):
        logging.debug(f"Dummy PWM chan {chan} set to {on}-{off}")

    @staticmethod
    def set_all_pwm(on, off):
        logging.debug(f"Dummy PWM all set to {on}-{off}")


class LightingController:
    def __init__(self, config):
        self._config = config
        try:
            self._pwm = Adafruit_PCA9685.PCA9685()
        except (FileNotFoundError, RuntimeError, PermissionError):
            self._pwm = DummyPWM()
        self._pwm.set_pwm_freq(200)

    def get_compartment(self, comp_id):
        comp_config = self._config.get_compartment(comp_id)
        if comp_config is None:
            logging.warn(f"No valid compartment config for {comp_id}")
            return None
        if comp_config.type == config.CompartmentConfig.CompartmentType.LOCAL:
            return LocalLightingDevice(self._pwm, comp_config.channel)
        else:
            return None

    def reset(self):
        self._pwm.set_all_pwm(0, 0)