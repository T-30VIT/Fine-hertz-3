# How It Works

## The problem, in one line

An embedded heart monitor has a limited battery. Checking the sensor
at full speed all the time wastes power when the patient is fine, but
checking too slowly risks missing a real problem. This project makes
the checking speed itself a decision, instead of a fixed number.

## Hardware flow (`firmware/firmware.ino`)

```
        ┌─────────────────────────────────────────────┐
        │                  loop()                      │
        │                                               │
   ┌───▶│ 1. Listen for a new speed level from computer │
   │    │ 2. If it's time, read the sensor,             │
   │    │    detect a heartbeat, update heart rate       │
   │    │ 3. If heart rate is dangerous, escalate        │
   │    │    speed on its own (doesn't wait for host)   │
   │    │ 4. If it's time, send heart rate + speed       │
   │    │    level to the computer over serial           │
   └────┴─────────────────────────────────────────────┘
```

Four speed levels control how often the sensor is checked and how
often data is sent:

| Level | Name | Check every | Send every |
|---|---|---|---|
| 0 | SLOW | 1000 ms | 10 s |
| 1 | MEDIUM | 40 ms | 2 s |
| 2 | FAST | 10 ms | 1 s |
| 3 | URGENT | 4 ms | 250 ms |

## Software flow (`agent/agent.py`)

```
   serial line arrives: "DATA,heartRate,leadOff,speedLevel"
                    │
                    ▼
        describe_situation(heart rate, previous heart rate)
          → a short label like "watch_changing"
                    │
                    ▼
        choose_speed(situation)
          → look up the scoreboard for this situation
          → usually pick the best-known speed,
            occasionally try a random one to keep learning
          → SAFETY RULE always wins: critical → URGENT,
            elevated/unknown → at least FAST
                    │
                    ▼
        send the chosen speed level back to the Arduino
                    │
                    ▼
        learn(situation, speed used, did something risky happen?)
          → nudge that situation's score up or down
```

The "brain" is a single Python dictionary called `scores`. Each key
is a situation label; each value is a list of 4 numbers, one per
speed level. Higher number = the agent believes that speed level
works well in that situation. This is a basic form of reinforcement
learning (Q-learning): try things, see what happens, remember what
worked.

## The one rule that can't be learned away

Regardless of what the scoreboard says, `choose_speed()` always
forces:

- **critical** situations → URGENT (level 3)
- **elevated** or **unknown** situations → at least FAST (level 2)

This means the agent is free to experiment and be wrong about
everything else, but it can never learn its way into ignoring a
dangerous heart rate.

## Known limitation

There's no real blood pressure sensor in this kit, so no BP is
measured or estimated anywhere in this version — heart rate is the
only vital sign tracked. That's a deliberate, honest simplification
rather than a fake number: a real BP reading would need either a
cuff or a second pulse sensor (for pulse transit time), neither of
which is part of this hardware.
