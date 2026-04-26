"""Abstracoes de leitura do sensor e controle dos atuadores fisicos."""

from machine import ADC, PWM, Pin, SoftI2C

from config import (
    ADC_MAX,
    LED_BLUE_PIN,
    LED_GREEN_PIN,
    LED_RED_PIN,
    OLED_SCL_PIN,
    OLED_SDA_PIN,
    SERVO_CLOSED_ANGLE,
    SERVO_FREQ,
    SERVO_OPEN_ANGLE,
    SERVO_PIN,
    SOIL_PIN,
)
from display import SSD1306_I2C


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def angle_to_duty(angle):
    angle = clamp(angle, 0, 180)
    return int(26 + (angle / 180) * 102)


class IrrigationHardware:
    def __init__(self):
        self.soil_sensor = ADC(Pin(SOIL_PIN))
        self.soil_sensor.atten(ADC.ATTN_11DB)
        self.soil_sensor.width(ADC.WIDTH_12BIT)

        self.servo = PWM(Pin(SERVO_PIN), freq=SERVO_FREQ)
        self.led_green = Pin(LED_GREEN_PIN, Pin.OUT)
        self.led_blue = Pin(LED_BLUE_PIN, Pin.OUT)
        self.led_red = Pin(LED_RED_PIN, Pin.OUT)

        i2c = SoftI2C(scl=Pin(OLED_SCL_PIN), sda=Pin(OLED_SDA_PIN), freq=400000)
        self.display = SSD1306_I2C(128, 64, i2c)

    def read_soil_percent(self):
        raw_value = self.soil_sensor.read()
        percent = int((raw_value / ADC_MAX) * 100)
        return clamp(percent, 0, 100), raw_value

    def set_valve(self, opened):
        angle = SERVO_OPEN_ANGLE if opened else SERVO_CLOSED_ANGLE
        self.servo.duty(angle_to_duty(angle))

    def set_leds(self, state):
        from config import IRRIGANDO, MONITORANDO, SOLO_SECO

        self.led_green.value(1 if state == MONITORANDO else 0)
        self.led_blue.value(1 if state == IRRIGANDO else 0)
        self.led_red.value(1 if state == SOLO_SECO else 0)
