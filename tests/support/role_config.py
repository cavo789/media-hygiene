"""The head of a `config.toml` with a comment and a protected folder (0532, 0533)."""

from __future__ import annotations

from typing import Final

PROTECTED_CONFIG: Final = """# my comment
[folders]
protected = ['C:\\\\Photos\\\\Master']

"""
