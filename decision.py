"""
Decision layer: maps perception + sustainability into an actionable recommendation.

Takes the perception JSON (from perception.perceive) and the sustainability record
(from sustainability.get_sustainability_record), applies a small ordered ruleset,
and returns a UI-ready decision dict including:
  - final action (one of the canonical actions below)
  - human-readable label, color, and reason
  - computed impact numbers (CO2 avoided, value, metals)
  - rule_trace: ordered list of which rules fired and what changed, for the
    "Why this recommendation?" panel.

Design notes:
- The class default_action from sustainability_data.json is the *starting* action.
  Modifiers from perception flags can override it.
- Modifiers are applied in priority order; later rules can overwrite earlier ones.
- Every transition appends to rule_trace so the path is fully transparent.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Canonical actions and their UI presentation
# ---------------------------------------------------------------------------

ACTION_LABELS: dict[str, dict[str, str]] = {
    "refurbish_resell": {
        "label": "Refurbish & resell",
        "color": "green",
        "default_reason": "Component in good condition with active resale market.",
    },
    "secure_wipe_then_refurbish": {
        "label": "Secure wipe → refurbish",
        "color": "blue",
        "default_reason": "Data-bearing device. Mandatory NIST 800-88 wipe before resale.",
    },
    "secure_destroy_then_recycle": {
        "label": "Secure destroy → recycle",
        "color": "blue",
        "default_reason": "Data-bearing device with no refurb path. Physical destruction required.",
    },
    "reuse_first": {
        "label": "Reuse",
        "color": "green",
        "default_reason": "Low-value but functional. Reuse before recycling.",
    },
    "metals_recovery": {
        "label": "Recycle (metals recovery)",
        "color": "amber",
        "default_reason": "End-of-life. Route to certified metals recovery.",
    },
    "hazardous_handling": {
        "label": "Hazardous handling",
        "color": "red",
        "default_reason": "Contains hazardous materials. Route to licensed hazmat processor.",
    },
    "manual_review": {
        "label": "Manual review",
        "color": "amber",
        "default_reason": "Low confidence or ambiguous case. Flag for human inspection.",
    },
}

# Hazard flags from sustainability data that should force hazmat handling
# regardless of condition. Soft flags like "do_not_landfill" are informational
# and do NOT trigger hazmat — most components carry them.
# Note: "lithium_battery" deliberately NOT in this set because in our current
# sustainability data it's used for motherboard CMOS coin cells (not the main
# component). If Person C splits that into lithium_coin_cell vs
# lithium_battery_pack, add the latter back here.
_HARD_HAZARD_FLAGS = frozenset(
    {
        "high_voltage_capacitors",
        "mercury",
        "crt",
        "leaking_capacitor",
    }
)

# Conditions that signal damage — used to downgrade refurbish actions.
_DAMAGED_CONDITIONS = frozenset({"poor"})

# Confidence below this threshold escalates to manual review.
_LOW_CONFIDENCE_THRESHOLD = 0.5

# Actions that imply the device will re-enter service (so refurb value applies
# and CO2 is avoided). Other actions imply recycling/disposal.
_REUSE_ACTIONS = frozenset(
    {"refurbish_resell", "secure_wipe_then_refurbish", "reuse_first"}
)

# When refurbish becomes infeasible, what's the next best path?
_RECYCLE_FALLBACK = "metals_recovery"

# CO2 avoided ≈ embodied CO2 if the device is reused instead of remanufactured.
# Sources cite 70-85%; we use 80% as a conservative-ish midpoint.
_CO2_AVOIDED_FRACTION = 0.80


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None:
            return default
        return float(x)
    except (TypeError, ValueError):
        return default


def _pick_refurb_value(sustainability: dict[str, Any], generation_hint: str) -> float:
    """Pick modern vs legacy refurb value; fall back to whichever exists."""
    modern = sustainability.get("refurb_value_modern_usd")
    legacy = sustainability.get("refurb_value_legacy_usd")

    if generation_hint == "modern" and modern is not None:
        return _safe_float(modern)
    if generation_hint == "legacy" and legacy is not None:
        return _safe_float(legacy)
    # unknown generation: be conservative — pick the lower of the two
    if modern is not None and legacy is not None:
        return min(_safe_float(modern), _safe_float(legacy))
    if modern is not None:
        return _safe_float(modern)
    if legacy is not None:
        return _safe_float(legacy)
    return 0.0


def _has_hard_hazard(hazard_flags: list[str] | None) -> tuple[bool, str | None]:
    if not hazard_flags:
        return False, None
    for flag in hazard_flags:
        if flag in _HARD_HAZARD_FLAGS:
            return True, flag
    return False, None


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def recommend_action(
    perception: dict[str, Any],
    sustainability: dict[str, Any],
) -> dict[str, Any]:
    """
    Compute the final action recommendation.

    Args:
        perception: dict from perception.perceive() matching the locked schema.
        sustainability: dict from sustainability.get_sustainability_record(...).

    Returns:
        dict with keys: action, label, color, reason, co2_avoided_kg, value_usd,
        metals_total_g, source, rule_trace.
    """
    trace: list[str] = []

    # --- 1. Read inputs (with sane defaults) ---
    device_class = perception.get("device_class", "unknown")
    condition = (perception.get("condition") or "unknown").lower()
    completeness = (perception.get("completeness") or "unknown").lower()
    confidence = _safe_float(perception.get("confidence"), 0.0)
    data_bearing = bool(perception.get("data_bearing", False))
    contains_hazardous = bool(perception.get("contains_hazardous", False))
    generation_hint = (perception.get("generation_hint") or "unknown").lower()

    component_type = sustainability.get("component_type", "undetected")
    starting_action = sustainability.get("default_action") or "manual_review"
    hazard_flags = sustainability.get("hazard_flags") or []

    # --- 2. Initialize action from sustainability default ---
    action = starting_action
    trace.append(
        f"Starting action from {component_type} default: {starting_action}"
    )

    # --- 3. Apply rules in priority order ---
    # Earlier rules can be overridden by later ones; the last applicable rule wins.

    # Rule R1: Low confidence → manual review (highest priority unless hazardous).
    if confidence < _LOW_CONFIDENCE_THRESHOLD and component_type != "undetected":
        action = "manual_review"
        trace.append(
            f"R1 confidence {confidence:.2f} < {_LOW_CONFIDENCE_THRESHOLD} → manual_review"
        )

    # Rule R2: Undetected component → manual review.
    if component_type == "undetected":
        action = "manual_review"
        trace.append("R2 component_type=undetected → manual_review")

    # Rule R3: Hard hazard from sustainability data → hazmat handling.
    has_hard, hazard_name = _has_hard_hazard(hazard_flags)
    if has_hard:
        action = "hazardous_handling"
        trace.append(
            f"R3 hard hazard flag '{hazard_name}' present → hazardous_handling"
        )

    # Rule R4: VLM-detected hazard → hazmat handling.
    if contains_hazardous:
        action = "hazardous_handling"
        trace.append("R4 perception.contains_hazardous=true → hazardous_handling")

    # Rule R5: Damaged condition downgrades refurbish actions.
    # Data-bearing damaged devices still need secure destruction first.
    if condition in _DAMAGED_CONDITIONS and action in _REUSE_ACTIONS:
        if data_bearing:
            action = "secure_destroy_then_recycle"
            trace.append(
                f"R5a condition={condition} + data_bearing=true → "
                f"secure_destroy_then_recycle"
            )
        else:
            action = _RECYCLE_FALLBACK
            trace.append(
                f"R5b condition={condition} blocks refurbish → {_RECYCLE_FALLBACK}"
            )

    # Rule R6: Major missing parts → cannot refurbish.
    if completeness == "missing_major_parts" and action in _REUSE_ACTIONS:
        if data_bearing:
            action = "secure_destroy_then_recycle"
            trace.append(
                "R6a completeness=missing_major_parts + data_bearing=true → "
                "secure_destroy_then_recycle"
            )
        else:
            action = _RECYCLE_FALLBACK
            trace.append(
                f"R6b completeness=missing_major_parts → {_RECYCLE_FALLBACK}"
            )

    # Rule R7: Data-bearing safety net.
    # If somehow a data-bearing device ended up at refurbish_resell (e.g. SSD
    # default got overridden somewhere upstream), force the wipe step.
    if data_bearing and action == "refurbish_resell":
        action = "secure_wipe_then_refurbish"
        trace.append(
            "R7 data_bearing=true on refurbish_resell → secure_wipe_then_refurbish"
        )

    # --- 4. Compute impact numbers ---
    embodied_co2 = _safe_float(sustainability.get("embodied_co2_kg"), 0.0)
    refurb_value = _pick_refurb_value(sustainability, generation_hint)
    scrap_value = _safe_float(sustainability.get("scrap_value_usd"), 0.0)

    is_reuse_path = action in _REUSE_ACTIONS
    co2_avoided = round(embodied_co2 * _CO2_AVOIDED_FRACTION) if is_reuse_path else 0
    value_usd = round(refurb_value) if is_reuse_path else round(scrap_value)

    metals = sustainability.get("recoverable_metals_g") or {}
    metals_total = round(sum(_safe_float(v) for v in metals.values()), 1)

    # --- 5. Build the reason string ---
    label_info = ACTION_LABELS.get(action, ACTION_LABELS["manual_review"])
    reason = _build_reason(action, perception, label_info["default_reason"])

    # --- 6. Source citation ---
    source = _build_source_citation(sustainability)

    return {
        "action": action,
        "label": label_info["label"],
        "color": label_info["color"],
        "reason": reason,
        "co2_avoided_kg": co2_avoided,
        "value_usd": value_usd,
        "metals_total_g": metals_total,
        "metals_breakdown_g": dict(metals),
        "source": source,
        "rule_trace": trace,
    }


_ACRONYM_CLASSES = frozenset({"gpu", "cpu", "ram", "hdd", "ssd", "psu", "pcb"})


def _format_class(device_class: str | None) -> str:
    """Render device class for prose: acronyms uppercase, others title-case."""
    if not device_class:
        return "device"
    raw = device_class.strip()
    if raw.lower() in _ACRONYM_CLASSES:
        return raw.upper()
    return raw.replace("_", " ")


def _build_reason(action: str, perception: dict[str, Any], default: str) -> str:
    """Compose a contextual reason string mentioning the actual perception inputs."""
    cls = _format_class(perception.get("device_class"))
    condition = perception.get("condition") or "unknown"

    if action == "refurbish_resell":
        return f"{cls} in {condition} condition with active resale market."
    if action == "secure_wipe_then_refurbish":
        return f"Data-bearing {cls} in {condition} condition. Mandatory wipe before resale."
    if action == "secure_destroy_then_recycle":
        return f"Data-bearing {cls} cannot be refurbished. Physical destruction required."
    if action == "reuse_first":
        return f"{cls} is low-value but functional. Reuse preferred over recycling."
    if action == "metals_recovery":
        return f"{cls} routed to certified metals recovery."
    if action == "hazardous_handling":
        return f"{cls} contains hazardous materials. Route to licensed hazmat processor."
    if action == "manual_review":
        conf_pct = int(_safe_float(perception.get("confidence"), 0.0) * 100)
        return f"Confidence {conf_pct}% — flag for human inspection."
    return default


def _build_source_citation(sustainability: dict[str, Any]) -> str:
    """Combine source tags into a short citation string."""
    parts = []
    for key in ("embodied_co2_source", "materials_source", "refurb_source"):
        val = sustainability.get(key)
        if val and val not in parts:
            parts.append(str(val))
    return "; ".join(parts) if parts else "no source"


__all__ = ["recommend_action", "ACTION_LABELS"]
