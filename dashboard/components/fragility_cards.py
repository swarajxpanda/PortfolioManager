from dash import html


# ─────────────────────────────────────────────────────────────
#  Premium Metric Strip  (5 cards matching screenshot)
# ─────────────────────────────────────────────────────────────

def why_metric_strip(why_data):
    """Build a premium 5-card metric strip for the 'Why These Actions?' section."""
    score = why_data["diversification_score"]
    badge = why_data.get("diversification_badge", "")
    hhi = why_data.get("hhi", 0)
    enb = why_data["effective_bets"]
    total_assets = why_data.get("total_assets", 0)
    top2 = why_data["top2_cluster_exposure"]
    concentration_alert = why_data.get("concentration_alert", False)
    multiplier = why_data["stress_risk_multiplier"]
    stress_status = why_data.get("stress_status", "")
    current_vol = why_data.get("current_vol", 0)
    stress_vol = why_data.get("stress_vol", 0)
    regime = why_data["correlation_regime"]
    corr_delta = why_data.get("correlation_delta", 0)
    short_term_corr = why_data.get("short_term_corr", 0)
    long_term_corr = why_data.get("long_term_corr", 0)

    # Card 1: Diversification Score - display badge and HHI
    score_color = "strip-green" if score >= 75 else ("strip-amber" if score >= 50 else "strip-red")
    score_sub = f"{badge.capitalize()} | HHI: {hhi:.2f}"

    # Card 2: Effective Bets - display ENB ratio
    enb_color = "strip-green" if enb >= total_assets * 0.5 else ("strip-amber" if enb >= total_assets * 0.3 else "strip-red")
    enb_ratio = (enb / total_assets * 100) if total_assets > 0 else 0
    enb_sub = f"{enb_ratio:.0f}% of assets"

    # Card 3: Top 2 Cluster Exposure - display alert status
    top2_color = "strip-red" if top2 > 0.60 else ("strip-amber" if top2 > 0.50 else "strip-green")
    top2_sub = f"{'Alert: ' if concentration_alert else ''}Top 2 clusters"

    # Card 4: Stress Risk Multiplier - display volatilities
    mult_color = "strip-red" if multiplier >= 1.6 else ("strip-amber" if multiplier >= 1.4 else "strip-green")
    mult_sub = f"Vol: {current_vol:.2%} → {stress_vol:.2%}"

    # Card 5: Correlation Regime - display short/long term correlation
    regime_display = regime.capitalize()
    regime_color = "strip-red" if regime == "compression" else ("strip-amber" if regime == "tightening" else "strip-green")
    regime_sub = f"Short: {short_term_corr:.2f} | Long: {long_term_corr:.2f}"

    cards = [
        _strip_card("DIVERSIFICATION SCORE", f"{score:.0f} / 100", score_color),
        _strip_card("EFFECTIVE BETS", f"{enb:.1f} of {total_assets}", enb_color),
        _strip_card("TOP 2 CLUSTER EXPOSURE", f"{top2:.0%}", top2_color),
        _strip_card("STRESS RISK MULTIPLIER", f"{multiplier:.2f}×", mult_color),
        _strip_card("CORRELATION REGIME", regime_display, regime_color),
    ]

    return html.Div(className="metric-strip", children=cards)


def _strip_card(title, value, color_class):
    return html.Div(
        className=f"metric-strip-card {color_class}",
        children=[
            html.Div(title, className="strip-title"),
            html.Div(value, className="strip-value"),
        ]
    )


# ─────────────────────────────────────────────────────────────
#  HTML Correlation Heatmap (cluster-grouped, full-width)
# ─────────────────────────────────────────────────────────────

def _corr_cell_color(val):
    if val is None:
        return "transparent"
    abs_val = abs(val)
    if val >= 0:
        if abs_val > 0.7:
            return f"rgba(220, 38, 38, {min(abs_val * 0.35, 0.30)})"
        elif abs_val > 0.5:
            return f"rgba(234, 179, 8, {min(abs_val * 0.25, 0.20)})"
        elif abs_val > 0.3:
            return f"rgba(209, 213, 219, {min(abs_val * 0.4, 0.25)})"
        else:
            return f"rgba(34, 197, 94, {min(abs_val * 0.5, 0.25)})"
    else:
        return f"rgba(34, 197, 94, {min(abs_val * 0.5, 0.25)})"


def _corr_text_color(val):
    abs_val = abs(val)
    if abs_val > 0.7:
        return "#991b1b"
    elif abs_val > 0.5:
        return "#92400e"
    elif abs_val > 0.3:
        return "#6b7280"
    else:
        return "#166534"


