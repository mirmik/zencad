# Shared user cache and Qt-independent configuration

- Date: 2026-08-30
- Status: Accepted
- Kanboard: #2002 “[runtime] Добавить eager-режим и управление cache”

## Context

ZenCad historically constructed EvalCache at import time with the hard-coded
path ~/.zencadcache. The managed runner independently repeated the same
default. This made cache selection inconsistent, required a writable home
directory, and gave headless callers no supported way to relocate or disable
disk caching.

The cache is valuable specifically because it is reused across script reloads
and processes. A directory created for each individual run would defeat that
property.

## Decision

ZenCad has one default cache shared by all ZenCad processes of the current
operating-system user. Its configured path is stored in the user's
Qt-independent ZenCad settings under cache.directory; caching is enabled by
cache.enabled.

The default setting is tempfile.gettempdir()/zencad-cache-<uid>.

On platforms without a numeric UID, ZenCad uses a filesystem-safe user name.
The default directory is created with user-only permissions on POSIX and is
never removed by ZenCad at process exit. The operating system may clean its
temporary area, including across reboot.

Configuration priority, from highest to lowest, is:

1. an explicit in-process call such as
   zencad.configure(cache_dir=..., cache_enabled=...);
2. ZENCAD_CACHE_DIR and ZENCAD_CACHE_DISABLE;
3. the persistent user settings.

The GUI settings dialog edits the persistent values. The managed GUI resolves
the effective configuration and passes it as data to each runner, so GUI,
worker, standalone, and headless execution use the same contract.

Disabling the cache turns off both reads and writes while retaining lazy
evaluation and in-memory values. File exports still execute directly and do
not require a cache directory.

## Rationale

A shared per-user directory retains reuse across runner generations and
separate invocations without requiring a permanent home-directory cache.
Storing the default in settings makes the choice visible and editable.
Environment overrides allow CI, sandboxes, and coding agents to select a
writable location before importing ZenCad, while the Python API lets a script
make an explicit local choice.

The cache must not be writable across operating-system users. EvalCache stores
Python pickle data, so a globally shared writable directory would allow one
user to supply executable serialized data to another.

## Alternatives considered

### One temporary directory per run

Rejected because it prevents reuse across reloads and processes, which is the
main purpose of ZenCad's disk cache.

### Keep ~/.zencadcache as the unconditional default

Rejected because it requires a writable home directory and is awkward for
sandboxed and headless execution.

### One system-wide cache shared by all users

Rejected because EvalCache's pickle representation makes cross-user writes a
code-execution boundary.

### Disable lazy evaluation together with disk caching

Rejected because evaluation timing and disk persistence are independent
concerns. Cache-off mode preserves the existing lazy API.

## Consequences and risks

- The default cache survives ZenCad processes but may be cleared by the host
  temporary-file policy or reboot.
- Users who need cache persistence across temporary-directory cleanup must
  choose a permanent directory in settings, the environment, or Python.
- Concurrent processes share the EvalCache directory. Existing atomic
  temporary-write-and-replace behavior protects individual cache entries, but
  clearing a live cache remains an explicitly disruptive operation.
- A script-level override applies to that Python process. Managed scripts run
  it again in every fresh runner generation.
- Cache schema/version namespacing remains a possible future hardening step.

## Follow-up work

- Complete the separate eager-evaluation portion of #2002.
- Consider explicit cache size/age cleanup policy after measuring real cache
  growth.
