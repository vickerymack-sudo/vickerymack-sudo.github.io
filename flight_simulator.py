#!/usr/bin/env python3
"""Interactive text flight simulator with emergency incidents.

You actively fly the aircraft using control commands while handling failures.
"""

from dataclasses import dataclass


@dataclass
class FlightState:
    time_min: int = 0
    distance_nm: float = 110.0
    altitude_ft: int = 32000
    speed_kts: int = 290
    heading_deg: int = 270

    throttle: int = 68
    pitch_cmd: int = 0  # -2 descend, -1 slight descend, 0 hold, 1 climb, 2 steep climb
    flaps: int = 0
    gear_down: bool = False

    engine1_on: bool = True
    engine2_on: bool = True
    engine2_fire: bool = False
    smoke_level: int = 0  # 0 none, 1 light, 2 heavy

    airport_heading_deg: int = 270
    emergency_declared: bool = False
    fire_bottle_used: bool = False

    score: int = 0
    game_over: bool = False
    landed: bool = False


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def normalize_heading(heading: int) -> int:
    value = heading % 360
    return value if value != 0 else 360


def heading_delta(current: int, target: int) -> int:
    raw = (target - current + 540) % 360 - 180
    return raw


def print_hud(state: FlightState) -> None:
    print("\n" + "=" * 70)
    print(
        f"T+{state.time_min:02d}m | DIST {state.distance_nm:05.1f}nm | ALT {state.altitude_ft:05d}ft "
        f"| SPD {state.speed_kts:03d}kt | HDG {state.heading_deg:03d}"
    )
    print(
        f"THR {state.throttle:02d}% | PITCH {state.pitch_cmd:+d} | FLAPS {state.flaps} "
        f"| GEAR {'DOWN' if state.gear_down else 'UP'}"
    )
    print(
        f"ENG1 {'ON' if state.engine1_on else 'OFF'} | ENG2 {'ON' if state.engine2_on else 'OFF'} "
        f"| FIRE2 {'YES' if state.engine2_fire else 'NO'} | SMOKE {state.smoke_level}"
    )
    print(f"ATC airport bearing {state.airport_heading_deg:03d}° | Score {state.score}")


def print_help() -> None:
    print(
        """
Commands:
  status                     show current aircraft state
  help                       show commands
  throttle <0-100>           set throttle
  pitch <-2..2>              set vertical control
  turn <L/R> <degrees>       turn heading (example: turn L 20)
  flaps <0|1|2|3>            set flaps
  gear up|down               landing gear control
  declare mayday             declare emergency for score bonus
  fire bottle                discharge extinguisher on engine 2 fire
  shutdown eng2              shutdown engine 2
  oxygen on                  cockpit oxygen masks on (helps with smoke)
  tick                       hold current controls for one minute
"""
    )


def incident_brief(state: FlightState) -> None:
    if state.time_min == 1:
        print("\nALERT: ENG2 OIL PRESS LOW. You see a thin smoke trail from engine 2.")
        state.score -= 2
    if state.time_min == 3 and state.engine2_on:
        print("\nALERT: Smoke worsens and ENG2 FIRE warning activates.")
        state.engine2_fire = True
        state.smoke_level = max(state.smoke_level, 1)
    if state.time_min == 5:
        print("\nCABIN REPORT: Smoke entering cabin. Immediate handling required.")
        state.smoke_level = max(state.smoke_level, 1)


def apply_flight_physics(state: FlightState) -> None:
    engine_count = int(state.engine1_on) + int(state.engine2_on)

    # Fire progression
    if state.engine2_fire:
        state.smoke_level = min(2, state.smoke_level + 1)
        state.score -= 4
        if state.time_min >= 9 and state.engine2_on:
            print("\nCRITICAL: Engine 2 suffers uncontained failure due to prolonged fire.")
            state.game_over = True
            return

    # Thrust model
    base_thrust = state.throttle
    if engine_count == 1:
        base_thrust -= 18
    elif engine_count == 0:
        base_thrust = 0

    if state.flaps > 0:
        base_thrust -= state.flaps * 4
    if state.gear_down:
        base_thrust -= 10

    # Speed update
    speed_change = (base_thrust - 55) // 5 - state.pitch_cmd * 3
    state.speed_kts = clamp(state.speed_kts + speed_change, 120, 360)

    # Altitude update
    climb_rate_fpm = state.pitch_cmd * 900 + max(0, (state.throttle - 55) * 12) - 350
    if engine_count == 1:
        climb_rate_fpm -= 600
    if engine_count == 0:
        climb_rate_fpm -= 2000

    if state.flaps >= 2:
        climb_rate_fpm -= 400
    if state.gear_down:
        climb_rate_fpm -= 500

    state.altitude_ft = clamp(state.altitude_ft + climb_rate_fpm, 0, 41000)

    # Distance closure (rough)
    turn_penalty = abs(heading_delta(state.heading_deg, state.airport_heading_deg)) / 90
    closure = max(0.2, state.speed_kts / 130 - turn_penalty)
    state.distance_nm = max(0.0, state.distance_nm - closure)

    # Operational risks
    if state.smoke_level == 2 and state.altitude_ft > 12000:
        print("\nWARNING: Heavy smoke at high altitude. Descend and use oxygen.")
        state.score -= 3

    if state.gear_down and state.speed_kts > 220:
        print("\nDAMAGE: Gear overspeed! Structural stress increased.")
        state.score -= 8

    if state.altitude_ft < 1000 and state.speed_kts < 135 and not state.landed:
        print("\nSTALL WARNING near ground.")
        state.score -= 10

    # Landing check
    if state.distance_nm <= 0.6 and state.altitude_ft <= 80:
        evaluate_landing(state)

    # Crash checks
    if state.altitude_ft == 0 and not state.landed:
        print("\nIMPACT: uncontrolled contact with terrain.")
        state.game_over = True


