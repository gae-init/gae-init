"""Gunicorn configuration."""

import contextlib
import os
import threading

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider


# Fix for CPython 3.12 regression (CPython Issue #135413):
# In Python 3.12, Thread._delete() removed the `try...except KeyError:` present in Python <=3.11.
# During interpreter shutdown, daemon threads (such as OpenTelemetry's BatchSpanProcessor)
# attempting to unregister from `_active` raise an unhandled KeyError that Python prints
# to stderr ("Exception ignored in thread started by: ..."), creating false-positive ERROR logs.
_orig_thread_delete = threading.Thread._delete  # ty: ignore[unresolved-attribute] # noqa: SLF001


def _safe_thread_delete(self: threading.Thread) -> None:
    """Safely delete thread from active registry, ignoring KeyError during shutdown."""
    with contextlib.suppress(KeyError):
        _orig_thread_delete(self)


threading.Thread._delete = _safe_thread_delete  # ty: ignore[unresolved-attribute] # noqa: SLF001

bind = f":{os.environ.get('PORT', '8080')}"
workers = 1  # reduced from 4 to 1 (to fit F1 instance class)
threads = 8  # increased from 4 to 8 (better fit for the F1)
worker_class = "gthread"
timeout = 60
max_requests = 1000  # start new worker after this; graceful (prevent memory creep)
max_requests_jitter = 100  # avoid thundering herd restarts (goes with max_requests)


def worker_exit(_server: object, _worker: object) -> None:
    """Shut down OpenTelemetry tracer provider when a worker exits."""
    provider = trace.get_tracer_provider()
    if isinstance(provider, TracerProvider):
        # Flush remaining spans and cleanly stop OpenTelemetry worker thread
        provider.shutdown()
    elif callable(shutdown := getattr(provider, "shutdown", None)):
        shutdown()
