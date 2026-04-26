"""Maquina de estados e regras de transicao da irrigacao automatica."""

from utime import ticks_diff, ticks_ms

from config import (
    AGUARDANDO,
    DISPLAY_INTERVAL_MS,
    DRY_CONFIRMATION_MS,
    DRY_THRESHOLD,
    IRRIGANDO,
    IRRIGATION_DURATION_MS,
    MONITORANDO,
    POST_IRRIGATION_WAIT_MS,
    READ_INTERVAL_MS,
    RECOVERY_THRESHOLD,
    SOLO_SECO,
)
from display import update_display


class IrrigationController:
    def __init__(self, hardware):
        self.hardware = hardware
        self.current_state = MONITORANDO
        self.state_started_at = ticks_ms()
        self.last_read_at = self.state_started_at - READ_INTERVAL_MS
        self.last_display_at = self.state_started_at - DISPLAY_INTERVAL_MS
        self.humidity_percent = 0
        self.humidity_raw = 0

    def apply_outputs(self):
        self.hardware.set_leds(self.current_state)
        self.hardware.set_valve(self.current_state == IRRIGANDO)

    def refresh_display(self):
        update_display(self.hardware.display, self.current_state, self.humidity_percent)

    def change_state(self, next_state):
        if next_state == self.current_state:
            return

        previous_state = self.current_state
        self.current_state = next_state
        self.state_started_at = ticks_ms()
        self.apply_outputs()
        print(
            f"STATE: {previous_state} -> {self.current_state,
                } | umidade={self.humidity_percent} | bruto={
                self.humidity_raw}"
        )

    def handle_state(self, now):
        elapsed = ticks_diff(now, self.state_started_at)

        if self.current_state == MONITORANDO:
            if self.humidity_percent <= DRY_THRESHOLD:
                self.change_state(SOLO_SECO)
            return

        if self.current_state == SOLO_SECO:
            if self.humidity_percent >= RECOVERY_THRESHOLD:
                self.change_state(MONITORANDO)
            elif elapsed >= DRY_CONFIRMATION_MS:
                self.change_state(IRRIGANDO)
            return

        if self.current_state == IRRIGANDO:
            if elapsed >= IRRIGATION_DURATION_MS:
                self.change_state(AGUARDANDO)
            return

        if elapsed >= POST_IRRIGATION_WAIT_MS:
            if self.humidity_percent <= DRY_THRESHOLD:
                self.change_state(SOLO_SECO)
            else:
                self.change_state(MONITORANDO)

    def update(self, now):
        if ticks_diff(now, self.last_read_at) >= READ_INTERVAL_MS:
            self.humidity_percent, self.humidity_raw = self.hardware.read_soil_percent()
            self.last_read_at = now
            self.handle_state(now)

        if ticks_diff(now, self.last_display_at) >= DISPLAY_INTERVAL_MS:
            self.refresh_display()
            self.last_display_at = now
