from pathlib import Path
from tempfile import TemporaryDirectory
import threading
import time
import unittest

from zencad.runtime.runner_supervisor import RunnerSupervisor


ROOT = Path(__file__).parents[1]
EXAMPLES = (
    "zencad/examples/3.Animation/base.py",
    "zencad/examples/3.Animation/color.py",
    "zencad/examples/3.Animation/pacman.py",
    "zencad/examples/MiniGames/tetris.py",
    "zencad/examples/MiniGames/tennis.py",
)


class ManagedExamplesTest(unittest.TestCase):
    def setUp(self):
        self.patch_events = {}
        self.camera_action_events = {}
        self.camera_actions = {}
        self.cache_directory = TemporaryDirectory()

        def on_message(message):
            if message.message_type == "scene_patch":
                self.patch_events.setdefault(
                    message.generation, threading.Event()
                ).set()
            elif message.message_type == "camera_action":
                self.camera_actions[message.generation] = message.camera_action
                self.camera_action_events.setdefault(
                    message.generation, threading.Event()
                ).set()

        self.supervisor = RunnerSupervisor(
            on_message=on_message,
            cancel_grace_period=0.5,
            record_scene_patches=False,
            cache_directory=self.cache_directory.name,
        )

    def tearDown(self):
        self.supervisor.shutdown()
        self.cache_directory.cleanup()

    def wait_for_message(self, generation, message_type, timeout=30):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            for message in self.supervisor.messages:
                if (
                    message.generation == generation
                    and message.message_type == message_type
                ):
                    return message
            time.sleep(0.01)
        self.fail(f"generation {generation} did not emit {message_type}")

    def test_representative_animations_and_games_emit_live_patches(self):
        for relative_path in EXAMPLES:
            with self.subTest(example=relative_path):
                generation = self.supervisor.start(ROOT / relative_path)
                ready = self.wait_for_message(generation, "ready")
                self.assertTrue(ready.payload["animated"])
                scene = self.wait_for_message(generation, "scene")
                self.assertGreater(len(scene.snapshot.objects), 0)
                patch_event = self.patch_events.setdefault(
                    generation, threading.Event()
                )
                self.assertTrue(
                    patch_event.wait(30),
                    f"{relative_path} did not emit a live patch",
                )
                self.assertTrue(self.supervisor.cancel_current())
                self.assertEqual(
                    self.supervisor.wait(generation, timeout=10),
                    "cancelled",
                )

    def test_camera_example_orbits_viewer_without_model_patches(self):
        generation = self.supervisor.start(
            ROOT / "zencad/examples/3.Animation/camera.py"
        )
        ready = self.wait_for_message(generation, "ready")
        self.assertTrue(ready.payload["animated"])
        scene = self.wait_for_message(generation, "scene")
        self.assertEqual(len(scene.snapshot.objects), 1)
        self.assertEqual(
            scene.snapshot.objects[0].properties["transform"]["rotation"],
            (0.0, 0.0, 0.0, 1.0),
        )
        action_event = self.camera_action_events.setdefault(
            generation, threading.Event()
        )
        self.assertTrue(action_event.wait(30))
        self.assertGreaterEqual(
            self.camera_actions[generation].action_revision, 1
        )
        self.assertNotIn(generation, self.patch_events)
        self.assertTrue(self.supervisor.cancel_current())
        self.assertEqual(
            self.supervisor.wait(generation, timeout=10), "cancelled"
        )


if __name__ == "__main__":
    unittest.main()
