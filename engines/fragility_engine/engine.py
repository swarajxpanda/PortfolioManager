import numpy as np
import pandas as pd
from sklearn.covariance import LedoitWolf
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform
from numpy.linalg import eigh

from services.fragility_data_service import get_fragility_data
from engines.fragility_engine.settings import *


def compute_ledoit_wolf_covariance(returns_matrix):
    """Compute Ledoit-Wolf shrinkage covariance matrix."""
    lw = LedoitWolf()
    lw.fit(returns_matrix.values)
    return lw.covariance_


def compute_diversification_score(weights, cov_matrix, n_assets):
    """Compute a diversification score combining ENB and HHI metrics."""
    # Step 1: Portfolio variance
    portfolio_variance = weights @ cov_matrix @ weights

    # Step 2: Average single-asset variance
    avg_single_asset_variance = np.mean(np.diag(cov_matrix))

    # Step 3: Normalized variance
    normalized_variance = portfolio_variance / avg_single_asset_variance

    # Step 4: Effective Number of Bets (ENB)
    enb = 1.0 / normalized_variance
    enb = np.clip(enb, 1, n_assets)

    # Step 5: Herfindahl-Hirschman Index
    hhi = np.sum(weights ** 2)

    # Step 6: Raw score
    score = 100.0 * (0.65 * (enb / n_assets) + 0.35 * (1.0 - hhi))

    # Step 7: Clamp to [0, 100]
    score = float(np.clip(score, 0, 100))

    # Step 8: Badge
    if score >= SCORE_HEALTHY:
        badge = "healthy"
    elif score >= SCORE_MODERATE:
        badge = "moderate"
    else:
        badge = "fragile"

    return {
        "score": score,
        "badge": badge,
        "enb": float(enb),
        "hhi": float(hhi),
        "ema_score": score,
    }


def compute_correlation_matrix(returns_matrix):
    """Compute the Pearson correlation matrix from returns."""
    return returns_matrix.corr().values


def perform_hierarchical_clustering(corr_matrix, stock_names, weights):
    """Cluster stocks using hierarchical clustering on correlation distance."""
    n = corr_matrix.shape[0]

    # Convert correlation to distance
    distance = np.sqrt(2.0 * (1.0 - corr_matrix))
    distance = np.clip(distance, 0, 2)
    np.fill_diagonal(distance, 0)

    # Condensed distance matrix
    condensed = squareform(distance)

    # Ward linkage
    Z = linkage(condensed, method="ward")

    # Cut tree at threshold
    threshold_dist = np.sqrt(2.0 * (1.0 - CLUSTER_CORRELATION_THRESHOLD))
    labels = fcluster(Z, t=threshold_dist, criterion="distance")

    # Group stocks by cluster label
    cluster_map = {}
    for idx, label in enumerate(labels):
        label = int(label)
        if label not in cluster_map:
            cluster_map[label] = {"stocks": [], "weight": 0.0}
        cluster_map[label]["stocks"].append(stock_names[idx])
        cluster_map[label]["weight"] += weights[idx]

    # Sort clusters by weight descending
    sorted_clusters = sorted(cluster_map.values(), key=lambda c: c["weight"], reverse=True)

    # Name clusters by weight rank
    clusters = []
    for rank, cluster in enumerate(sorted_clusters, start=1):
        clusters.append({
            "name": f"Cluster {rank}",
            "stocks": cluster["stocks"],
            "weight": float(cluster["weight"]),
            "dominant": False,
        })

    return clusters


def identify_dominant_clusters(clusters, threshold=TOP_CLUSTER_CONCENTRATION_THRESHOLD):
    """Identify whether the top 2 clusters dominate portfolio weight."""
    # Sort by weight descending
    sorted_clusters = sorted(clusters, key=lambda c: c["weight"], reverse=True)

    # Top 2 weight
    top2_weight = sum(c["weight"] for c in sorted_clusters[:2])

    # Mark top 2 as dominant if concentration exceeds threshold
    if top2_weight > threshold:
        for c in sorted_clusters[:2]:
            c["dominant"] = True

    return {
        "clusters": sorted_clusters,
        "top2_weight": float(top2_weight),
        "concentration_alert": top2_weight > threshold,
    }


def compute_average_correlation(returns_matrix, window):
    """Compute the average pairwise correlation over a rolling window."""
    windowed = returns_matrix.iloc[-window:]
    corr = windowed.corr().values

    # Upper triangle excluding diagonal
    upper_indices = np.triu_indices_from(corr, k=1)
    upper_values = corr[upper_indices]

    return float(np.mean(upper_values))


