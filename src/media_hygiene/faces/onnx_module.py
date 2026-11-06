"""Keep the ONNX runtime's telemetry off.

The official `onnxruntime` wheels hold a Microsoft telemetry client, on by default, that
starts at import time and warns on the console when it cannot save its device id. This
tool promises that nothing leaves the computer: call this before importing the runtime.
"""

from __future__ import annotations

import os
from typing import Final

_NO_TELEMETRY: Final = "ORT_DISABLE_TELEMETRY"


def no_telemetry() -> None:
    """Turn the runtime's telemetry off, for this process and those it starts."""
    os.environ[_NO_TELEMETRY] = "1"
