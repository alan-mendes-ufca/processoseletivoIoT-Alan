"""Driver do OLED e funcoes de apresentacao do estado atual."""

import framebuf

from config import AGUARDANDO, IRRIGANDO, MONITORANDO, RECOVERY_THRESHOLD, SOLO_SECO, STATE_LABELS


class SSD1306(framebuf.FrameBuffer):
    def __init__(self, width, height, external_vcc):
        self.width = width
        self.height = height
        self.external_vcc = external_vcc
        self.pages = self.height // 8
        self.buffer = bytearray(self.pages * self.width)
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_VLSB)
        self.init_display()

    def init_display(self):
        for cmd in (
            0xAE,
            0x20,
            0x00,
            0x40,
            0xA1,
            0xA8,
            self.height - 1,
            0xC8,
            0xD3,
            0x00,
            0xDA,
            0x12 if self.width > 2 * self.height else 0x02,
            0xD5,
            0x80,
            0xD9,
            0x22 if self.external_vcc else 0xF1,
            0xDB,
            0x30,
            0x81,
            0xFF,
            0xA4,
            0xA6,
            0x8D,
            0x10 if self.external_vcc else 0x14,
            0xAF,
        ):
            self.write_cmd(cmd)
        self.fill(0)
        self.show()

    def show(self):
        x0 = 0
        x1 = self.width - 1
        if self.width == 64:
            x0 += 32
            x1 += 32
        self.write_cmd(0x21)
        self.write_cmd(x0)
        self.write_cmd(x1)
        self.write_cmd(0x22)
        self.write_cmd(0)
        self.write_cmd(self.pages - 1)
        self.write_data(self.buffer)

    def write_cmd(self, cmd):
        raise NotImplementedError

    def write_data(self, buf):
        raise NotImplementedError


class SSD1306_I2C(SSD1306):
    def __init__(self, width, height, i2c, addr=0x3C, external_vcc=False):
        self.i2c = i2c
        self.addr = addr
        self.temp = bytearray(2)
        self.write_list = [b"\x40", None]
        super().__init__(width, height, external_vcc)

    def write_cmd(self, cmd):
        self.temp[0] = 0x80
        self.temp[1] = cmd
        self.i2c.writeto(self.addr, self.temp)

    def write_data(self, buf):
        self.write_list[1] = buf
        self.i2c.writevto(self.addr, self.write_list)


def status_message(state, humidity):
    if state == MONITORANDO:
        return "Solo ok" if humidity >= RECOVERY_THRESHOLD else "Em analise"
    if state == SOLO_SECO:
        return "Iniciando rega"
    if state == IRRIGANDO:
        return "Valvula aberta"
    if state == AGUARDANDO:
        return "Estabilizando"
    return "Estado invalido"


def update_display(display, state, humidity):
    display.fill(0)
    display.text("Irrigacao Auto", 0, 0)
    display.text("Umidade: {:>3}%".format(humidity), 0, 16)
    display.text("Estado:", 0, 32)
    display.text(STATE_LABELS[state], 0, 42)
    display.text(status_message(state, humidity), 0, 56)
    display.show()
