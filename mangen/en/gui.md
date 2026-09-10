# Graphical interface, highlights. 

![gui.png](../images/gui.png)

---
## Call
The GUI window can be invoked in the following ways:

* Calling `show()` in a Python script opens a standalone viewer in that process; the commands below start the full editor.
* Executing `python3 -m zencad` in a terminal environment. (usage: `python3 -m zencad [filepath]`)
* Call the command line utility `zencad` (usage:` zencad [filepath] `) 

---
## Updating the model by updating the source file
The renderer keeps track of changes in the file, the source of the geometry. When the source is updated, the program automatically starts re-executing the script. The editor starts a separate script runner and receives a scene snapshot. The viewer and camera persist across evaluations. On failure, the last successful result remains visible. See [ZenCad internals](internal.html).

---
## Built-in text editor
The visualizer has a built-in text editor widget that can be used for quick editing or experimentation. Show editor `View/'Hide editor'`

---
## Built-in console
ZenCad also relays the terminal output to the embedded console. Show console `View/'Hide console'`.
This can be used when the main terminal output is not available. 

---
## Markers, determination of coordinates
To set markers, use the keys `Q (F1)`, `W (F2)`. After setting, the coordinates of the marker are displayed in the corresponding field. If both markers are set, the distance between them is displayed in the Distance field. 

---
## 3D navigation
Rotation: MouseLeftClick / Alt + MouseMove
Offset: MouseMiddleClick / MouseRightClick / Shift + MouseMove
Scaling: PgUp / PgDown / MouseWheel

The navigation preset can be selected in `Edit/Settings`: ZenCad, Legacy
ZenCad, Blender, FreeCAD CAD, Maya, or Custom. Custom assigns separate Rotate,
Pan, and Zoom gestures. Wheel zoom and orbit direction can also be inverted.

The renderer supports two orientation modes. Orthogonal orientation (Z axis is always upward) and free rotation mode. Switch between them - `Navigation/'Axionometric view'`, `Navigation / 'Free rotation view'`. 
