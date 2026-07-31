from pathlib import Path
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
        self.supervisor = RunnerSupervisor(cancel_grace_period=0.1)

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
        self.assertIn(str(self.root), stdout)
        self.assertIn("diagnostic", stderr)
        progress = self.messages(generation, "progress")
        self.assertTrue(progress)
        self.assertTrue(any(
            item.payload.get("subcmd") in {"newtree", "progress"}
            for item in progress
        ))
        self.assertEqual(
            self.messages(generation, "finished")[-1].payload["status"],
            "success",
        )

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
