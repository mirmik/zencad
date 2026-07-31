#!/usr/bin/env python3
"""Benchmark BREP and SceneSnapshot transfer candidates.

The output is JSON so measured results can be copied into the architecture
notes and compared on another platform.
"""

import argparse
import gc
import importlib.util
import json
import multiprocessing
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory
import time
import tracemalloc

from OCP.BRep import BRep_Builder
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCP.TopoDS import TopoDS_Compound


ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

import zencad
from evalcache.dircache_v2 import DirCache_v2
from zencad.runtime.scene_protocol import (
    FileSnapshotBundle,
    SceneObjectRecord,
    SceneSnapshot,
    decode_brep,
    decode_snapshot_frame,
    encode_brep,
    encode_snapshot_frame,
)


def compound_of_boxes(count):
    compound = TopoDS_Compound()
    builder = BRep_Builder()
    builder.MakeCompound(compound)
    for index in range(count):
        box = BRepPrimAPI_MakeBox(1.0, 2.0, 3.0).Shape()
        moved = zencad.Shape(box).translate(index * 2.0, 0, 0).Shape()
        builder.Add(compound, moved)
    return compound


def organizer_model():
    path = ROOT / "zencad" / "examples" / "Models" / "organizer" / "organizer.py"
    spec = importlib.util.spec_from_file_location("zencad_benchmark_organizer", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.organizer(3, 5, 27, 20, 64, 1.5, 5, 5).unlazy().Shape()


def measure(operation, repeat):
    gc.collect()
    tracemalloc.start()
    started = time.perf_counter()
    for _ in range(repeat):
        operation()
    elapsed = time.perf_counter() - started
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {
        "mean_ms": round(elapsed * 1000.0 / repeat, 3),
        "python_peak_bytes": peak,
    }


def receive_frames(connection, count):
    try:
        for _ in range(count):
            connection.recv_bytes()
    finally:
        connection.close()


def measure_pipe(frame, repeat):
    receiver, sender = multiprocessing.Pipe(duplex=False)
    process = multiprocessing.Process(
        target=receive_frames,
        args=(receiver, repeat + 1),
    )
    process.start()
    receiver.close()
    sender.send_bytes(frame)  # Warm the connection and receiver process.
    result = measure(lambda: sender.send_bytes(frame), repeat)
    sender.close()
    process.join(timeout=30)
    if process.is_alive():
        process.terminate()
        process.join()
        raise RuntimeError("Pipe benchmark receiver did not finish")
    if process.exitcode != 0:
        raise RuntimeError(
            f"Pipe benchmark receiver exited with {process.exitcode}"
        )
    return result


def benchmark_case(name, shape, repeat, directory):
    payload = encode_brep(shape)
    snapshot = SceneSnapshot(
        generation=1,
        objects=(SceneObjectRecord(name, "brep", payload),),
    )
    frame = encode_snapshot_frame(snapshot)

    write_counter = 0

    def write_bundle():
        nonlocal write_counter
        path = directory / f"{name}-write-{write_counter}"
        write_counter += 1
        FileSnapshotBundle.write(path, snapshot)
        shutil.rmtree(path)

    read_path = directory / f"{name}-read"
    FileSnapshotBundle.write(read_path, snapshot)

    result = {
        "brep_bytes": len(payload),
        "frame_bytes": len(frame),
        "brep_encode": measure(lambda: encode_brep(shape), repeat),
        "brep_decode": measure(lambda: decode_brep(payload), repeat),
        "frame_encode": measure(
            lambda: encode_snapshot_frame(snapshot), repeat
        ),
        "frame_decode": measure(lambda: decode_snapshot_frame(frame), repeat),
        "pipe_send": measure_pipe(frame, repeat),
        "bundle_write": measure(write_bundle, repeat),
        "bundle_read": measure(
            lambda: FileSnapshotBundle.read(read_path), repeat
        ),
    }
    shutil.rmtree(read_path)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeat", type=int, default=5)
    parser.add_argument("--compound-count", type=int, default=1000)
    arguments = parser.parse_args()
    if arguments.repeat < 1 or arguments.compound_count < 1:
        parser.error("repeat and compound-count must be positive")

    with TemporaryDirectory() as cache_directory, TemporaryDirectory() as data_directory:
        zencad.lazy.cache = DirCache_v2(cache_directory)
        zencad.lazy.encache = False
        zencad.lazy.decache = False
        zencad.lazy.fastdo = True

        shapes = {
            "box": zencad.box(20).unlazy().Shape(),
            "boolean": (
                zencad.box(20, center=True) - zencad.sphere(5)
            ).unlazy().Shape(),
            "organizer_model": organizer_model(),
            "compound": compound_of_boxes(arguments.compound_count),
        }
        output = {
            "repeat": arguments.repeat,
            "compound_count": arguments.compound_count,
            "cases": {},
        }
        directory = Path(data_directory)
        for name, shape in shapes.items():
            output["cases"][name] = benchmark_case(
                name, shape, arguments.repeat, directory
            )

    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
