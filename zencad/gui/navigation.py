"""Qt-free navigation presets shared by the viewer and settings UI."""


DEFAULT_NAVIGATION_SCHEME = "zencad"
NAVIGATION_SCHEME_OPTIONS = (
    ("ZenCad — LMB rotate, MMB/RMB pan, wheel zoom", "zencad"),
    ("Legacy ZenCad — LMB rotate, MMB zoom, RMB pan", "classic"),
    (
        "Blender — MMB rotate, Shift+MMB pan, Ctrl+MMB zoom",
        "blender",
    ),
    ("FreeCAD CAD — MMB pan, LMB+MMB rotate", "freecad"),
    ("Maya — Alt+LMB rotate, Alt+MMB pan, Alt+RMB zoom", "maya"),
    ("Custom", "custom"),
)
NAVIGATION_SCHEMES = frozenset(
    value for _label, value in NAVIGATION_SCHEME_OPTIONS
)

CUSTOM_GESTURE_OPTIONS = (
    ("Disabled", "none"),
    ("Left drag", "left"),
    ("Middle drag", "middle"),
    ("Right drag", "right"),
    ("Left + Middle drag", "left+middle"),
    ("Middle + Right drag", "middle+right"),
    ("Alt + Left drag", "alt+left"),
    ("Alt + Middle drag", "alt+middle"),
    ("Alt + Right drag", "alt+right"),
    ("Shift + Left drag", "shift+left"),
    ("Shift + Middle drag", "shift+middle"),
    ("Shift + Right drag", "shift+right"),
    ("Ctrl + Left drag", "control+left"),
    ("Ctrl + Middle drag", "control+middle"),
    ("Ctrl + Right drag", "control+right"),
)
CUSTOM_GESTURES = frozenset(
    value for _label, value in CUSTOM_GESTURE_OPTIONS
)
DEFAULT_CUSTOM_BINDINGS = {
    "rotate": "left",
    "pan": "middle",
    "zoom": "none",
}

_BUTTON_ORDER = ("left", "middle", "right", "back", "forward")
_MODIFIER_ORDER = ("control", "shift", "alt", "meta")

_PRESET_BINDINGS = {
    "zencad": {
        "left": "rotate",
        "middle": "pan",
        "right": "pan",
        "alt": "rotate",
        "shift": "pan",
    },
    "classic": {
        "left": "rotate",
        "middle": "zoom",
        "right": "pan",
        "alt": "rotate",
        "shift": "pan",
    },
    "blender": {
        "middle": "rotate",
        "shift+middle": "pan",
        "control+middle": "zoom",
    },
    "freecad": {
        "middle": "pan",
        "left+middle": "rotate",
    },
    "maya": {
        "alt+left": "rotate",
        "alt+middle": "pan",
        "alt+right": "zoom",
    },
}


def normalize_navigation_scheme(value):
    if value not in NAVIGATION_SCHEMES:
        return DEFAULT_NAVIGATION_SCHEME
    return value


def normalize_custom_gesture(value, fallback="none"):
    if value not in CUSTOM_GESTURES:
        return fallback
    return value


def normalized_custom_bindings(bindings=None):
    bindings = bindings or {}
    return {
        action: normalize_custom_gesture(
            bindings.get(action),
            fallback,
        )
        for action, fallback in DEFAULT_CUSTOM_BINDINGS.items()
    }


def custom_bindings_conflict(bindings):
    gestures = [
        gesture
        for gesture in normalized_custom_bindings(bindings).values()
        if gesture != "none"
    ]
    return len(gestures) != len(set(gestures))


def _gesture(buttons, modifiers):
    buttons = frozenset(buttons)
    modifiers = frozenset(modifiers)
    unknown_buttons = buttons - set(_BUTTON_ORDER)
    unknown_modifiers = modifiers - set(_MODIFIER_ORDER)
    if unknown_buttons or unknown_modifiers:
        return None
    parts = [item for item in _MODIFIER_ORDER if item in modifiers]
    parts.extend(item for item in _BUTTON_ORDER if item in buttons)
    return "+".join(parts) or None


def navigation_drag_action(
    scheme,
    buttons,
    modifiers,
    custom_bindings=None,
):
    """Return ``rotate``, ``pan``, ``zoom``, or ``None`` for a gesture."""
    scheme = normalize_navigation_scheme(scheme)
    gesture = _gesture(buttons, modifiers)
    if gesture is None:
        return None
    if scheme == "custom":
        bindings = normalized_custom_bindings(custom_bindings)
        if custom_bindings_conflict(bindings):
            return None
        for action, binding in bindings.items():
            if binding == gesture:
                return action
        return None
    return _PRESET_BINDINGS[scheme].get(gesture)


def wheel_zoom_factor(delta, inverted=False, multiplier=1.1):
    if not delta:
        return 1.0
    zoom_in = delta > 0
    if inverted:
        zoom_in = not zoom_in
    return multiplier if zoom_in else 1 / multiplier


def navigation_scheme_help(scheme, custom_bindings=None):
    scheme = normalize_navigation_scheme(scheme)
    if scheme == "classic":
        return (
            "Left drag: rotate camera around center\n"
            "Middle drag: zoom\n"
            "Right drag: pan\n"
            "Mouse wheel: zoom"
        )
    if scheme == "blender":
        return (
            "Middle drag: rotate camera around center\n"
            "Shift+Middle drag: pan\n"
            "Ctrl+Middle drag: zoom\n"
            "Mouse wheel: zoom"
        )
    if scheme == "freecad":
        return (
            "Middle drag: pan\n"
            "Left+Middle drag: rotate camera around center\n"
            "Mouse wheel: zoom"
        )
    if scheme == "maya":
        return (
            "Alt+Left drag: rotate camera around center\n"
            "Alt+Middle drag: pan\n"
            "Alt+Right drag: zoom\n"
            "Mouse wheel: zoom"
        )
    if scheme == "custom":
        bindings = normalized_custom_bindings(custom_bindings)
        labels = dict((value, label) for label, value in CUSTOM_GESTURE_OPTIONS)
        return (
            f"Rotate: {labels[bindings['rotate']]}\n"
            f"Pan: {labels[bindings['pan']]}\n"
            f"Zoom: {labels[bindings['zoom']]}\n"
            "Mouse wheel: zoom"
        )
    return (
        "Left drag: rotate camera around center\n"
        "Middle or right drag: pan\n"
        "Mouse wheel: zoom"
    )
