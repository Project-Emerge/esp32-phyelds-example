"""
Dropbot board: importing it keeps the board on, and powers it off when the button is held for HOLD_MS.
``Host`` runs a phyelds device on it, talking to the boards in range over ESP-NOW.
"""
import time

from machine import Pin, I2C, Timer

HOLD_MS = 3000
POLL_MS = 50
BROADCAST = b"\xff" * 6

kill = Pin(20, Pin.OUT, value=1)  # KILL -> STM6601 PS_HOLD: high keeps the board on, low powers it off
button = Pin(21, Pin.IN, Pin.PULL_UP)  # INT <- STM6601 PB_OUT: low while the button is pressed

try:
    import ssd1306
    # this is needed for the display to work, even if the board has no display: it will raise OSError on I2C init
    oled = ssd1306.SSD1306_I2C(128, 64, I2C(0, scl=Pin(22), sda=Pin(23)))
except (ImportError, OSError):  # no driver installed or no display answering: show() does nothing
    oled = None


def show(*lines):
    """Write ``lines`` on the display, one per row (16 characters, 6 rows)."""
    if oled is None:
        return
    oled.fill(0)
    for i, line in enumerate(lines):
        oled.text(line, 0, i * 10)
    oled.show()


_held_ms = 0

def _watch_button(_):
    global _held_ms
    _held_ms = _held_ms + POLL_MS if button.value() == 0 else 0
    if _held_ms >= HOLD_MS:
        if oled is not None:
            oled.poweroff()
        kill.off()


# Runs in the background, also while the program sleeps or after it ends (at the REPL).
_timer = Timer(0, period=POLL_MS, callback=_watch_button)


def device_id(mac=None):
    """The id of a board: the last three bytes of its MAC address, of this board by default."""
    if mac is None:
        import network  # pylint: disable=import-error,import-outside-toplevel
        station = network.WLAN(network.WLAN.IF_STA)
        station.active(True)  # ESP-NOW needs the Wi-Fi station on, not connected
        mac = station.config("mac")
    return int.from_bytes(mac[-3:], "big")


class Host:
    """
    Run a phyelds ``Device`` in rounds: its messages go on ESP-NOW broadcast, its state on the display.

    ``describe(result)`` gives the lines that show the result of a round, under ``title`` and
    above the radio usage.
    """

    def __init__(self, title, device, describe, round_ms=1000):
        import espnow  # pylint: disable=import-error,import-outside-toplevel
        device_id()  # turns the Wi-Fi station on
        self.radio = espnow.ESPNow()
        self.radio.active(True)
        self.radio.add_peer(BROADCAST)
        self.title = title
        self.device = device
        self.describe = describe
        self.round_ms = round_ms
        self.heard = {}  # neighbor id -> [bytes of its last packet, rounds since it was received]

    def step(self):
        """Listen for ``round_ms``, then run a round, broadcast its message and show it."""
        deadline = time.ticks_add(time.ticks_ms(), self.round_ms)
        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            sender, payload = self.radio.recv(max(0, time.ticks_diff(deadline, time.ticks_ms())))
            if payload:
                try:
                    self.device.receive(device_id(sender), payload)
                except Exception:  # pylint: disable=broad-exception-caught
                    continue  # not a phyelds message: another ESP-NOW device, or a broken packet
                self.heard[device_id(sender)] = [len(payload), 0]
        payload = self.device.run_round({})
        self.radio.send(BROADCAST, payload, False)
        for neighbor in list(self.heard):  # dropped after device.lifetime silent rounds, as the device does
            self.heard[neighbor][1] += 1
            if self.heard[neighbor][1] > self.device.lifetime:
                del self.heard[neighbor]
        sent, _, _, received, _ = self.radio.stats()  # packets counted by the ESP-NOW driver itself
        lines = self.describe(self.device.result)
        heard = [f"<- {n:06x} {size}B" for n, (size, _) in self.heard.items()]
        print(" | ".join(lines + [f"tx {len(payload)}B"] + heard))
        show(
            f"{self.title} {self.device.device_id:06x}",
            *lines,
            f"tx {sent} pkt {len(payload)}B",
            f"rx {received} pkt",
            *heard,
        )

    def run(self):
        """Run rounds forever."""
        while True:
            self.step()
