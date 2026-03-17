"""
Action generation logic for the Portfolio Fragility Engine.

Produces up to 3 deterministic hero actions based on cluster concentration,
stress multiplier, and correlation regime analysis.
"""

from engines.fragility_engine.settings import (
    CLUSTER_TRIM_THRESHOLD,
    CLUSTER_AVOID_THRESHOLD,
    DEFENSIVE_MIN_THRESHOLD,
    TOP_CLUSTER_CONCENTRATION_THRESHOLD,
    STRESS_FRAGILITY,
)


def generate_hero_actions(cluster_analysis, stress_multiplier, correlation_regime):
    """Generate up to 3 prioritised hero actions for the fragility dashboard.

    Priority order:
        1. TRIM        — top-2 cluster weight exceeds concentration threshold
        2. AVOID_ADDING — any single cluster weight exceeds avoid threshold
        3. INCREASE     — smallest cluster is under-represented or stress is elevated

    Args:
        cluster_analysis: dict with ``clusters`` list, ``top2_weight``, etc.
        stress_multiplier: dict with ``multiplier``, ``status``, etc.
        correlation_regime: dict with ``short_term``, ``long_term``, ``delta``, ``status``.

    Returns:
        list[dict]: Up to 3 action dicts, or a single STABLE action if nothing fires.
    """
    actions = []

    # 1. TRIM — top-2 concentration too high
    if cluster_analysis.get("top2_weight", 0) > TOP_CLUSTER_CONCENTRATION_THRESHOLD:
        actions.append(format_trim_action(cluster_analysis))

    # 2. AVOID_ADDING — any single cluster above avoid threshold
    clusters = cluster_analysis.get("clusters", [])
    if any(c.get("weight", 0) > CLUSTER_AVOID_THRESHOLD for c in clusters):
        actions.append(format_avoid_action(cluster_analysis))

    # 3. INCREASE — smallest cluster under-represented or stress elevated
    if clusters:
        smallest_weight = min(c.get("weight", 0) for c in clusters)
        if (
            smallest_weight < DEFENSIVE_MIN_THRESHOLD
            or stress_multiplier.get("multiplier", 0) > STRESS_FRAGILITY
        ):
            actions.append(format_increase_action(cluster_analysis, stress_multiplier))

    # Cap at 3 actions
    actions = actions[:3]

    # Fallback when nothing triggered
    if not actions:
        return [
            {
                "type": "STABLE",
                "message": "Structure Stable — No Rebalancing Required",
                "badge": "success",
            }
        ]

    return actions


def format_trim_action(cluster_analysis):
    """Build a TRIM action targeting the largest cluster.

    The trim range is derived from how far ``top2_weight`` exceeds
    ``CLUSTER_TRIM_THRESHOLD``.

    Args:
        cluster_analysis: dict with ``clusters`` and ``top2_weight``.

    Returns:
        dict with keys ``type``, ``cluster``, ``message``, ``badge``.
    """
    clusters = sorted(
        cluster_analysis.get("clusters", []),
        key=lambda c: c.get("weight", 0),
        reverse=True,
    )
    largest = clusters[0]
    cluster_name = largest["name"]

    excess = cluster_analysis.get("top2_weight", 0) - CLUSTER_TRIM_THRESHOLD
    lower = round(excess * 100 - 2)
    upper = round(excess * 100 + 3)

    # Clamp bounds
    lower = max(lower, 1)
    upper = max(upper, lower + 1)

    message = f"Reduce {cluster_name} by {lower}\u2013{upper}%"

    return {
        "type": "TRIM",
        "cluster": cluster_name,
        "message": message,
        "badge": "danger",
    }


def format_avoid_action(cluster_analysis):
    """Build an AVOID_ADDING action for the most concentrated cluster.

    Selects the cluster with the highest weight among those exceeding
    ``CLUSTER_AVOID_THRESHOLD``.

    Args:
        cluster_analysis: dict with ``clusters``.

    Returns:
        dict with keys ``type``, ``cluster``, ``message``, ``badge``.
    """
    candidates = [
        c
        for c in cluster_analysis.get("clusters", [])
        if c.get("weight", 0) > CLUSTER_AVOID_THRESHOLD
    ]
    # Pick the largest offender
    target = max(candidates, key=lambda c: c.get("weight", 0))
    cluster_name = target["name"]

    message = (
        f"No new positions in {cluster_name} "
        f"\u2014 marginal diversification benefit is low"
    )

    return {
        "type": "AVOID_ADDING",
        "cluster": cluster_name,
        "message": message,
        "badge": "warning",
    }


def format_increase_action(cluster_analysis, stress_multiplier):
    """Build an INCREASE action targeting the least-represented cluster.

    If the portfolio is under stress (status != ``"normal"``), the message
    additionally notes the stress-fragility benefit.

    Args:
        cluster_analysis: dict with ``clusters``.
        stress_multiplier: dict with ``status``.

    Returns:
        dict with keys ``type``, ``cluster``, ``message``, ``badge``.
    """
    clusters = cluster_analysis.get("clusters", [])
    smallest = min(clusters, key=lambda c: c.get("weight", 0))
    cluster_name = smallest["name"]

    message = f"Increase allocation to {cluster_name} to improve diversification"

    if stress_multiplier.get("status") != "normal":
        message += " and reduce stress fragility"

    return {
        "type": "INCREASE",
        "cluster": cluster_name,
        "message": message,
        "badge": "success",
    }