def evaluate_landing(state: FlightState) -> None:
    stable = (
        128 <= state.speed_kts <= 170
        and state.flaps >= 2
        and state.gear_down
        and abs(heading_delta(state.heading_deg, state.airport_heading_deg)) <= 20
    )
    if stable:
        state.landed = True
        state.game_over = True
        state.score += 25
        print("\nTOUCHDOWN: You landed safely at the diversion airport.")
    else:
        state.game_over = True
        state.score -= 25
        print("\nRUNWAY ACCIDENT: Unstable approach caused a crash landing.")


def apply_command(state: FlightState, cmd: str) -> bool:
    """Apply command. Return True if one minute should advance."""
    parts = cmd.strip().lower().split()
    if not parts:
        return False

    if parts[0] == "help":
        print_help()
        return False

    if parts[0] == "status":
        print_hud(state)
        return False

    if parts[0] == "throttle" and len(parts) == 2 and parts[1].isdigit():
        state.throttle = clamp(int(parts[1]), 0, 100)
        return True

    if parts[0] == "pitch" and len(parts) == 2:
        try:
            state.pitch_cmd = clamp(int(parts[1]), -2, 2)
            return True
        except ValueError:
            pass

    if parts[0] == "turn" and len(parts) == 3:
        side = parts[1]
        try:
            degrees = clamp(int(parts[2]), 0, 180)
            if side == "l":
                state.heading_deg = normalize_heading(state.heading_deg - degrees)
                return True
            if side == "r":
                state.heading_deg = normalize_heading(state.heading_deg + degrees)
                return True
        except ValueError:
            pass

    if parts[0] == "flaps" and len(parts) == 2 and parts[1].isdigit():
        state.flaps = clamp(int(parts[1]), 0, 3)
        return True

    if parts[0] == "gear" and len(parts) == 2:
        if parts[1] == "down":
            state.gear_down = True
            return True
        if parts[1] == "up":
            state.gear_down = False
            return True

    if cmd.strip().lower() == "declare mayday":
        if not state.emergency_declared:
            state.emergency_declared = True
            state.score += 8
            print("ATC: MAYDAY received. Cleared direct nearest airport.")
        else:
            print("ATC: Emergency already declared.")
        return True

    if cmd.strip().lower() == "fire bottle":
        if state.engine2_fire and not state.fire_bottle_used:
            state.engine2_fire = False
            state.fire_bottle_used = True
            state.score += 12
            print("Engine 2 fire warning extinguished.")
        elif state.fire_bottle_used:
            print("No fire bottles remaining.")
        else:
            print("No active engine 2 fire.")
        return True

    if cmd.strip().lower() == "shutdown eng2":
        if state.engine2_on:
            state.engine2_on = False
            state.score += 6
            print("Engine 2 shutdown complete.")
            if state.engine2_fire:
                print("Fire intensity reducing after fuel cut-off.")
        else:
            print("Engine 2 already off.")
        return True

    if cmd.strip().lower() == "oxygen on":
        if state.smoke_level > 0:
            state.score += 5
            state.smoke_level = max(0, state.smoke_level - 1)
            print("Crew oxygen masks on. Smoke impact reduced.")
        else:
            print("Oxygen available; no smoke impact currently.")
        return True

    if parts[0] == "tick":
        return True

    print("Unknown command. Type 'help'.")
    return False


def print_summary(state: FlightState) -> None:
    print("\n" + "=" * 70)
    print("FINAL REPORT")
    print(f"Time elapsed: {state.time_min} min")
    print(f"Distance to airport: {state.distance_nm:.1f} nm")
    print(f"Final altitude: {state.altitude_ft} ft")
    print(f"Final speed: {state.speed_kts} kt")
    print(f"Emergency declared: {'YES' if state.emergency_declared else 'NO'}")
    print(f"Engine 2 fire active: {'YES' if state.engine2_fire else 'NO'}")
    print(f"Score: {state.score}")

    if state.landed:
        if state.score >= 35:
            print("Outcome: SUCCESSFUL EMERGENCY LANDING")
        else:
            print("Outcome: LANDED WITH MAJOR DAMAGE")
    elif state.game_over:
        print("Outcome: FLIGHT LOST")
    else:
        print("Outcome: SIM ENDED")


def run_game() -> None:
    print(
        """
======================================================================
 VERBAL FLIGHT SIMULATOR - EMERGENCY MODE
======================================================================
You are actively flying a twin-engine jet to a diversion airport.
Failures will escalate. Fly the airplane and handle emergencies.
Type 'help' for commands.
"""
    )

    state = FlightState()

    while not state.game_over and state.time_min < 40:
        print_hud(state)
        incident_brief(state)
        command = input("\nCommand> ")
        advance_time = apply_command(state, command)

        if advance_time:
            state.time_min += 1
            apply_flight_physics(state)

    print_summary(state)


if __name__ == "__main__":
    run_game()
