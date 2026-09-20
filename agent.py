"""
SUPER SIMPLE INTELLIGENT AGENT
--------------------------------
This one file does everything:
  - describe the situation (is the heart rate risky? changing fast?)
  - keep a "scoreboard" of which speed level worked well in each situation
  - pick a speed level, then learn from what happens next
  - a fake patient, so you can test this without a real sensor

Run it:
    python agent.py practice        <- no hardware needed
    python agent.py live COM3       <- talk to a real Arduino
"""

import random
import sys
import time

SPEED_NAMES = ["SLOW", "MEDIUM", "FAST", "URGENT"]

# The "scoreboard": for every situation we've seen, a list of 4 numbers
# (one score per speed level). Higher score = agent thinks this speed
# level works well in this situation.
scores = {}


# ---------------------------------------------------------------- brain --
def describe_situation(heart_rate, previous_heart_rate):
    """Turn the raw heart rate into a simple, easy-to-read category."""
    if heart_rate == 0:
        risk = "unknown"
    elif heart_rate > 140 or heart_rate < 40:
        risk = "critical"
    elif heart_rate > 110 or heart_rate < 55:
        risk = "elevated"
    elif heart_rate > 95:
        risk = "watch"
    else:
        risk = "stable"

    changing_fast = abs(heart_rate - previous_heart_rate) > 3
    trend = "changing" if changing_fast else "steady"

    return risk + "_" + trend      # e.g. "watch_changing"


def get_scores(situation):
    """Look up the scoreboard for this situation. Make one if it's new."""
    if situation not in scores:
        # Start with a reasonable guess instead of zeros, so the agent
        # isn't clueless the very first time it sees a new situation.
        if situation.startswith("critical"):
            guess = 3
        elif situation.startswith("elevated") or situation.startswith("unknown"):
            guess = 2
        elif situation.startswith("watch"):
            guess = 1
        else:
            guess = 0
        scores[situation] = [0.0, 0.0, 0.0, 0.0]
        scores[situation][guess] = 1.0
    return scores[situation]


def choose_speed(situation, explore_chance=0.2):
    """Pick a speed level: usually the best-known one, sometimes a random try."""
    row = get_scores(situation)

    if random.random() < explore_chance:
        speed = random.randint(0, 3)
    else:
        speed = row.index(max(row))

    # SAFETY RULE -- this always wins, no matter what the scoreboard says.
    if situation.startswith("critical") and speed < 3:
        speed = 3
    elif (situation.startswith("elevated") or situation.startswith("unknown")) and speed < 2:
        speed = 2

    return speed


def learn(situation, speed_used, event_happened):
    """After seeing what happened, nudge the scoreboard up or down."""
    row = get_scores(situation)

    reward = 0.0
    if event_happened and speed_used < 2:
        reward -= 10.0                       # bad: too slow during a real event
    elif event_happened:
        reward += 2.0                        # good: kept up with a real event
    else:
        reward += (3 - speed_used) * 0.3     # good: saved battery, nothing wrong

    learning_rate = 0.2
    row[speed_used] = row[speed_used] + learning_rate * (reward - row[speed_used])


def print_scoreboard():
    print(f"\n{'Situation':<20} {'Best speed':<10}")
    print("-" * 32)
    for situation in sorted(scores):
        row = scores[situation]
        best = row.index(max(row))
        print(f"{situation:<20} {SPEED_NAMES[best]:<10}")


# ------------------------------------------------------------- practice --
def practice_mode():
    """Test the agent against a made-up patient. No hardware needed."""
    heart_rate = 72
    target = 72
    ticks_left = 60
    battery = 100.0
    previous_heart_rate = 72

    print("Running 600 seconds of practice...\n")

    for second in range(600):
        # -- fake patient: drifts toward a target heart rate --
        ticks_left -= 1
        if ticks_left <= 0:
            ticks_left = random.randint(30, 90)
            if random.random() < 0.15:
                target = random.randint(130, 170)   # occasional risky spike
            else:
                target = random.randint(65, 85)      # usually calm
        heart_rate += (target - heart_rate) * 0.1 + random.gauss(0, 1)
        heart_rate = max(30, min(200, heart_rate))
        event_happened = heart_rate > 130 or heart_rate < 45

        # -- the agent's turn --
        situation = describe_situation(round(heart_rate), previous_heart_rate)
        speed = choose_speed(situation)
        battery -= [0.002, 0.004, 0.008, 0.015][speed]
        learn(situation, speed, event_happened)

        previous_heart_rate = round(heart_rate)

        if second % 60 == 0:
            flag = "  ** EVENT **" if event_happened else ""
            print(f"t={second:4d}s  HR={heart_rate:5.1f}  speed={SPEED_NAMES[speed]:<7}"
                  f"  battery={battery:5.1f}%{flag}")

    print_scoreboard()


# ------------------------------------------------------------------ live --
def live_mode(port):
    """Talk to a real Arduino over USB."""
    import serial   # pip install pyserial

    ser = serial.Serial(port, 115200, timeout=1)
    time.sleep(2)   # let the Arduino finish resetting

    previous_heart_rate = 0
    current_speed_sent = -1

    print(f"Connected to {port}. Press Ctrl+C to stop.\n")

    try:
        while True:
            line = ser.readline().decode(errors="ignore").strip()
            if not line.startswith("DATA,"):
                if line:
                    print("  [arduino]", line)
                continue

            # Format: DATA,heartRate,leadOff,speedLevel
            parts = line.split(",")
            heart_rate = int(parts[1])
            lead_off = parts[2] == "1"

            situation = describe_situation(heart_rate, previous_heart_rate)
            speed = choose_speed(situation)
            if lead_off:
                speed = max(speed, 1)   # never go fully slow with a loose sensor

            if speed != current_speed_sent:
                ser.write(str(speed).encode())
                current_speed_sent = speed

            print(f"HR={heart_rate:3d}  situation={situation:<18} -> {SPEED_NAMES[speed]}"
                  f"{'  (lead off!)' if lead_off else ''}")

            previous_heart_rate = heart_rate

    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        ser.close()


# ------------------------------------------------------------------ main --
if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "practice":
        practice_mode()
    elif len(sys.argv) >= 3 and sys.argv[1] == "live":
        live_mode(sys.argv[2])
    else:
        print("Usage:")
        print("  python agent.py practice")
        print("  python agent.py live COM3")
