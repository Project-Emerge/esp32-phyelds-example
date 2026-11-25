#!/bin/sh
# Install a program on the board as main.py, with board.py, the ssd1306 driver and phyelds.
# phyelds goes as .mpy bytecode, only the modules and definitions the program uses (--mpy --prune).
# Usage: ./deploy.sh [program.py]   (default: remember_demo.py)
set -e
PHYELDS=phyelds==10.0.0  # use the same version on every board
MPY_CROSS=mpy-cross==1.29.0.post2  # must match the MicroPython version of the board
program=${1:-remember_demo.py}
name=$(basename "$program" .py)
rm -rf dist
# board.py goes to the build only for --prune to keep what it calls (Device.run_round): the board gets it as it is
uv run --with "$PHYELDS" --with "$MPY_CROSS" python -m phyelds.micropython "$program" board.py -o dist --mpy --prune
mkdir -p dist/phyelds  # a program without phyelds (hello_world.py) gets no folder from the build
uv run mpremote rm -r :phyelds 2>/dev/null || true  # old .py files would be imported before the .mpy ones
uv run mpremote mip install ssd1306 + cp -r dist/phyelds : + cp board.py : + cp "dist/$name.py" :main.py + reset
