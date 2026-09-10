# Examples

Examples are included in `zencad/examples`. Open a model from the GUI examples menu or run its file from a repository checkout:

```sh
python3 -m zencad zencad/examples/4.Assemble/robot-arm.py
```

- `4.Assemble/robot-arm.py` — a rotary-joint arm follows a ball using a Jacobian and inverse kinematics.
- `4.Assemble/robot.py` — an animated hierarchical assembly with rotating head and arms.
- `4.Assemble/EulerAngles.py` — composition of rotations.
- `3.Animation/camera.py` — camera control from an animation.
- `Models/nut.py` — threaded geometry built with a helix and a swept profile. The model functions are defined in the example itself; this is not a separate standard fastener library.

To check a model without opening a window:

```sh
python3 -m zencad --no-show zencad/examples/4.Assemble/robot-arm.py
```

This mode checks the initial scene construction; the animation callback runs during normal execution. See [Animation](animate.html) for animation behavior and [Kinematics](kinematic.html) for chains.
