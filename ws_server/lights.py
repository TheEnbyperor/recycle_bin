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
        self._logger = logging.getLogger(__name__)

    def set_state(self, intensity):
        intensity &= 0xFF
        self._logger.debug(f"Setting local light {self._pwm_chan} to {intensity}")
        intensity = (intensity * 16) - 1
        if intensity < 0:
            intensity = 0
        self._pwm.set_pwm(self._pwm_chan, 0, intensity)


class DummyPWM:
    def __init__(self):
        self._logger = logging.getLogger(__name__)

    def set_pwm_freq(self, freq):
        self._logger.debug(f"Dummy PWM freq set te {freq}")

    def set_pwm(self, chan, on, off):
        self._logger.debug(f"Dummy PWM chan {chan} set to {on}-{off}")

    def set_all_pwm(self, chan, on, off):
        self._logger.debug(f"Dummy PWM all set to {on}-{off}")


class LightingController:
    def __init__(self, config):
        self._config = config
        try:
            self._pwm = Adafruit_PCA9685.PCA9685()
        except FileNotFoundError:
            self._pwm = DummyPWM()
        self._pwm.set_pwm_freq(200)

    def get_compartment(self, comp_id):
        comp_config = self._config.get_compartment(comp_id)
        if comp_config is None:
            return None
        if comp_config.type == config.CompartmentConfig.CompartmentType.LOCAL:
            return LocalLightingDevice(self._pwm, comp_config.channel)
        else:
            return None

    def reset(self):
        self._pwm.set_all_pwm(0, 0)