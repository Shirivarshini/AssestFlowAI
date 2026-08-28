"""
AssetFlow AI -- Member 4: Data & Integration layer.

This package is a standalone, framework-free module (no FastAPI, no
SQLAlchemy, no React, no LLM SDK, no external services, no API keys)
implementing the multi-source simulation, normalization, reconciliation,
and event simulation described in:

    03_ARCHITECTURE.md
    04_API_CONTRACT.md
    05_DATABASE_SCHEMA.md
    06_ASSET_LIFECYCLE.md
    09_RECONCILIATION_ENGINE.md
    12_EVENT_SYSTEM.md
    13_TEAM_WORKFLOW.md (Member 4 ownership: data/)

Public interface (stable -- Members 1-3 integrate against these):

    load_source_records(scenario="healthy") -> List[SourceRecord]
    normalize_records(source_records)        -> List[NormalizedRecord]
    map_records(records)                     -> Dict[asset_id, Dict[field, List[NormalizedRecord]]]
    detect_conflicts(asset_fields)           -> Dict[field, dict]
    reconcile_asset(asset_id, scenario=...)  -> CanonicalAssetState
    reconcile_all_assets(scenario=...)       -> Dict[asset_id, CanonicalAssetState]
    get_provenance_for_asset(conflicts)      -> List[FieldProvenance]
    create_event(asset_id, event_type, ...)  -> LifecycleEvent
    get_demo_scenario(name)                  -> dict bundle
    list_demo_scenarios()                    -> List[str]

Every function returns plain dataclasses / dicts / lists so the
(not-yet-built) backend and AI layers can consume this module's output
without taking on any of its dependencies.
"""

from data.loader import load_source_records
from data.normalizer import normalize_records
from data.mapper import map_records, get_asset_ids
from data.conflict_detector import detect_conflicts, detect_field_conflict
from data.resolver import resolve_field, resolve_asset_fields
from data.provenance import get_provenance, get_provenance_for_asset
from data.reconciliation import reconcile_asset, reconcile_all_assets
from data.event_simulator import (
    create_event,
    UnsupportedEventTypeError,
    reset_event_counter,
)
from data.fixtures.demo_scenarios import get_demo_scenario, list_demo_scenarios
from data.sources import DEMO_ASSET_ID, SECONDARY_DEMO_ASSET_ID

__all__ = [
    "load_source_records",
    "normalize_records",
    "map_records",
    "get_asset_ids",
    "detect_conflicts",
    "detect_field_conflict",
    "resolve_field",
    "resolve_asset_fields",
    "get_provenance",
    "get_provenance_for_asset",
    "reconcile_asset",
    "reconcile_all_assets",
    "create_event",
    "UnsupportedEventTypeError",
    "reset_event_counter",
    "get_demo_scenario",
    "list_demo_scenarios",
    "DEMO_ASSET_ID",
    "SECONDARY_DEMO_ASSET_ID",
]
