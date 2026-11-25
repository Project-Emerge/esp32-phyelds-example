# ESP32 MicroPython examples

Examples for Dropbot boards with an ESP32-C6, 
and an SSD1306 display. 
The aggregate computing examples use [Phyelds](https://github.com/phyelds/phyelds) over ESP-NOW.

## Requirements

- A Dropbot board running MicroPython 1.29.0, connected over USB.
- Python 3.13 and [uv](https://docs.astral.sh/uv/).
- Two or more boards for the communication examples.

The pin assignments in `board.py` are specific to the Dropbot hardware.

## Flash MicroPython

The firmware binary is not stored in this repository. Download
[ESP32_GENERIC_C6-20260824-v1.29.0.bin](https://micropython.org/resources/firmware/ESP32_GENERIC_C6-20260824-v1.29.0.bin)
(other versions on [MicroPython downloads](https://micropython.org/download/ESP32_GENERIC_C6/)), connect the board and run once:

```sh
uv sync
uv run esptool --chip esp32c6 erase-flash
uv run esptool --chip esp32c6 write-flash 0 ESP32_GENERIC_C6-20260824-v1.29.0.bin
```

## Deploy

Install the host tools with `uv sync`, connect a board and run:

```sh
./deploy.sh                    # remember_demo.py
./deploy.sh scr_demo.py        # leader election and node count
```

The script builds the required Phyelds modules as MicroPython bytecode, 
installs the SSD1306 driver and copies the selected program as `main.py`. 
It replaces the existing `phyelds` directory and `main.py` on the board, 
then resets it. 
Use the same Phyelds version on all communicating boards. 
The script pins Phyelds 10.0.0 and `mpy-cross` 1.29.0.post2; 
match the compiler version to the firmware when changing MicroPython versions.

Connect to the serial REPL with `uv run mpremote`. 
The aggregate examples communicate over ESP-NOW and report results on the display and serial console.

## Files

- `board.py`: power button, display and ESP-NOW host.
- `remember_demo.py`: round counter and neighbors.
- `scr_demo.py`: leader election, hop distance and node count.
- `deploy.sh`: build and copy a selected example to the board.

Generated files, virtual environments and downloaded firmware are ignored by Git.
