from pathlib import Path
import os
from tempfile import TemporaryDirectory
import time
import unittest

from zencad.runtime.runner_protocol import (
    decode_control_message,
    encode_control_message,
)
from zencad.runtime.runner_supervisor import RunnerSupervisor
from zencad.runtime.scene_protocol import ProtocolError


class RunnerSupervisorTest(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.supervisor = RunnerSupervisor(
            cancel_grace_period=0.1,
            cache_directory=self.root / "cache",
        )

    def tearDown(self):
        self.supervisor.shutdown()
        self.directory.cleanup()

    def script(self, name, source):
        path = self.root / name
        path.write_text(source, encoding="utf-8")
        return path

    def messages(self, generation, message_type=None):
        return [
            message
            for message in self.supervisor.messages
            if message.generation == generation
            and (
                message_type is None
                or message.message_type == message_type
            )
        ]

    def wait_for_message(self, generation, message_type, timeout=10):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            messages = self.messages(generation, message_type)
            if messages:
                return messages[-1]
            time.sleep(0.01)
        self.fail(
            f"Runner generation {generation} did not emit {message_type!r}"
        )

    def test_default_cache_directory_is_persistent(self):
        supervisor = RunnerSupervisor()
        try:
            self.assertEqual(
                supervisor.cache_directory,
                Path.home() / ".zencadcache",
            )
        finally:
            supervisor.shutdown()

    def test_control_message_round_trip_and_validation(self):
        frame = encode_control_message(
            "run",
            8,
            script_path="demo.py",
            arguments=["one"],
        )
        self.assertEqual(
            decode_control_message(frame),
            (
                "run",
                8,
                {"arguments": ["one"], "script_path": "demo.py"},
            ),
        )
        with self.assertRaises(ProtocolError):
            decode_control_message(frame[:-1])

    def test_scene_output_progress_and_isolation(self):
        self.script("helper.py", "VALUE = 'local-import'\n")
        path = self.script("success.py", """
import os
import sys
from helper import VALUE
assert "PyQt5" not in sys.modules
assert "zencad.gui.display" not in sys.modules
from zencad import box, display, show
print(VALUE)
print(os.getcwd())
print("diagnostic", file=sys.stderr)
display(box(2), color=(0.1, 0.2, 0.3, 0.4)).right(5)
show()
""")
        generation = self.supervisor.start(path, cwd=self.root)
        self.assertEqual(self.supervisor.wait(generation, timeout=10), "success")

        scenes = self.messages(generation, "scene")
        self.assertEqual(len(scenes), 1)
        self.assertEqual(scenes[0].snapshot.generation, generation)
        self.assertEqual(len(scenes[0].snapshot.objects), 1)
        output = self.messages(generation, "output")
        stdout = "".join(
            item.payload["text"]
            for item in output
            if item.payload["stream"] == "stdout"
        )
        stderr = "".join(
            item.payload["text"]
            for item in output
            if item.payload["stream"] == "stderr"
        )
        self.assertIn("local-import", stdout)
        reported_cwd = next(
            line for line in stdout.splitlines() if line != "local-import"
        )
        self.assertTrue(os.path.samefile(reported_cwd, self.root))
        self.assertIn("diagnostic", stderr)
        progress = self.messages(generation, "progress")
        self.assertTrue(progress)
        self.assertTrue(any(
            item.payload.get("subcmd") in {"newtree", "progress"}
            for item in progress
        ))
        self.assertTrue(any(
            item.payload.get("operation") in {"load", "evaluate", "memory"}
            and item.payload.get("object")
            for item in progress
        ))
        self.assertEqual(
            self.messages(generation, "finished")[-1].payload["status"],
            "success",
        )

    def test_cache_is_reused_by_sequential_runner_generations(self):
        counter = self.root / "evaluation-count.txt"
        path = self.script("cached.py", f"""
from pathlib import Path
from zencad import box, display, show
from zencad.lazifier import lazy

counter = Path({str(counter)!r})

@lazy
def cached_box(size):
    count = int(counter.read_text()) if counter.exists() else 0
    counter.write_text(str(count + 1))
    return box(size).unlazy()

display(cached_box(2))
show()
""")

        first = self.supervisor.start(path)
        self.assertEqual(self.supervisor.wait(first, timeout=10), "success")
        second = self.supervisor.start(path)
        self.assertEqual(self.supervisor.wait(second, timeout=10), "success")

        self.assertEqual(counter.read_text(), "1")

    def test_exception_contains_traceback_and_next_run_succeeds(self):
        failing = self.script("failing.py", "raise ValueError('broken script')\n")
        generation = self.supervisor.start(failing)
        self.assertEqual(self.supervisor.wait(generation, timeout=10), "error")
        error = self.messages(generation, "error")[-1]
        self.assertEqual(error.payload["exception_type"], "ValueError")
        self.assertIn("broken script", error.payload["message"])
        self.assertIn("failing.py", error.payload["traceback"])

        succeeding = self.script(
            "after_error.py",
            "from zencad import box, display, show\ndisplay(box(1))\nshow()\n",
        )
        next_generation = self.supervisor.start(succeeding)
        self.assertEqual(
            self.supervisor.wait(next_generation, timeout=10),
            "success",
        )
        self.assertEqual(len(self.messages(next_generation, "scene")), 1)

    def test_animation_emits_ready_and_patches_before_structured_failure(self):
        path = self.script("animated_failure.py", """
import sys
from zencad import box, display, show, translate
assert "PyQt5" not in sys.modules
assert "zencad.gui.display" not in sys.modules
controller = display(box(2))
assert not hasattr(controller, "ais_object")
ticks = 0
def animate(state):
    global ticks
    ticks += 1
    controller.relocate(translate(ticks, 2, 3))
    controller.set_color(1, 0, 0, 0.25)
    controller.hide(ticks % 2 == 0)
    if ticks == 3:
        raise RuntimeError("animation failed")
def close_handle():
    print("animation closed")
show(animate=animate, animate_step=0.001, close_handle=close_handle)
""")
        generation = self.supervisor.start(path)
        self.assertEqual(self.supervisor.wait(generation, timeout=10), "error")

        message_types = [
            message.message_type
            for message in self.messages(generation)
        ]
        scene_index = message_types.index("scene")
        ready_index = message_types.index("ready")
        patch_index = message_types.index("scene_patch")
        self.assertLess(scene_index, ready_index)
        self.assertLess(ready_index, patch_index)
        ready = self.messages(generation, "ready")[-1]
        self.assertEqual(dict(ready.payload), {
            "animated": True,
            "scene_revision": 0,
        })
        patches = self.messages(generation, "scene_patch")
        self.assertEqual(len(patches), 2)
        self.assertEqual(
            [message.scene_patch.sequence for message in patches],
            [1, 2],
        )
        first = patches[0].scene_patch
        self.assertEqual(first.generation, generation)
        self.assertEqual(first.scene_revision, 0)
        self.assertEqual(
            set(first.updates[0].properties),
            {"transform", "color", "visible"},
        )
        error = self.messages(generation, "error")[-1]
        self.assertEqual(error.payload["exception_type"], "RuntimeError")
        self.assertIn("animation failed", error.payload["message"])
        stdout = "".join(
            message.payload["text"]
            for message in self.messages(generation, "output")
            if message.payload["stream"] == "stdout"
        )
        self.assertIn("animation closed", stdout)

    def test_live_animation_is_cooperatively_cancelled(self):
        path = self.script("animated_cancel.py", """
import sys
from zencad import box, display, show, translate
assert "PyQt5" not in sys.modules
assert "zencad.gui.display" not in sys.modules
controller = display(box(1))
ticks = 0
def animate(state):
    global ticks
    ticks += 1
    controller.relocate(translate(ticks, 0, 0))
show(animate=animate, animate_step=0.001)
""")
        generation = self.supervisor.start(path)
        self.wait_for_message(generation, "scene_patch")
        self.assertTrue(self.supervisor.cancel_current(grace_period=0.5))
        self.assertEqual(
            self.supervisor.wait(generation, timeout=10),
            "cancelled",
        )
        self.assertFalse(self.supervisor.is_alive(generation))
        finished = self.messages(generation, "finished")[-1]
        self.assertFalse(finished.payload.get("hard", False))

    def test_input_edges_reach_only_the_current_runner(self):
        path = self.script("animated_input.py", """
import sys
from zencad import box, display, show, translate
assert "PyQt5" not in sys.modules
controller = display(box(1))
saw_press = False
def animate(state):
    global saw_press
    saw_press = saw_press or state.input.key_pressed("right")
    if saw_press and state.input.key_released("right"):
        assert not state.input.key_down("right")
        controller.relocate(translate(9, 0, 0))
        raise RuntimeError("input edges observed")
show(animate=animate, animate_step=0.01)
""")
        generation = self.supervisor.start(path)
        self.wait_for_message(generation, "ready")
        self.assertTrue(self.supervisor.send_input("key_down", {
            "key": "right", "text": "", "modifiers": [], "repeat": False,
        }))
        time.sleep(0.03)
        self.assertTrue(self.supervisor.send_input("key_up", {
            "key": "right", "text": "", "modifiers": [], "repeat": False,
        }))
        self.assertEqual(self.supervisor.wait(generation, timeout=10), "error")
        error = self.messages(generation, "error")[-1]
        self.assertIn("input edges observed", error.payload["message"])

        replacement = self.script("input_replacement.py", "print('replacement')\n")
        next_generation = self.supervisor.start(replacement)
        self.assertFalse(self.supervisor.send_input(
            "key_down",
            {"key": "left", "text": "", "modifiers": [], "repeat": False},
            generation=generation,
        ))
        self.assertEqual(
            self.supervisor.wait(next_generation, timeout=10), "success"
        )

    def test_superseded_live_generation_cannot_dispatch_late_patches(self):
        live = self.script("superseded_animation.py", """
from zencad import box, display, show, translate
controller = display(box(1))
ticks = 0
def animate(state):
    global ticks
    ticks += 1
    controller.relocate(translate(ticks, 0, 0))
show(animate=animate, animate_step=0.001)
""")
        replacement = self.script(
            "animation_replacement.py",
            "from zencad import show, sphere, display\n"
            "display(sphere(2))\nshow()\n",
        )
        first = self.supervisor.start(live)
        self.wait_for_message(first, "scene_patch")

        second = self.supervisor.start(replacement)
        patches_after_reload = len(self.messages(first, "scene_patch"))
        self.assertEqual(self.supervisor.wait(second, timeout=10), "success")
        self.assertEqual(self.supervisor.wait(first, timeout=10), "cancelled")
        time.sleep(0.05)

        self.assertEqual(
            len(self.messages(first, "scene_patch")),
            patches_after_reload,
        )
        self.assertEqual(len(self.messages(second, "scene")), 1)

    def test_superseded_generation_cannot_publish_scene(self):
        slow = self.script("slow.py", """
import time
from zencad import box, display, show
for _ in range(500):
    time.sleep(0.01)
display(box(10))
show()
""")
        fast = self.script(
            "fast.py",
            "from zencad import sphere, display, show\ndisplay(sphere(2))\nshow()\n",
        )
        first = self.supervisor.start(slow)
        time.sleep(0.1)
        second = self.supervisor.start(fast)
        self.assertEqual(self.supervisor.wait(second, timeout=10), "success")
        self.assertEqual(self.supervisor.wait(first, timeout=10), "cancelled")

        scene_generations = [
            message.generation
            for message in self.supervisor.messages
            if message.message_type == "scene"
        ]
        self.assertEqual(scene_generations, [second])

    def test_hung_runner_is_hard_cancelled_without_blocking_caller(self):
        hung = self.script("hung.py", "import time\ntime.sleep(60)\n")
        generation = self.supervisor.start(hung)
        time.sleep(0.2)
        started = time.monotonic()
        self.assertTrue(self.supervisor.cancel_current(grace_period=0.05))
        self.assertLess(time.monotonic() - started, 0.1)
        self.assertEqual(
            self.supervisor.wait(generation, timeout=5),
            "cancelled",
        )
        self.assertFalse(self.supervisor.is_alive(generation))

        next_path = self.script("after_cancel.py", "print('alive again')\n")
        next_generation = self.supervisor.start(next_path)
        self.assertEqual(
            self.supervisor.wait(next_generation, timeout=10),
            "success",
        )

    def test_crash_is_diagnosed_and_does_not_poison_restart(self):
        crashing = self.script("crash.py", "import os\nos._exit(7)\n")
        generation = self.supervisor.start(crashing)
        self.assertEqual(self.supervisor.wait(generation, timeout=10), "crashed")
        error = self.messages(generation, "error")[-1]
        self.assertEqual(error.payload["kind"], "crash")
        self.assertIn("code 7", error.payload["message"])

        next_path = self.script("after_crash.py", "print('restarted')\n")
        next_generation = self.supervisor.start(next_path)
        self.assertEqual(
            self.supervisor.wait(next_generation, timeout=10),
            "success",
        )


if __name__ == "__main__":
    unittest.main()
