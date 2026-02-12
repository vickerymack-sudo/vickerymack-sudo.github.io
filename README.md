# Verbal Flight Simulator (Emergency Scenario)

This is an interactive terminal flight simulator where you **actively fly the plane** while handling an emergency chain.

## What makes this different
Instead of only choosing story options, you now control flight parameters in real time:
- Throttle
- Pitch (climb/descend)
- Heading (turn left/right)
- Flaps
- Landing gear

At the same time, incidents escalate (engine smoke -> engine fire -> cabin smoke), and you must run emergency actions like:
- `declare mayday`
- `shutdown eng2`
- `fire bottle`
- `oxygen on`

## Run
```bash
python3 flight_simulator.py
```

## Core commands
- `help`
- `status`
- `throttle 70`
- `pitch -1`
- `turn L 20`
- `flaps 2`
- `gear down`
- `declare mayday`
- `fire bottle`
- `shutdown eng2`
- `oxygen on`
- `tick`

## Win condition
Get to the diversion airport and land in a stable configuration:
- Correct speed
- Proper heading alignment
- Gear down
- Landing flaps set

Poor energy management or delayed emergency response can still cause loss of control or a crash landing.
