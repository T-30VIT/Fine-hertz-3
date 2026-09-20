# Adaptive Biomedical Monitoring

**A heart monitor that learns when to watch closely — and when it's
safe to save the battery.**

Built for [hackathon name] · Team [team name]

---

## The problem

Embedded patient monitors have limited battery, processing, and
communication resources. A fixed sampling rate is always wrong in
one direction: too aggressive when the patient is stable (wasting
energy), or too slow to catch a deterioration the moment it starts.

## The solution

This project makes the sampling rate itself a decision. An Arduino
with a heart-rate sensor reports to a small Python agent that:

1. turns the raw heart rate into a simple situation (how risky does
   it look, is it changing fast?),
2. picks one of four checking speeds based on what has worked in
   that situation before, and
3. learns from the outcome — good decisions get reinforced, bad ones
   get corrected.

A hard safety rule sits on top of the learning: a dangerous heart
rate always forces the fastest checking speed, no matter what the
learned policy says. Full explanation in
[`docs/HOW_IT_WORKS.md`](docs/HOW_IT_WORKS.md).

## Repository layout

```
firmware/firmware.ino   Arduino code — reads the sensor, detects
                         heartbeats, escalates on its own if the
                         reading looks dangerous
agent/agent.py           Python host agent — decides the checking
                         speed, learns from outcomes, and can run
                         with either a real Arduino or a built-in
                         fake patient for testing
agent/graph.py            Live scrolling graph of heart rate, with
                         the background colored by the current
                         speed level — see "Live graph" below
docs/WIRING.md            full wiring guide
docs/HOW_IT_WORKS.md      flowcharts + explanation of the logic
slides/                   hackathon presentation deck (.pptx)
```

## Live graph

Two ways to see the heartbeat visually, instead of just numbers in
a terminal:

**Instant, zero setup** — the firmware prints the raw sensor value
every reading, so Arduino's built-in plotter works immediately:
open the sketch in Arduino IDE, upload it, then
**Tools → Serial Plotter**. You'll see the raw ECG waveform scroll by.

**Full dashboard** — `agent/graph.py` plots heart rate over time
with the background shaded by whichever speed tier the agent is
currently using, so you can *see* the adaptive behavior during a
demo:
```bash
pip install matplotlib pyserial
python3 agent/graph.py practice        # fake patient, no hardware
python3 agent/graph.py live COM3       # real Arduino
```

## Quickstart — no hardware needed

```bash
python3 agent/agent.py practice
```

Runs 600 seconds of simulated patient data against the learning
agent and prints what it learned at the end.

## Quickstart — with real hardware

1. Wire the AD8232 sensor to the Arduino — see
   [`docs/WIRING.md`](docs/WIRING.md) for the full pinout.
2. Flash `firmware/firmware.ino` using the Arduino IDE.
3. Install the one dependency needed for live mode:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the agent against the real board:
   ```bash
   python3 agent/agent.py live COM3
   ```
   (swap `COM3` for your board's actual port — `/dev/ttyUSB0` or
   similar on Mac/Linux)

## What's built and tested

- [x] Firmware: reads sensor, detects heartbeats, sends data over serial
- [x] Firmware: local safety escalation — speeds up on its own if HR looks dangerous
- [x] Firmware: listens for speed commands from the host
- [x] Agent: situation → scoreboard → speed decision
- [x] Agent: learns from outcomes (basic Q-learning)
- [x] Agent: safety rule that always overrides the learned scoreboard
- [x] Practice mode — runs end-to-end with a simulated patient, no hardware
- [x] Live mode — tested against real Arduino + AD8232 hardware

## Known limitations

- **No blood pressure.** This kit has an ECG sensor only. Real BP
  needs a cuff, or a second pulse sensor for pulse-transit-time
  estimation — out of scope for this build. See the note in
  `docs/HOW_IT_WORKS.md`.
- **Simple beat detector.** The heartbeat detection is a basic
  threshold crossing, not a clinical-grade algorithm — good enough
  to demonstrate adaptive sampling, not for real diagnosis.
- **Learning starts cold each run.** The scoreboard isn't saved to
  disk between runs in this simple version, so every `practice` or
  `live` session starts fresh.

## License

MIT — see [`LICENSE`](LICENSE). Not a medical device; a hackathon
prototype only.
