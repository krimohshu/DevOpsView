"""
Task Service - Observability Package

Exports tracing and monitoring utilities.

Usage:
    from src.observability import setup_opentelemetry, traced_operation
"""

from .tracing import (
    setup_opentelemetry,
    get_tracer,
    add_span_attributes,
    add_span_event,
    set_span_error,
    traced_operation,
)

__all__ = [
    "setup_opentelemetry",
    "get_tracer",
    "add_span_attributes",
    "add_span_event",
    "set_span_error",
    "traced_operation",
]
