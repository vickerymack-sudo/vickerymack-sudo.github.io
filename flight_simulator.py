#!/usr/bin/env python3
"""Visual flight simulator with emergency scenario gameplay.

This is a lightweight 2D simulator inspired by cockpit/attitude visuals.
It is not a full 3D simulator like Microsoft Flight Simulator, but it provides
real-time controls, instrumentation, and emergency handling in a visual window.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass

try:
    import tkinter as tk
except Exception:  # pragma: no cover - environment-specific import
    tk = None


@dataclass
class FlightState:
    time_s: float = 0.0
    distance_nm: float = 60.0
    altitude_ft: float = 12000.0
    speed_kts: float = 240.0
    heading_deg: float = 270.0

    throttle: float = 62.0
    pitch_deg: float = 0.0
    bank_deg: float = 0.0
    flaps: int = 0
    gear_down: bool = False

    engine1_on: bool = True
    engine2_on: bool = True
    engine2_fire: bool = False
    smoke_level: float = 0.0

    emergency_declared: bool = False
    fire_bottle_used: bool = False
    oxygen_on: bool = False

    score: int = 0
    game_over: bool = False
    landed: bool = False
    message: str = ""


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def norm_heading(heading: float) -> float:
    x = heading % 360.0
    return x if x > 0 else 360.0


def heading_delta(current: float, target: float) -> float:
    return (target - current + 540.0) % 360.0 - 180.0


class SimulatorCore:
    def __init__(self) -> None:
        self.state = FlightState()
        self.airport_heading = 270.0

    def incident_logic(self) -> None:
        s = self.state
        t = s.time_s
        if 20.0 < t <= 20.2:
            s.message = "ENG2 OIL PRESS LOW: smoke trail observed."
            s.score -= 2
        if 50.0 < t <= 50.2 and s.engine2_on:
            s.engine2_fire = True
            s.smoke_level = max(1.0, s.smoke_level)
            s.message = "ENGINE 2 FIRE WARNING!"
        if 90.0 < t <= 90.2:
            s.smoke_level = max(1.0, s.smoke_level)
            s.message = "CABIN: smoke increasing. Descend + oxygen."

    def step(self, dt: float) -> None:
        s = self.state
        if s.game_over:
            return

        s.time_s += dt
        self.incident_logic()

        engines_on = int(s.engine1_on) + int(s.engine2_on)

        if s.engine2_fire:
            s.smoke_level = clamp(s.smoke_level + 0.01 * dt * 60, 0.0, 2.0)
            s.score -= 1
            if s.time_s > 180 and s.engine2_on:
                s.game_over = True
                s.message = "Uncontained engine failure. Flight lost."
                return

        effective_thrust = s.throttle
        if engines_on == 1:
            effective_thrust -= 18
        elif engines_on == 0:
            effective_thrust = 0

        effective_thrust -= s.flaps * 4
        if s.gear_down:
            effective_thrust -= 10

        # Turn dynamics from bank
        yaw_rate_dps = s.bank_deg * 0.07
        s.heading_deg = norm_heading(s.heading_deg + yaw_rate_dps * dt)

        # Speed dynamics
        accel = (effective_thrust - 52) * 0.04 - abs(s.bank_deg) * 0.02 - s.pitch_deg * 0.05
        s.speed_kts = clamp(s.speed_kts + accel * dt, 110, 360)

        # Vertical dynamics
        climb_fpm = s.pitch_deg * 700 + (s.throttle - 55) * 18
        if engines_on == 1:
            climb_fpm -= 700
        if engines_on == 0:
            climb_fpm -= 2500
        if s.flaps >= 2:
            climb_fpm -= 400
        if s.gear_down:
            climb_fpm -= 500
        s.altitude_ft = clamp(s.altitude_ft + (climb_fpm / 60.0) * dt, 0, 41000)

        # Distance closure
        bearing_penalty = abs(heading_delta(s.heading_deg, self.airport_heading)) / 120.0
        closure_nm_s = max(0.003, (s.speed_kts / 3600.0) - bearing_penalty * 0.01)
        s.distance_nm = max(0.0, s.distance_nm - closure_nm_s * dt)

        # Smoke effects
        if s.smoke_level > 1.2 and not s.oxygen_on:
            s.score -= 1
            if s.altitude_ft > 10000:
                s.message = "Heavy smoke. Use oxygen and descend."

        # Landing and crash checks
        if s.distance_nm <= 0.25 and s.altitude_ft <= 60:
            self.evaluate_landing()
        elif s.altitude_ft <= 0 and not s.landed:
            s.game_over = True
            s.message = "Terrain impact."

    def evaluate_landing(self) -> None:
        s = self.state
        aligned = abs(heading_delta(s.heading_deg, self.airport_heading)) <= 20
        stable_speed = 120 <= s.speed_kts <= 165
        configured = s.gear_down and s.flaps >= 2

        if aligned and stable_speed and configured:
            s.landed = True
            s.game_over = True
            s.score += 30
            s.message = "Safe emergency landing completed."
        else:
            s.game_over = True
            s.score -= 30
            s.message = "Crash landing: unstable approach."

    def command_fire_bottle(self) -> None:
        s = self.state
        if s.engine2_fire and not s.fire_bottle_used:
            s.engine2_fire = False
            s.fire_bottle_used = True
            s.score += 12
            s.message = "Fire bottle discharged, warning extinguished."
        elif s.fire_bottle_used:
            s.message = "Fire bottle already used."
        else:
            s.message = "No active engine fire."

    def command_shutdown_engine2(self) -> None:
        s = self.state
        if s.engine2_on:
            s.engine2_on = False
            s.score += 6
            s.message = "Engine 2 shutdown complete."
        else:
            s.message = "Engine 2 already off."


class VisualFlightSim:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.core = SimulatorCore()
        self.state = self.core.state

        self.root.title("Verbal Flight Simulator - Visual Emergency Mode")
        self.canvas = tk.Canvas(root, width=1024, height=640, bg="#10151d")
        self.canvas.pack(fill="both", expand=True)

        self.root.bind("<KeyPress>", self.on_key)
        self.running = True

        self.info = (
            "Controls: W/S throttle | Up/Down pitch | Left/Right bank | "
            "F flaps | G gear | M mayday | E shutdown ENG2 | B fire bottle | O oxygen | Q quit"
        )

        self.loop()

    def on_key(self, event: tk.Event) -> None:
        k = event.keysym.lower()
        s = self.state

        if k == "w":
            s.throttle = clamp(s.throttle + 3, 0, 100)
        elif k == "s":
            s.throttle = clamp(s.throttle - 3, 0, 100)
        elif k == "up":
            s.pitch_deg = clamp(s.pitch_deg + 1, -10, 15)
        elif k == "down":
            s.pitch_deg = clamp(s.pitch_deg - 1, -10, 15)
        elif k == "left":
            s.bank_deg = clamp(s.bank_deg - 3, -35, 35)
        elif k == "right":
            s.bank_deg = clamp(s.bank_deg + 3, -35, 35)
        elif k == "space":
            s.bank_deg *= 0.5
            s.pitch_deg *= 0.8
        elif k == "f":
            s.flaps = (s.flaps + 1) % 4
        elif k == "g":
            s.gear_down = not s.gear_down
        elif k == "m":
            if not s.emergency_declared:
                s.emergency_declared = True
                s.score += 8
                s.message = "MAYDAY declared. Direct to nearest airport."
            else:
                s.message = "MAYDAY already active."
        elif k == "e":
            self.core.command_shutdown_engine2()
        elif k == "b":
            self.core.command_fire_bottle()
        elif k == "o":
            s.oxygen_on = not s.oxygen_on
            s.message = f"Oxygen {'ON' if s.oxygen_on else 'OFF'}."
        elif k == "q":
            self.running = False
            self.root.destroy()

    def draw(self) -> None:
        c = self.canvas
        s = self.state
        w = int(c.winfo_width())
        h = int(c.winfo_height())
        c.delete("all")

        cx = w // 2
        cy = h // 2

        # Sky/ground artificial horizon
        horizon_offset = int(s.pitch_deg * 10)
        horizon_y = cy + horizon_offset
        sky_color = "#4b87d8"
        ground_color = "#6b4f2f"
        c.create_rectangle(0, 0, w, horizon_y, fill=sky_color, outline="")
        c.create_rectangle(0, horizon_y, w, h, fill=ground_color, outline="")

        # Banked horizon line
        bank_rad = math.radians(s.bank_deg)
        line_len = 1400
        dx = math.cos(bank_rad) * line_len
        dy = math.sin(bank_rad) * line_len
        c.create_line(cx - dx, horizon_y - dy, cx + dx, horizon_y + dy, fill="white", width=3)

        # Runway cue appears when close
        if s.distance_nm < 8:
            rw_w = max(30, int(280 * (8 - s.distance_nm) / 8))
            rw_h = max(20, int(140 * (8 - s.distance_nm) / 8))
            rcy = horizon_y + 140
            c.create_polygon(
                cx - rw_w,
                rcy + rw_h,
                cx + rw_w,
                rcy + rw_h,
                cx + rw_w // 3,
                rcy,
                cx - rw_w // 3,
                rcy,
                fill="#2f2f2f",
                outline="white",
            )

        # Aircraft reference symbol
        c.create_line(cx - 50, cy, cx + 50, cy, fill="#00ff66", width=3)
        c.create_line(cx, cy - 15, cx, cy + 15, fill="#00ff66", width=3)

        # HUD text
        warn = ""
        if s.engine2_fire:
            warn = " ENGINE2 FIRE"
        elif s.smoke_level > 1.1:
            warn = " HEAVY SMOKE"

        c.create_text(
            15,
            15,
            anchor="nw",
            fill="white",
            font=("Consolas", 14, "bold"),
            text=(
                f"SPD {int(s.speed_kts):03d}kt   ALT {int(s.altitude_ft):05d}ft   "
                f"HDG {int(s.heading_deg):03d}   DIST {s.distance_nm:04.1f}nm{warn}"
            ),
        )
        c.create_text(
            15,
            42,
            anchor="nw",
            fill="#d7f0ff",
            font=("Consolas", 12),
            text=(
                f"THR {int(s.throttle):02d}%  PITCH {s.pitch_deg:+.1f}°  BANK {s.bank_deg:+.1f}°  "
                f"FLAPS {s.flaps}  GEAR {'DOWN' if s.gear_down else 'UP'}  O2 {'ON' if s.oxygen_on else 'OFF'}"
            ),
        )

        c.create_text(15, h - 45, anchor="nw", fill="#9cc0d8", font=("Consolas", 11), text=self.info)
        c.create_text(15, h - 24, anchor="nw", fill="#fff7a8", font=("Consolas", 11), text=f"MSG: {s.message}")

        # End overlay
        if s.game_over:
            overlay = "SUCCESSFUL EMERGENCY LANDING" if s.landed else "FLIGHT LOST"
            c.create_rectangle(0, 0, w, h, fill="#000000", stipple="gray50", outline="")
            c.create_text(cx, cy - 20, fill="white", font=("Consolas", 30, "bold"), text=overlay)
            c.create_text(
                cx,
                cy + 20,
                fill="#f5f5f5",
                font=("Consolas", 16),
                text=f"Score: {s.score} | Time: {int(s.time_s)}s | Press Q to quit",
            )

    def loop(self) -> None:
        if not self.running:
            return

        self.core.step(0.1)
        self.draw()
        self.root.after(100, self.loop)


def run_text_demo(seconds: int = 20) -> None:
    """Headless demo mode for environments without GUI."""
    sim = SimulatorCore()
    s = sim.state

    # Autopilot-ish setup so CI/headless can validate core logic
    s.emergency_declared = True
    for i in range(seconds * 10):
        if s.time_s > 52 and s.engine2_on:
            sim.command_shutdown_engine2()
            sim.command_fire_bottle()
        if s.altitude_ft > 3000:
            s.pitch_deg = -4
            s.throttle = 50
        else:
            s.pitch_deg = -1
            s.throttle = 45
            s.flaps = 2
            s.gear_down = True
        sim.step(0.1)
        if s.game_over:
            break
        if i % 20 == 0:
            print(
                f"t={s.time_s:5.1f}s alt={s.altitude_ft:7.0f}ft spd={s.speed_kts:6.1f}kt "
                f"dist={s.distance_nm:5.2f}nm fire={s.engine2_fire} msg={s.message}"
            )

    print(
        f"END landed={s.landed} lost={s.game_over and not s.landed} "
        f"score={s.score} alt={s.altitude_ft:.0f} dist={s.distance_nm:.2f}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Visual emergency flight simulator")
    parser.add_argument("--demo", action="store_true", help="run headless text demo")
    parser.add_argument("--demo-seconds", type=int, default=20, help="seconds for demo mode")
    args = parser.parse_args()

    if args.demo:
        run_text_demo(args.demo_seconds)
        return

    if tk is None:
        print("Tkinter is not available in this environment. Try: python3 flight_simulator.py --demo")
        return

    root = tk.Tk()
    VisualFlightSim(root)
    root.mainloop()


if __name__ == "__main__":
    main()
