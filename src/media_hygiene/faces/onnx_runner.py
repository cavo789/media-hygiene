"""Run a model file with the ONNX runtime, on the CPU, one thread per process.

`onnxruntime` is imported only here, when faces are asked for: no other command pays
for loading it, and a build without it says so in one sentence, never a traceback.
The process pool already uses every CPU: each model runs on one thread.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Final

from media_hygiene.errors import FaceModelError
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from pathlib import Path

    import numpy as np
    from numpy.typing import NDArray

    from media_hygiene.faces.engine import Runner

RUNTIME_MODULE: Final = "onnxruntime"
_PROVIDERS: Final = ("CPUExecutionProvider",)
_ERRORS_ONLY: Final = 3  # the runtime's log level: no warning about the model's graph


def onnx_runner(model: Path) -> Runner:
    """Load a model file.

    Args:
        model: The `.onnx` file.

    Returns:
        A runner: input tensor → outputs by name.

    Raises:
        FaceModelError: The ONNX runtime is not installed in this build.
    """
    try:
        runtime = importlib.import_module(RUNTIME_MODULE)
    except ModuleNotFoundError as exc:
        raise FaceModelError(
            _("This build cannot find faces: the ONNX runtime is not installed."),
            _("Use the published image, or install the dependencies again: uv sync."),
        ) from exc
    options = runtime.SessionOptions()
    options.log_severity_level = _ERRORS_ONLY
    options.intra_op_num_threads = 1
    options.inter_op_num_threads = 1
    session = runtime.InferenceSession(str(model), options, providers=_PROVIDERS)
    name = str(session.get_inputs()[0].name)
    outputs = tuple(str(output.name) for output in session.get_outputs())

    def run(pixels: NDArray[np.float32]) -> dict[str, NDArray[np.float32]]:
        """Run the model once.

        Args:
            pixels: The input tensor.

        Returns:
            Its outputs by name.
        """
        values = session.run(None, {name: pixels})
        return dict(zip(outputs, values, strict=True))

    return run
