from __future__ import annotations

from pathlib import Path
from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)

_backend_app = Path(__file__).resolve().parent.parent / "backend" / "app"
if _backend_app.exists():
    __path__.append(str(_backend_app))
