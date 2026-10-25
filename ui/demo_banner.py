from datetime import datetime

import dash_bootstrap_components as dbc

from utils.business_time import business_now
from utils.runtime import demo_mode


def create_demo_banner() -> dbc.Alert | None:
    if not demo_mode():
        return None
    reference = business_now(datetime).date().isoformat()
    return dbc.Alert(
        f"Offline demo - Synthetic data - Evaluation date: {reference}",
        id="demo-mode-banner",
        color="info",
        className="mb-2 py-2",
    )
