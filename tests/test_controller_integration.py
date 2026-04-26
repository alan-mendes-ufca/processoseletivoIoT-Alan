import importlib
import sys
import types
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


class FakeClock:
    def __init__(self, start=0):
        self.now = start

    def ticks_ms(self):
        return self.now

    @staticmethod
    def ticks_diff(now, start):
        return now - start


class FakeDisplay:
    pass


class FakeHardware:
    def __init__(self, readings):
        self.readings = iter(readings)
        self.display = FakeDisplay()
        self.led_states = []
        self.valve_states = []

    def read_soil_percent(self):
        return next(self.readings)

    def set_leds(self, state):
        self.led_states.append(state)

    def set_valve(self, opened):
        self.valve_states.append(opened)


def load_controller_module(clock, display_calls):
    fake_utime = types.ModuleType("utime")
    fake_utime.ticks_ms = clock.ticks_ms
    fake_utime.ticks_diff = clock.ticks_diff

    fake_display = types.ModuleType("display")

    def update_display(display, state, humidity):
        display_calls.append((state, humidity))

    fake_display.update_display = update_display

    sys.modules["utime"] = fake_utime
    sys.modules["display"] = fake_display
    sys.modules.pop("controller", None)
    return importlib.import_module("controller")


class IrrigationControllerIntegrationTests(unittest.TestCase):
    def test_full_irrigation_cycle_returns_to_monitoring(self):
        clock = FakeClock()
        display_calls = []
        controller = load_controller_module(clock, display_calls)

        hardware = FakeHardware(
            [
                (20, 819),
                (20, 819),
                (20, 819),
                (80, 3276),
            ]
        )
        irrigation = controller.IrrigationController(hardware)

        irrigation.apply_outputs()
        irrigation.refresh_display()

        irrigation.update(500)
        self.assertEqual(irrigation.current_state, controller.SOLO_SECO)

        irrigation.update(2000)
        self.assertEqual(irrigation.current_state, controller.IRRIGANDO)

        irrigation.update(7000)
        self.assertEqual(irrigation.current_state, controller.AGUARDANDO)

        irrigation.update(11500)
        self.assertEqual(irrigation.current_state, controller.MONITORANDO)

        self.assertEqual(
            hardware.led_states,
            [
                controller.MONITORANDO,
                controller.SOLO_SECO,
                controller.IRRIGANDO,
                controller.AGUARDANDO,
                controller.MONITORANDO,
            ],
        )
        self.assertEqual(hardware.valve_states, [False, False, True, False, False])
        self.assertIn((controller.MONITORANDO, 80), display_calls)

    def test_recovery_before_irrigation_cancels_watering(self):
        clock = FakeClock()
        display_calls = []
        controller = load_controller_module(clock, display_calls)

        hardware = FakeHardware(
            [
                (20, 819),
                (60, 2457),
            ]
        )
        irrigation = controller.IrrigationController(hardware)

        irrigation.apply_outputs()
        irrigation.update(500)
        self.assertEqual(irrigation.current_state, controller.SOLO_SECO)

        irrigation.update(1000)
        self.assertEqual(irrigation.current_state, controller.MONITORANDO)
        self.assertNotIn(True, hardware.valve_states)
        self.assertEqual(
            hardware.led_states,
            [controller.MONITORANDO, controller.SOLO_SECO, controller.MONITORANDO],
        )


if __name__ == "__main__":
    unittest.main()