def compute_correlation_regime(returns_matrix):
    """Detect whether correlations are tightening or compressing."""
    short_term = compute_average_correlation(returns_matrix, SHORT_WINDOW)
    long_term = compute_average_correlation(returns_matrix, LONG_WINDOW)
    delta = short_term - long_term

    if delta >= CORRELATION_COMPRESSION:
        status = "compression"
    elif delta >= CORRELATION_TIGHTENING:
        status = "tightening"
    else:
        status = "normal"

    return {
        "short_term": short_term,
        "long_term": long_term,
        "delta": float(delta),
        "status": status,
    }


def compute_portfolio_volatility(weights, cov_matrix):
    """Compute annualized portfolio volatility."""
    return float(np.sqrt(weights @ cov_matrix @ weights))


def create_stress_covariance(cov_matrix, corr_matrix, cluster_labels):
    """Create a stressed covariance matrix by elevating intra-cluster correlations."""
    n = cov_matrix.shape[0]
    stds = np.sqrt(np.diag(cov_matrix))

    # Start with a copy of the correlation matrix
    stressed_corr = corr_matrix.copy()

    # For each pair in the same cluster, set correlation to max(current, 0.85)
    for i in range(n):
        for j in range(i + 1, n):
            if cluster_labels[i] == cluster_labels[j]:
                stressed_corr[i, j] = max(corr_matrix[i, j], 0.85)
                stressed_corr[j, i] = stressed_corr[i, j]

    # Reconstruct covariance from stressed correlations
    stress_cov = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            stress_cov[i, j] = stressed_corr[i, j] * stds[i] * stds[j]

    return stress_cov


def compute_stress_multiplier(weights, cov_matrix, stress_cov):
    """Compute how much portfolio volatility increases under stress."""
    current_vol = compute_portfolio_volatility(weights, cov_matrix)
    stress_vol = compute_portfolio_volatility(weights, stress_cov)

    multiplier = stress_vol / current_vol if current_vol > 0 else 1.0

    if multiplier >= STRESS_HIGH_FRAGILITY:
        status = "high_fragility"
    elif multiplier >= STRESS_FRAGILITY:
        status = "fragile"
    else:
        status = "normal"

    return {
        "current_vol": current_vol,
        "stress_vol": stress_vol,
        "multiplier": float(multiplier),
        "status": status,
    }


def compute_enb_diagnostics(weights, cov_matrix, stock_names, cluster_labels_array, enb_value):
    """Identify dominant portfolio bets via eigen decomposition and generate diagnostics.

    Parameters
    ----------
    weights : np.ndarray
        Portfolio weight vector.
    cov_matrix : np.ndarray
        Covariance matrix.
    stock_names : list[str]
        Names of stocks matching the matrix columns.
    cluster_labels_array : list[str]
        Cluster label for each stock.
    enb_value : float
        Effective Number of Bets already computed.

    Returns
    -------
    dict with ``bets`` and ``recommendations``.
    """
    n = len(stock_names)

    # --- eigen decomposition ---
    eigvals, eigvecs = eigh(cov_matrix)
    # Sort descending by eigenvalue
    order = np.argsort(eigvals)[::-1]
    eigvals = eigvals[order]
    eigvecs = eigvecs[:, order]

    # --- number of factors to analyse ---
    K = max(1, min(round(enb_value), n))

    # --- factor exposure and risk contribution ---
    factor_risk = np.zeros(K)
    for k in range(K):
        exposure = weights @ eigvecs[:, k]
        factor_risk[k] = eigvals[k] * exposure ** 2

    total_factor_risk = factor_risk.sum()
    if total_factor_risk > 0:
        factor_share = factor_risk / total_factor_risk
    else:
        factor_share = np.ones(K) / K

    # --- representative stocks per factor ---
    bets = []
    for k in range(K):
        loadings = np.abs(eigvecs[:, k])
        top_indices = np.argsort(loadings)[::-1][:min(5, n)]
        top_stocks = [stock_names[i] for i in top_indices]
        top_clusters = list(dict.fromkeys(
            cluster_labels_array[i] for i in top_indices
        ))  # unique, order-preserved

        # Auto-label based on cluster composition
        if len(top_clusters) >= 3:
            label = "Broad Market" if k == 0 else f"Factor {k + 1}"
        else:
            label = top_clusters[0] if top_clusters else f"Factor {k + 1}"

        bets.append({
            "label": f"Bet {k + 1} — {label}",
            "risk_share": float(factor_share[k]),
            "stocks": top_stocks,
            "clusters": top_clusters,
            "stock_loadings": {stock_names[i]: float(loadings[i]) for i in top_indices},
        })

    # --- generate recommendations ---
    recommendations = []

    # Rule 1: Market concentration — largest factor > 35%
    if factor_share[0] > 0.35:
        dominant_stocks = bets[0]["stocks"][:3]
        recommendations.append({
            "type": "reduce",
            "title": "Reduce market concentration",
            "message": f"Top factor contributes {factor_share[0]:.0%} of risk",
            "stocks": dominant_stocks,
        })

    # Rule 2: Sector concentration — any bet's clusters all the same
    for bet in bets[1:]:
        if len(bet["clusters"]) == 1 and bet["risk_share"] > 0.10:
            recommendations.append({
                "type": "reduce",
                "title": f"Reduce {bet['clusters'][0]} exposure",
                "message": f"{bet['label']} contributes {bet['risk_share']:.0%} of risk",
                "stocks": bet["stocks"][:3],
            })

    # Rule 3: Missing diversification drivers — if ENB < 50% of assets
    if enb_value < n * 0.5:
        recommendations.append({
            "type": "increase",
            "title": "Increase diversification",
            "message": f"ENB ({enb_value:.1f}) is low relative to {n} assets",
            "stocks": [],
            "suggestions": [
                "Add uncorrelated asset classes",
                "Add defensive sectors",
                "Add international equities",
            ],
        })

    return {
        "bets": bets,
        "recommendations": recommendations,
        "K": K,
    }