def html_correlation_heatmap(corr_matrix, stock_names, cluster_labels):
    """Build an HTML table heatmap grouped by cluster — full width, no scroll."""
    n = len(stock_names)

    # Sort stocks by cluster label to group them
    indexed = list(zip(stock_names, cluster_labels, range(n)))
    indexed.sort(key=lambda x: x[1])
    sorted_names = [x[0] for x in indexed]
    sorted_indices = [x[2] for x in indexed]

    # Abbreviate names for header
    short_names = [name[:5].upper() for name in sorted_names]

    # Header row
    header_cells = [html.Th("", className="hm-corner")]
    for sn in short_names:
        header_cells.append(html.Th(sn, className="hm-header"))
    header = html.Thead(html.Tr(header_cells))

    # Body rows
    rows = []
    for ri, row_idx in enumerate(sorted_indices):
        cells = [html.Td(sorted_names[ri], className="hm-label")]
        for ci, col_idx in enumerate(sorted_indices):
            if ri == ci:
                cells.append(html.Td("", className="hm-cell hm-diag"))
            else:
                val = corr_matrix[row_idx][col_idx]
                bg = _corr_cell_color(val)
                tc = _corr_text_color(val)
                cells.append(
                    html.Td(
                        f"{val:.2f}",
                        className="hm-cell",
                        style={"backgroundColor": bg, "color": tc},
                    )
                )
        rows.append(html.Tr(cells))

    return html.Div(
        className="heatmap-section",
        children=[
            html.Div("PAIRWISE CORRELATION HEATMAP — CLUSTER-GROUPED", className="section-heading"),
            html.Table(
                className="hm-table",
                children=[header, html.Tbody(rows)]
            )
        ]
    )


# ─────────────────────────────────────────────────────────────
#  Cluster Dropdown  (unique id so it works independently)
# ─────────────────────────────────────────────────────────────

def cluster_dropdown(clusters):
    """Expandable section listing each cluster and its stocks."""
    cluster_items = []
    for c in clusters:
        stock_chips = [
            html.Span(s, className="stock-chip") for s in c.get("stocks", [])
        ]
        dominant_badge = ""
        if c.get("dominant"):
            dominant_badge = html.Span("DOMINANT", className="badge-dominant")

        cluster_items.append(
            html.Div(
                className="cluster-item",
                children=[
                    html.Div(
                        className="cluster-header",
                        children=[
                            html.Span(c["name"], className="cluster-name"),
                            html.Span(f"{c['weight']:.0%}", className="cluster-weight"),
                            dominant_badge,
                        ]
                    ),
                    html.Div(className="chip-row", children=stock_chips),
                ]
            )
        )

    return html.Div(
        id="cluster-dropdown-wrapper",
        className="dropdown-section",
        children=[
            html.Div(
                "Clusters",
                id="cluster-toggle",
                className="dropdown-toggle",
                n_clicks=0,
            ),
            html.Div(
                id="cluster-body",
                className="dropdown-body dropdown-closed",
                children=cluster_items,
            ),
        ]
    )


# ─────────────────────────────────────────────────────────────
#  Effective Bets Dropdown  (unique id so it works independently)
# ─────────────────────────────────────────────────────────────

def effective_bets_dropdown(enb_diagnostics):
    """Expandable section showing each bet with risk contribution and stocks."""
    bets = enb_diagnostics.get("bets", [])
    bet_items = []

    for bet in bets:
        stock_chips = [
            html.Span(s, className="stock-chip") for s in bet.get("stocks", [])
        ]

        bet_items.append(
            html.Div(
                className="bet-card",
                children=[
                    html.Div(
                        className="bet-header",
                        children=[
                            html.Span(bet["label"], className="bet-label"),
                            html.Span(
                                f"{bet['risk_share']:.0%} risk",
                                className="bet-risk"
                            ),
                        ]
                    ),
                    html.Div(
                        className="bet-bar-track",
                        children=[
                            html.Div(
                                className="bet-bar-fill",
                                style={"width": f"{bet['risk_share'] * 100:.0f}%"},
                            )
                        ]
                    ),
                    html.Div(className="chip-row", children=stock_chips),
                ]
            )
        )

    return html.Div(
        id="bets-dropdown-wrapper",
        className="dropdown-section",
        children=[
            html.Div(
                "Effective Number of Bets",
                id="bets-toggle",
                className="dropdown-toggle",
                n_clicks=0,
            ),
            html.Div(
                id="bets-body",
                className="dropdown-body dropdown-closed",
                children=bet_items,
            ),
        ]
    )
