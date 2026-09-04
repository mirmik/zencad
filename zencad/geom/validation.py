"""Canonical shape validation API."""

from zencad._native.validation import (
    ShapeValidationError,
    ValidationIssue,
    ValidationReport,
)

from .modeling import assert_valid, clean, heal, is_valid, validate

__all__ = [
    "ShapeValidationError",
    "ValidationIssue",
    "ValidationReport",
    "assert_valid",
    "clean",
    "heal",
    "is_valid",
    "validate",
]
