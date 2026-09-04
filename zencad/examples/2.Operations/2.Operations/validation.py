#!/usr/bin/env python3
"""Structured validation with explicit cleanup and healing."""

import json

import zencad


source = zencad.box(10) + zencad.box(10).right(10)
report = source.validate()
assert report.valid
print(json.dumps(report.to_dict(), sort_keys=True))

cleaned = source.clean()
healed = cleaned.heal()
healed.assert_valid()

zencad.display(source.left(12), color=zencad.yellow)
zencad.display(healed.right(12), color=zencad.green)
zencad.show()
