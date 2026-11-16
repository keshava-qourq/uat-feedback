"""The condition pack: axSpA configuration, loaded from the database.

The architecture's `pack` component holds every clinical constant as data
rather than as code -- ICD-10/CPT/LOINC/HLA-B27/ATC code lists with their
drift equivalences, signal definitions, ASAS criteria and SPARTAN point items,
counter-evidence and demotion rules, tier and reachable-history thresholds,
workup items with their reasoning text, patient-facing copy and the prohibited
term list -- stored as JSONB in `condition_packs` and versioned on every save.

This package exists so the rest of the application has one import path for
that configuration from the first ticket onwards: `app.pack.loader` resolves
the active pack (and answers cleanly when none is active, which the app must
start with), and the validation, versioning and change-log behaviour the API
spec's `GET`/`PUT /api/admin/pack` describe are added here by the tickets that
own them (US-033 onward), not guessed at now.
"""

from app.pack.loader import ActivePack, active_pack, pack_is_active

__all__ = ["ActivePack", "active_pack", "pack_is_active"]
