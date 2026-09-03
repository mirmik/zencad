import math
import unittest

from zencad.gui.camera_action_presenter import (
    CameraActionPresentationError,
    CameraActionPresenter,
)
from zencad.runtime.camera_action_protocol import (
    CameraAction,
    CameraActionSequenceError,
    quaternion_from_axis_angle,
    quaternion_multiply,
    rotate_vector,
)


def close_tuple(test, actual, expected):
    for got, wanted in zip(actual, expected):
        test.assertAlmostEqual(got, wanted, places=10)


class FakeCameraWidget:
    def __init__(self):
        self.camera = {
            "eye": (2.0, 0.0, 0.0),
            "center": (1.0, 0.0, 0.0),
            "up": (0.0, 0.0, 1.0),
            "scale": 3.0,
            "projection": "perspective",
        }
        self.thread_checks = 0
        self.redraws = 0
        self.fail_next = False

    def assert_gui_thread(self):
        self.thread_checks += 1

    def apply_camera_orbit(self, quaternion):
        saved = dict(self.camera)
        try:
            center = self.camera["center"]
            eye = self.camera["eye"]
            offset = tuple(eye[i] - center[i] for i in range(3))
            rotated = rotate_vector(quaternion, offset)
            self.camera["eye"] = tuple(
                center[i] + rotated[i] for i in range(3)
            )
            self.camera["up"] = rotate_vector(
                quaternion, self.camera["up"]
            )
            if self.fail_next:
                self.fail_next = False
                raise RuntimeError("camera failed")
            self.redraws += 1
        except Exception:
            self.camera = saved
            raise


class CameraActionPresenterTest(unittest.TestCase):
    def test_manual_navigation_becomes_base_for_next_delta(self):
        widget = FakeCameraWidget()
        presenter = CameraActionPresenter(widget)
        z = quaternion_from_axis_angle((0, 0, 1), math.pi / 2)
        x = quaternion_from_axis_angle((1, 0, 0), math.pi / 2)

        presenter.apply(CameraAction(3, 0, 1, 1, z), 3, 0)
        close_tuple(self, widget.camera["eye"], (1, 1, 0))

        # Simulate GUI-owned pan, zoom and orbit between runner checkpoints.
        widget.camera.update({
            "eye": (4.0, 7.0, 0.0),
            "center": (4.0, 5.0, 0.0),
            "up": (0.0, 0.0, 1.0),
            "scale": 9.0,
            "projection": "orthographic",
        })
        cumulative = quaternion_multiply(x, z)
        presenter.apply(CameraAction(3, 0, 4, 2, cumulative), 3, 0)

        close_tuple(self, widget.camera["eye"], (4, 5, 2))
        close_tuple(self, widget.camera["center"], (4, 5, 0))
        close_tuple(self, widget.camera["up"], (0, -1, 0))
        self.assertEqual(widget.camera["scale"], 9.0)
        self.assertEqual(widget.camera["projection"], "orthographic")
        self.assertEqual(widget.redraws, 2)
        self.assertEqual(widget.thread_checks, 2)

    def test_stale_replay_and_failure_do_not_advance_checkpoint(self):
        widget = FakeCameraWidget()
        presenter = CameraActionPresenter(widget)
        first = CameraAction(
            8, 2, 1, 1,
            quaternion_from_axis_angle((0, 0, 1), 0.1),
        )
        presenter.apply(first, 8, 2)
        committed_camera = dict(widget.camera)

        with self.assertRaises(CameraActionSequenceError):
            presenter.apply(first, 8, 2)
        with self.assertRaises(CameraActionPresentationError):
            presenter.apply(
                CameraAction(9, 2, 2, 2, first.cumulative_orbit), 8, 2
            )
        self.assertEqual(widget.camera, committed_camera)

        second = CameraAction(
            8, 2, 2, 2,
            quaternion_from_axis_angle((0, 0, 1), 0.2),
        )
        widget.fail_next = True
        with self.assertRaisesRegex(CameraActionPresentationError, "commit"):
            presenter.apply(second, 8, 2)
        self.assertEqual(widget.camera, committed_camera)
        self.assertEqual(presenter.last_sequence, 1)
        self.assertEqual(presenter.last_action_revision, 1)

        presenter.apply(second, 8, 2)
        self.assertEqual(presenter.last_sequence, 2)


if __name__ == "__main__":
    unittest.main()
