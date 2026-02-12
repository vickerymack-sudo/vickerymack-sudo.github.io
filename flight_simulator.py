#!/usr/bin/env python3
"""Text-based flight incident simulator.

The player responds to escalating in-flight failures.
Each decision affects safety, aircraft status, and final outcome.
"""

from dataclasses import dataclass
from typing import Callable


@dataclass
class FlightState:
    altitude_ft: int = 33000
    airspeed_kts: int = 280
    engine_fire: bool = False
    smoke_in_cabin: bool = False
    electrical_failure: bool = False
    fuel_imbalance: bool = False
    score: int = 0
    game_over: bool = False


def ask_choice(prompt: str, options: dict[str, str]) -> str:
    print("\n" + prompt)
    for key, text in options.items():
        print(f"  {key}) {text}")

    while True:
        choice = input("Choose an action: ").strip().lower()
        if choice in options:
            return choice
        print("Invalid choice. Try again.")


def apply_outcome(state: FlightState, success: bool, message: str) -> None:
    print(f"\n{message}")
    state.score += 15 if success else -10
    if not success:
        state.airspeed_kts = max(160, state.airspeed_kts - 15)


def engine_smoke_event(state: FlightState) -> None:
    print("\n--- INCIDENT 1: ENGINE SMOKE ---")
    print("Warning lights: ENG 2 OIL PRESS LOW + visible gray smoke trail.")

    choice = ask_choice(
        "What do you do first?",
        {
            "a": "Throttle back engine 2 and run memory items for smoke/fire.",
            "b": "Ignore it until ATC asks about the smoke.",
            "c": "Shut down both engines to be safe.",
        },
    )

    if choice == "a":
        state.smoke_in_cabin = True
        apply_outcome(
            state,
            True,
            "Good call. Engine 2 is isolated, but smoke starts entering the cabin ducts.",
        )
    elif choice == "b":
        state.engine_fire = True
        apply_outcome(
            state,
            False,
            "Delay worsens the fault. Smoke thickens and engine 2 catches fire.",
        )
    else:
        state.electrical_failure = True
        apply_outcome(
            state,
            False,
            "Both engines offline causes rapid power loss and major electrical failures.",
        )


def engine_fire_event(state: FlightState) -> None:
    print("\n--- INCIDENT 2: ENGINE FIRE ---")

    if not state.engine_fire:
        state.engine_fire = True
        print("A sudden bang! Fire warning activates for engine 2.")
    else:
        print("Fire warning persists. EGT is climbing dangerously.")

    choice = ask_choice(
        "How do you respond?",
        {
            "a": "Discharge first fire bottle, declare MAYDAY, begin diversion.",
            "b": "Keep climbing to cruise altitude before handling checklist.",
            "c": "Deploy landing gear now to slow down quickly.",
        },
    )

    if choice == "a":
        state.engine_fire = False
        state.altitude_ft -= 6000
        apply_outcome(
            state,
            True,
            "Excellent emergency management. Fire warning extinguished and diversion begun.",
        )
    elif choice == "b":
        state.fuel_imbalance = True
        apply_outcome(
            state,
            False,
            "Fire keeps burning during climb. Wing structure starts overheating.",
        )
    else:
        state.airspeed_kts = max(170, state.airspeed_kts - 40)
        apply_outcome(
            state,
            False,
            "Gear overspeed risk triggered and drag spikes. Fire remains unresolved.",
        )


def cabin_smoke_event(state: FlightState) -> None:
    print("\n--- INCIDENT 3: CABIN SMOKE ---")
    state.smoke_in_cabin = True
    print("Cabin crew reports dense smoke in the aft cabin.")

    choice = ask_choice(
        "What is your next priority?",
        {
            "a": "Crew oxygen masks ON, emergency descent, smoke checklist.",
            "b": "Ask cabin crew to open cockpit door for ventilation.",
            "c": "Turn off all electrical busses immediately.",
        },
    )

    if choice == "a":
        state.altitude_ft = 10000
        apply_outcome(
            state,
            True,
            "Correct priorities: aviate, navigate, communicate. Cabin conditions improve.",
        )
    elif choice == "b":
        state.game_over = True
        apply_outcome(
            state,
            False,
            "Smoke enters cockpit heavily. Visibility loss leads to loss of control.",
        )
    else:
        state.electrical_failure = True
        apply_outcome(
            state,
            False,
            "Critical avionics drop offline. You now have partial instrument capability.",
        )


def final_approach(state: FlightState) -> None:
    print("\n--- FINAL PHASE: DIVERSION LANDING ---")
    print("You are lined up for an emergency landing at the nearest suitable airport.")

    choice = ask_choice(
        "How do you configure for landing?",
        {
            "a": "Stabilized approach, single-engine profile, long runway.",
            "b": "Fast approach to minimize smoke exposure.",
            "c": "Circle once more to troubleshoot systems.",
        },
    )

    if choice == "a":
        apply_outcome(
            state,
            True,
            "Smooth touchdown. Aircraft stops safely and emergency crews inspect the jet.",
        )
    elif choice == "b":
        state.game_over = True
        apply_outcome(
            state,
            False,
            "Unstable approach ends in runway excursion.",
        )
    else:
        state.game_over = True
        apply_outcome(
            state,
            False,
            "Additional delay causes fire re-ignition before landing.",
        )


def print_summary(state: FlightState) -> None:
    print("\n=== FLIGHT SUMMARY ===")
    print(f"Altitude: {state.altitude_ft} ft")
    print(f"Airspeed: {state.airspeed_kts} kts")
    print(f"Engine fire active: {'YES' if state.engine_fire else 'NO'}")
    print(f"Smoke in cabin: {'YES' if state.smoke_in_cabin else 'NO'}")
    print(f"Electrical failure: {'YES' if state.electrical_failure else 'NO'}")
    print(f"Fuel imbalance: {'YES' if state.fuel_imbalance else 'NO'}")
    print(f"Safety score: {state.score}")

    if state.game_over:
        print("Outcome: FLIGHT LOST")
    elif state.score >= 35:
        print("Outcome: SUCCESSFUL EMERGENCY LANDING")
    else:
        print("Outcome: HARD LANDING WITH SIGNIFICANT DAMAGE")


def run_game() -> None:
    print("""
========================================
 FLIGHT INCIDENT SIMULATOR
========================================
You are the pilot in command of a twin-engine airliner.
Make decisions as incidents escalate.
""")

    state = FlightState()
    sequence: list[Callable[[FlightState], None]] = [
        engine_smoke_event,
        engine_fire_event,
        cabin_smoke_event,
        final_approach,
    ]

    for event in sequence:
        if state.game_over:
            break
        event(state)

    print_summary(state)


if __name__ == "__main__":
    run_game()
