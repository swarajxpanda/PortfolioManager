import sqlite3, json

DB = "settings.db"

DEFAULT = {
    "groups": {
        "Metals": [],
        "US Equity": [],
        "Indian Equity ETF": [],
        "Indian Equity": []
    },
    "targets": {
        "Metals": [15, 18],
        "US Equity": [15, 18],
        "Indian Equity ETF": [20, 24],
        "Indian Equity": [40, 50]
    },
    "concentration": {
        "top5": 35,
        "single": 5
    }
}

def _ensure_table(conn):
    conn.execute("CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY, config TEXT)")


def get_settings():
    conn = sqlite3.connect(DB)
    _ensure_table(conn)

    row = conn.execute("SELECT config FROM settings WHERE id=1").fetchone()
    conn.close()

    return json.loads(row[0]) if row else DEFAULT


def save_settings(config: dict):
    conn = sqlite3.connect(DB)
    _ensure_table(conn)

    # ensure targets exist for every group
    for group in config.get("groups", {}):
        if group not in config.get("targets", {}):
            config["targets"][group] = [0, 0]

    # remove stale targets for deleted groups
    stale = [g for g in config.get("targets", {}) if g not in config.get("groups", {})]
    for g in stale:
        del config["targets"][g]

    conn.execute(
        "INSERT INTO settings (id, config) VALUES (1, ?) "
        "ON CONFLICT(id) DO UPDATE SET config = excluded.config",
        (json.dumps(config),)
    )
    conn.commit()
    conn.close()


def reset_settings():
    conn = sqlite3.connect(DB)
    _ensure_table(conn)

    conn.execute("DELETE FROM settings WHERE id=1")
    conn.commit()
    conn.close()

    return DEFAULT