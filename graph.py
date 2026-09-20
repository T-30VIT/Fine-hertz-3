"""
LIVE GRAPH -- real-time heart rate display
--------------------------------------------
Shows a scrolling line graph of your heart rate as it comes in from
the Arduino, with the background colored by which speed level the
agent is currently using. This is meant to run ALONGSIDE agent.py --
agent.py makes the decisions, this just draws a picture of what's
happening.

Run it:
    python graph.py live COM3          <- real Arduino
    python graph.py practice           <- fake patient, no hardware

Needs matplotlib (for the graph) and pyserial (for live mode only):
    pip install matplotlib pyserial
"""

import random
import sys
import time
from collections import deque

import matplotlib.pyplot as plt
import matplotlib.animation as animation

# import the brain from agent.py so the two files always agree on
# how decisions get made
from agent import describe_situation, choose_speed, learn, SPEED_NAMES

HISTORY_SECONDS = 60          # how much time the graph shows at once
TIER_COLORS = ["#2ecc71", "#f1c40f", "#e67e22", "#e74c3c"]   # slow -> urgent


def make_plot():
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.set_title("Live Heart Rate  --  background color = current speed level")
    ax.set_xlabel("seconds ago")
    ax.set_ylabel("heart rate (bpm)")
    ax.set_xlim(-HISTORY_SECONDS, 0)
    ax.set_ylim(30, 200)
    line, = ax.plot([], [], color="black", linewidth=1.6)

    # a legend so the colors are easy to read
    for i, name in enumerate(SPEED_NAMES):
        ax.plot([], [], color=TIER_COLORS[i], linewidth=8, label=name)
    ax.legend(loc="upper right", fontsize=8)

    return fig, ax, line


def run(get_next_reading):
    """
    get_next_reading() must return (heart_rate, speed_level) each time
    it's called -- either from the real Arduino or the fake patient.
    """
    fig, ax, line = make_plot()
    times = deque()
    values = deque()
    shading = []   # list of (start_time, end_time, color) rectangles
    t = 0.0

    def update(_frame):
        nonlocal t
        heart_rate, speed = get_next_reading()
        if heart_rate is None:
            return line,

        t += 1
        times.append(t)
        values.append(heart_rate)
        while times and (t - times[0]) > HISTORY_SECONDS:
            times.popleft()
            values.popleft()

        # shade the background strip for this second with the tier color
        for patch in ax.patches[:]:
            patch.remove()
        shading.append((t, TIER_COLORS[speed]))
        shading[:] = [(st, c) for st, c in shading if (t - st) <= HISTORY_SECONDS]
        for i in range(len(shading)):
            st, c = shading[i]
            ax.axvspan(st - t - 1, st - t, color=c, alpha=0.15, lw=0)

        line.set_data([x - t for x in times], values)
        ax.set_xlim(-HISTORY_SECONDS, 0)
        return line,

    ani = animation.FuncAnimation(fig, update, interval=200, blit=False, cache_frame_data=False)
    plt.tight_layout()
    plt.show()


# ------------------------------------------------------------- practice --
def practice_source():
    """Fake patient, same behavior as agent.py's practice mode."""
    state = {"hr": 72.0, "target": 72.0, "ticks_left": 60, "prev": 72}

    def get_next_reading():
        state["ticks_left"] -= 1
        if state["ticks_left"] <= 0:
            state["ticks_left"] = random.randint(30, 90)
            if random.random() < 0.15:
                state["target"] = random.randint(130, 170)
            else:
                state["target"] = random.randint(65, 85)
        state["hr"] += (state["target"] - state["hr"]) * 0.1 + random.gauss(0, 1)
        state["hr"] = max(30, min(200, state["hr"]))
        heart_rate = round(state["hr"])
        event_happened = heart_rate > 130 or heart_rate < 45

        situation = describe_situation(heart_rate, state["prev"])
        speed = choose_speed(situation)
        learn(situation, speed, event_happened)
        state["prev"] = heart_rate

        time.sleep(0.15)   # slow the loop down so the graph is watchable
        return heart_rate, speed

    return get_next_reading


# ------------------------------------------------------------------ live --
def live_source(port):
    import serial   # pip install pyserial
    ser = serial.Serial(port, 115200, timeout=1)
    time.sleep(2)
    state = {"prev": 0, "current_speed_sent": -1}

    def get_next_reading():
        line = ser.readline().decode(errors="ignore").strip()
        if not line.startswith("DATA,"):
            return None, None
        parts = line.split(",")
        heart_rate = int(parts[1])

        situation = describe_situation(heart_rate, state["prev"])
        speed = choose_speed(situation)
        if speed != state["current_speed_sent"]:
            ser.write(str(speed).encode())
            state["current_speed_sent"] = speed
        state["prev"] = heart_rate

        return heart_rate, speed

    return get_next_reading


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "practice":
        run(practice_source())
    elif len(sys.argv) >= 3 and sys.argv[1] == "live":
        run(live_source(sys.argv[2]))
    else:
        print("Usage:")
        print("  python graph.py practice")
        print("  python graph.py live COM3")
