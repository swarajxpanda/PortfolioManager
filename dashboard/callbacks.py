from dash import Input, Output, html, callback_context


def register_callbacks(app):
    """
    Dropdown toggle callbacks for fragility tab.
    Each dropdown operates independently.
    """

    @app.callback(
        Output("cluster-body", "className"),
        Input("cluster-toggle", "n_clicks"),
        prevent_initial_call=True,
    )
    def toggle_cluster(n):
        if n and n % 2 == 1:
            return "dropdown-body dropdown-open"
        return "dropdown-body dropdown-closed"

    @app.callback(
        Output("bets-body", "className"),
        Input("bets-toggle", "n_clicks"),
        prevent_initial_call=True,
    )
    def toggle_bets(n):
        if n and n % 2 == 1:
            return "dropdown-body dropdown-open"
        return "dropdown-body dropdown-closed"