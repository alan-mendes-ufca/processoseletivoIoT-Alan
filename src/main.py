"""Ponto de entrada do firmware e loop principal da aplicacao."""

from utime import sleep_ms, ticks_ms

from controller import IrrigationController
from hardware import IrrigationHardware


hardware = IrrigationHardware()
controller = IrrigationController(hardware)

controller.apply_outputs()
controller.refresh_display()
print("BOOT: Irrigacao automatica iniciada")
print("STATE: {}".format(controller.current_state))

while True:
    controller.update(ticks_ms())
    sleep_ms(50)
