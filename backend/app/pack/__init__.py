"""The condition pack: all condition logic, as configuration data.

Every clinical constant -- code lists with their systems, signal definitions,
criteria (set-based and point-based), counter-evidence and demotion rules,
tier and history thresholds, suggested workup items with their reasoning text,
the patient-facing copy strings and the prohibited-term list -- lives in a
declarative data file under `app/pack/packs/`, never in application code
(NFR-019).

`app.pack.registry` loads and validates those files and exposes a generic,
key-based API over them; `app.pack.loader` resolves the pack stored in the
database when one has been saved there. Both answer cleanly when no pack is
active, which is the state the application starts in.
"""

from app.pack.loader import ActivePack, active_pack, pack_is_active
from app.pack.registry import active_pack_status, get_active_pack, log_active_pack

__all__ = [
    "ActivePack",
    "active_pack",
    "active_pack_status",
    "get_active_pack",
    "log_active_pack",
    "pack_is_active",
]
