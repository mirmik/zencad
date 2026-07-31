# SceneSnapshot transport v1

This document records the implemented transport spike for the planned
[runtime architecture](runtime-architecture.md).  It describes a protocol
foundation, not yet the default ZenCad execution path.

## Wire contract

Protocol version 1 is explicit and pickle-free.  An inline frame contains:

1. `ZCSN` magic, protocol version, manifest size, and payload count;
2. canonical UTF-8 JSON manifest;
3. length-prefixed binary payloads.

The manifest carries the generation, camera policy, metadata, ordered object
records, payload sizes, and SHA-256 digests.  A receiver validates the entire
frame before it returns a `SceneSnapshot`.  Unknown versions, malformed JSON,
truncation, size mismatch, digest mismatch, duplicate object IDs, and an
unexpected generation are errors; they cannot produce a partial snapshot.

Shape payloads are OCCT BREP bytes.  Logical object identity and presentation
properties remain in the manifest rather than being hidden in Python pickle.

## Carrier selection

- Frames up to and including 32 MiB use a binary connection frame.
- Larger snapshots use an atomic directory-backed bundle with the same JSON
  manifest and separately stored payloads.
- The supervisor owns bundle lifetime and cleanup.  A bundle becomes visible
  only after its temporary directory is renamed into place.

The 32 MiB boundary is a memory guard, not a format boundary.  Encoding a
monolithic inline frame allocates another buffer approximately as large as the
already serialized payload.  File-backed writing streams the existing payload
objects without that additional combined frame.  Both carriers decode to the
same `SceneSnapshot` contract.

## Benchmark

Measured on 2026-08-01 with Linux x86-64, CPython 3.10.19,
`cadquery-ocp-novtk==7.9.3.1.1`.  Run with:

```bash
python tools/benchmark_scene_transport.py --repeat 3 --compound-count 10000
```

Times are per operation.  Python peak memory is measured with `tracemalloc`;
it does not include allocations internal to OCCT.

| Case | BREP size | BREP encode | BREP decode | Frame encode | Pipe send | Bundle write | Bundle read |
|---|---:|---:|---:|---:|---:|---:|---:|
| box | 2,545 B | 0.113 ms | 0.092 ms | 0.073 ms | 0.041 ms | 0.370 ms | 0.121 ms |
| boolean | 3,408 B | 0.124 ms | 0.094 ms | 0.066 ms | 0.021 ms | 0.306 ms | 0.126 ms |
| organizer example | 221,676 B | 6.389 ms | 3.170 ms | 0.309 ms | 0.074 ms | 0.464 ms | 0.242 ms |
| compound, 10,000 boxes | 21,171,970 B | 656.581 ms | 379.717 ms | 31.169 ms | 6.526 ms | 10.605 ms | 9.467 ms |

For the 21.2 MB case the inline pipe remains approximately three times faster
than bundle write plus read.  BREP conversion dominates both carriers.  Frame
encoding peaks at roughly one additional payload-sized Python allocation
(21,175,691 B in this run), while bundle writing adds only about 10 KiB beyond
the payload already held by the snapshot.  This supports inline transport for
ordinary scenes and a file-backed escape path for unusually large scenes.

## Verification

`utest/scene_protocol_test.py` covers:

- BREP round-trip for a primitive, boolean result, and compound;
- logical ID, properties, metadata, and camera-policy round-trip;
- the repository organizer model in the repeatable benchmark;
- binary frame and atomic file bundle carriers;
- corrupt payload, truncated frame, and unknown protocol version;
- inline/file carrier selection and superseded generation rejection.
