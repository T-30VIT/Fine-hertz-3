# Wiring Guide

## What you need

- Arduino Uno or Nano (any AVR-based board with a USB port that
  shows up directly in the Arduino IDE's Tools → Port menu)
- AD8232 heart rate monitor module
- 3-lead ECG cable + sticky electrode pads (comes with most AD8232 kits)
- Jumper wires
- USB cable (whatever your Arduino board uses — no separate
  programmer/debugger needed for a standard Arduino)

## AD8232 → Arduino

| AD8232 pin | Arduino pin | Purpose |
|---|---|---|
| GND | GND | common ground |
| 3.3V | 3.3V | power (not 5V) |
| OUTPUT | A0 | analog ECG signal |
| LO+ | Pin 2 | tells us if a pad fell off |
| LO− | *(unused)* | not read by this firmware |
| SDN | *(unused)* | shutdown pin, not needed |

Four wires total: GND, 3.3V, OUTPUT, LO+.

If you wire A0 or Pin 2 differently, update `sensorPin` and
`leadOffPin` at the top of `firmware/firmware.ino` to match.

## Electrode cable → body

| Lead | Placement |
|---|---|
| RA (right arm) | below right collarbone |
| LA (left arm) | below left collarbone |
| RL (right leg) | lower right ribcage (reference/ground) |

For a quick bench test, exact placement doesn't matter much — two
pads on your forearms and one anywhere else on your torso will
usually pick up a usable signal.

## Do I need an ST-Link?

No, not for a standard Arduino Uno/Nano. ST-Link is a separate
programmer used for STM32-based boards, which use a different debug
interface (SWD) instead of plain USB-serial. A standard Arduino
programs, powers, and communicates entirely over its single USB
cable.

Quick check: plug the board in, open the Arduino IDE, and look at
**Tools → Port**. If a port appears and you can select a board like
"Arduino Uno" or "Arduino Nano" under **Tools → Board**, you're on a
standard Arduino and don't need anything else.

## After wiring

1. Open `firmware/firmware.ino` in the Arduino IDE and upload it.
2. Open Serial Monitor at **115200 baud** — you should see `Ready`
   followed by `DATA,...` lines.
3. Close Serial Monitor (only one program can hold the port at a
   time), then run the host agent — see the main [README](../README.md).
