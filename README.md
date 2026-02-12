# Verbal Flight Simulator (Visual Emergency Mode)

You asked for visuals like a real simulator experience, so this version runs in a **live graphical window** with an attitude horizon, runway cue, cockpit-style HUD, and real-time controls.

> Note: this is a lightweight 2D simulator and **not a full 3D Microsoft Flight Simulator clone**.

## Features
- Real-time visual cockpit/horizon rendering (Tkinter canvas)
- Flight controls: throttle, pitch, bank, flaps, gear
- Emergency chain: engine smoke -> engine fire -> cabin smoke
- Emergency actions: MAYDAY, engine shutdown, fire bottle, oxygen
- Landing evaluation based on speed, alignment, and configuration

## Run (visual mode)
```bash
python3 flight_simulator.py
```

## Controls
- `W / S` : throttle up / down
- `Up / Down` : pitch up / down
- `Left / Right` : bank left / right
- `Space` : dampen bank/pitch
- `F` : cycle flaps (0-3)
- `G` : toggle landing gear
- `M` : declare MAYDAY
- `E` : shutdown engine 2
- `B` : discharge fire bottle
- `O` : toggle oxygen
- `Q` : quit

## Headless demo mode (for non-GUI environments)
```bash
python3 flight_simulator.py --demo --demo-seconds 20
```

This runs the same physics/emergency core and prints state updates to terminal.
