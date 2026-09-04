"""GUI-thread checkpointing for cumulative camera actions."""

from zencad.runtime.camera_action_protocol import (
    CameraAction,
    CameraActionSequenceError,
    IDENTITY_QUATERNION,
    SupersededCameraActionError,
    ensure_current_camera_action,
    relative_quaternion,
)


class CameraActionPresentationError(RuntimeError):
    """A camera action could not be safely applied."""


class CameraActionPresenter:
    """Apply cumulative checkpoints as deltas to a GUI-owned camera."""

    def __init__(self, widget):
        self.widget = widget
        self.reset()

    def reset(self):
        self._generation = None
        self._scene_revision = None
        self.last_sequence = None
        self.last_action_revision = None
        self.cumulative_orbit = IDENTITY_QUATERNION

    def apply(self, action, expected_generation, expected_scene_revision):
        checker = getattr(self.widget, "assert_gui_thread", None)
        if checker is not None:
            checker()
        if not isinstance(action, CameraAction):
            raise TypeError("CameraActionPresenter requires a CameraAction")
        if expected_generation is None or expected_scene_revision is None:
            raise CameraActionPresentationError(
                "Cannot apply a camera action without a committed scene"
            )
        try:
            ensure_current_camera_action(
                action, expected_generation, expected_scene_revision
            )
        except SupersededCameraActionError as exception:
            raise CameraActionPresentationError(str(exception)) from exception

        identity = (action.generation, action.scene_revision)
        current = (self._generation, self._scene_revision)
        if self._generation is not None and identity != current:
            raise CameraActionPresentationError(
                "CameraAction stream changed without a lifecycle reset"
            )
        if (
            self.last_sequence is not None
            and action.sequence <= self.last_sequence
        ):
            raise CameraActionSequenceError(
                "CameraAction sequence is duplicate or out of order"
            )
        if (
            self.last_action_revision is not None
            and action.action_revision <= self.last_action_revision
        ):
            raise CameraActionSequenceError(
                "CameraAction revision is duplicate or out of order"
            )

        delta = relative_quaternion(
            self.cumulative_orbit, action.cumulative_orbit
        )
        try:
            self.widget.apply_camera_orbit(delta)
        except Exception as exception:
            raise CameraActionPresentationError(
                "Failed to commit CameraAction"
            ) from exception

        self._generation, self._scene_revision = identity
        self.last_sequence = action.sequence
        self.last_action_revision = action.action_revision
        self.cumulative_orbit = action.cumulative_orbit
        return action.sequence