def compute_fragility(kite, df):
    """Main entry point: compute all fragility metrics for the portfolio."""
    data = get_fragility_data(kite, df)
    status = data.get("status", "error")

    if status != "ok":
        return {
            "status": status,
            "warning_message": data.get("warning_message"),
            "diversification_score": None,
            "cluster_analysis": None,
            "correlation_regime": None,
            "stress_multiplier": None,
            "actions": [],
            "why_section": None,
            "evidence": None,
        }

    # Extract data
    price_matrix = data["price_matrix"]
    returns_matrix = data["returns_matrix"]
    weights = data["weights"]
    stock_names = data["stock_names"]
    n_assets = len(stock_names)

    # Ledoit-Wolf covariance
    cov_matrix = compute_ledoit_wolf_covariance(returns_matrix)

    # Diversification score
    div_score_result = compute_diversification_score(weights, cov_matrix, n_assets)

    # Correlation matrix
    corr_matrix = compute_correlation_matrix(returns_matrix)

    # Hierarchical clustering
    clusters = perform_hierarchical_clustering(corr_matrix, stock_names, weights)

    # Dominant clusters
    cluster_result = identify_dominant_clusters(clusters)

    # Correlation regime
    corr_regime_result = compute_correlation_regime(returns_matrix)

    # Build cluster labels array for stress covariance
    # Map each stock to its cluster label
    stock_to_cluster = {}
    for cluster in cluster_result["clusters"]:
        for stock in cluster["stocks"]:
            stock_to_cluster[stock] = cluster["name"]
    cluster_labels_array = [stock_to_cluster[name] for name in stock_names]

    # Stress covariance
    stress_cov = create_stress_covariance(cov_matrix, corr_matrix, cluster_labels_array)

    # Stress multiplier
    stress_result = compute_stress_multiplier(weights, cov_matrix, stress_cov)

    # Actions (from actions module, if available)
    actions = []
    try:
        from engines.fragility_engine.actions import generate_hero_actions
        actions = generate_hero_actions(
            cluster_result, stress_result, corr_regime_result
        )
    except ImportError:
        actions = []

    # ENB Diagnostics
    enb_diagnostics = compute_enb_diagnostics(
        weights, cov_matrix, stock_names,
        cluster_labels_array, div_score_result["enb"],
    )

    return {
        "status": "ok",
        "warning_message": data.get("warning_message"),
        "diversification_score": div_score_result,
        "cluster_analysis": cluster_result,
        "correlation_regime": corr_regime_result,
        "stress_multiplier": stress_result,
        "actions": actions,
        "enb_diagnostics": enb_diagnostics,
        "why_section": {
            "diversification_score": div_score_result["score"],
            "diversification_badge": div_score_result["badge"],
            "hhi": div_score_result["hhi"],
            "effective_bets": div_score_result["enb"],
            "total_assets": n_assets,
            "top2_cluster_exposure": cluster_result["top2_weight"],
            "concentration_alert": cluster_result["concentration_alert"],
            "stress_risk_multiplier": stress_result["multiplier"],
            "stress_status": stress_result["status"],
            "current_vol": stress_result["current_vol"],
            "stress_vol": stress_result["stress_vol"],
            "correlation_regime": corr_regime_result["status"],
            "correlation_delta": corr_regime_result["delta"],
            "short_term_corr": corr_regime_result["short_term"],
            "long_term_corr": corr_regime_result["long_term"],
        },
        "evidence": {
            "correlation_matrix": corr_matrix,
            "cluster_labels": cluster_labels_array,
            "stock_names": stock_names,
            "short_term_corr": corr_regime_result["short_term"],
            "long_term_corr": corr_regime_result["long_term"],
            "stress_simulation": {
                "current_vol": stress_result["current_vol"],
                "stress_vol": stress_result["stress_vol"],
                "multiplier": stress_result["multiplier"],
            },
        },
    }
