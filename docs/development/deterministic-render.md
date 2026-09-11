# Deterministic PNG render boundary

`zencad render` evaluates a model in the same isolated managed runner used by
the editor, receives its final `SceneSnapshot`, and materializes that snapshot
in a short-lived native OCCT view. It does not restore editor layout or camera
state.

For every requested tile the renderer applies all camera inputs explicitly:

- orthographic projection;
- one of `iso`, `front`, `back`, `left`, `right`, `top`, or `bottom`, or an
  explicit camera azimuth/elevation pair;
- `FitAll` with the requested margin;
- fixed pixel size, solid sRGB background, explicit MSAA (default 4), axes policy, and display
  mode.

Multiple tiles are composed in request order into a row-major near-square PNG.
The output is encoded into a temporary file in the destination directory and
atomically replaces the destination only after the complete render succeeds.

Each preview releases its OCCT resources and explicitly destroys its native Qt
widget on the GUI thread, including when rendering fails. Closing the widget
alone leaves Python presenter cycles alive; collecting them later on a runner
thread can crash Cocoa. Cleanup completes before an owned QApplication is
released, and preserves an application's existing quit-on-last-window policy.
The preview shows its Qt window before binding OCCT, and binds explicitly
outside Qt event callbacks. A context-creation failure therefore reaches the
same cleanup as a rendering failure. Completed failure frames release their
local native handles before Qt destruction; traceback locations are preserved.

## Interfaces

The CLI entry point is:

```text
zencad render SCRIPT.py -o OUTPUT.png [--view iso,front] [--size 1024x768]
```

The Python entry points are `zencad.render_script(...)` and
`zencad.render_snapshot(...)`. `render_script` starts a multiprocessing runner,
so ordinary Python programs should invoke it below an
`if __name__ == "__main__"` guard. `render_snapshot` is useful when a managed
snapshot is already available and must run on the Qt application thread.

Script output is forwarded by the CLI. Script exceptions and animated sessions
use exit code 3, an absent or empty scene uses 4, a timeout uses 5, and a native
rendering failure uses 6. Argument errors use argparse's exit code 2. No output
path is replaced on those failures.

### Camera and MSAA options

```sh
zencad render model.py -o preview.png --yaw -65 --pitch 12 --msaa 8
```

CLI angles are degrees; `render_script` and `render_snapshot` accept `yaw` and
`pitch` in radians. Yaw is the camera's azimuth from +X toward +Y, and pitch is
its elevation above XY in [-pi/2, pi/2]. Both angles are required, and explicit
`views` cannot be combined with them. Omitting both angles and views selects
`iso`. A custom view returns `RenderResult.views == ("custom",)` and a single
tile. Its orthogonal up vector preserves vertical orientation and defines roll
at both poles. Projection remains orthographic with a fresh FitAll.

`msaa` accepts the integers 0, 2, 4, and 8 (CLI: `--msaa`), defaulting to 4.
It is explicit and independent of saved GUI settings; 0 disables MSAA. The
requested sampling is applied to the native view before image capture.
Invalid sampling, non-finite angles, out-of-range pitch, incomplete angle pairs,
and conflicts with fixed views fail before executing the model. CLI usage
errors return 2 and leave existing output files intact.

## Platform display contract

This is a non-interactive render command, but OCCT still creates a native
OpenGL-backed view. Windows and macOS use their desktop window systems. Linux
uses X11/XWayland; a display-less Linux host needs a virtual X server:

```sh
LIBGL_ALWAYS_SOFTWARE=1 xvfb-run -a \
  zencad render model.py -o preview.png --view iso,front,top,right
```

On macOS the viewer requests an OpenGL core profile. The default OCCT
compatibility profile selects OpenGL 2.1, which cannot supply the multisample
textures OCCT needs for MSAA even when the GPU supports them in a core context.
OCCT retains its legacy fallback for systems unable to create a core context.

On macOS, `ZENCAD_OPENGL_SOFTWARE=1` explicitly selects Apple's software
OpenGL renderer through OCCT's `contextNoAccel` option. Intel macOS CI uses
this mode because hosted machines may lack accelerated OpenGL; desktop Macs
and ARM macOS CI keep the default accelerated renderer. This setting does
not change rendering on Windows or Linux (use Mesa's `LIBGL_ALWAYS_SOFTWARE`
on Linux). The render tests still require actual MSAA edge coverage.

CI exercises the command on Windows and macOS desktops and under Xvfb with
software OpenGL on Linux. The smoke verifies image dimensions and content,
exact solid-background color, deterministic repeated output, contact-sheet
layout, custom CLI/API camera agreement, vertical poles, actual MSAA edge
coverage, error exits, and prompt cancellation of animated scripts.
