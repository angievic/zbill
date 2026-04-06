from __future__ import annotations

import uuid
from datetime import datetime, timezone


def unique_zbill_runtime_dir_name() -> str:
    """Nombre de carpeta único por ejecución; siempre termina en ``-zbill-runtime``."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{ts}-{uuid.uuid4().hex[:8]}-zbill-runtime"
