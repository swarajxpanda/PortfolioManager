from dash import html
from dashboard.components.fragility_cards import (
    why_metric_strip,
    html_correlation_heatmap,
    cluster_dropdown,
    effective_bets_dropdown,
)


def build_fragility_tab(fragility_data):
    if fragility_data["status"] != "ok":
        return html.Div(
            className="tab-content",
            children=[
                html.Div(
                    className="allocation-card",
                    children=[
                        html.Div(
                            fragility_data.get("warning_message", "Insufficient data to compute fragility."),
                            className="allocation-title",
                        ),
                    ]
                ),
            ]
        )

    return html.Div(
        className="tab-content",
        children=[
            # Premium metric strip (5 cards)
            why_metric_strip(fragility_data["why_section"]),

            # Dropdowns row — clusters + effective bets
            build_dropdowns(fragility_data),

            # Correlation heatmap
            build_heatmap(fragility_data["evidence"]),
        ]
    )


def build_dropdowns(fragility_data):
    clusters = fragility_data["cluster_analysis"]["clusters"]
    enb_diagnostics = fragility_data.get("enb_diagnostics", {})

    return html.Div(
        className="dropdowns-row",
        children=[
            cluster_dropdown(clusters),
            effective_bets_dropdown(enb_diagnostics),
        ]
    )


def build_heatmap(evidence):
    corr_matrix = evidence["correlation_matrix"]
    stock_names = evidence["stock_names"]
    cluster_labels = evidence["cluster_labels"]

    return html_correlation_heatmap(corr_matrix, stock_names, cluster_labels)
