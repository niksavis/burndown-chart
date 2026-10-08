from __future__ import annotations

import logging
import math
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


def build_correlation_signals(
    statistics_df: pd.DataFrame,
    budget_data: dict[str, Any] | None = None,
    pert_data: dict[str, Any] | None = None,
    deadline: str | None = None,
    bug_metrics: dict[str, Any] | None = None,
    flow_metrics: dict[str, Any] | None = None,
    dora_metrics: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:

    if statistics_df.empty:
        return []

    signals: list[dict[str, Any]] = []

    try:
        _add_h1_h2_h3(signals, statistics_df, budget_data, pert_data)
    except Exception:
        logger.debug(
            "[CorrelationSignals] H1/H2/H3 skipped due to error", exc_info=True
        )

    try:
        _add_h4_wip_lead_time(signals, flow_metrics)
    except Exception:
        logger.debug("[CorrelationSignals] H4 skipped due to error", exc_info=True)

    try:
        _add_h5_bug_velocity_drain(signals, statistics_df, bug_metrics)
    except Exception:
        logger.debug("[CorrelationSignals] H5 skipped due to error", exc_info=True)

    try:
        _add_h6_quality_scope_pressure(signals, statistics_df, bug_metrics)
    except Exception:
        logger.debug("[CorrelationSignals] H6 skipped due to error", exc_info=True)

    try:
        _add_h7_dora_velocity_divergence(signals, statistics_df, dora_metrics)
    except Exception:
        logger.debug("[CorrelationSignals] H7 skipped due to error", exc_info=True)

    return signals


def _velocity_cv(statistics_df: pd.DataFrame) -> float:
    mean = statistics_df["completed_items"].mean()
    if mean <= 0:
        return 0.0
    return float(statistics_df["completed_items"].std() / mean * 100)


def _velocity_split(
    statistics_df: pd.DataFrame,
) -> tuple[float, float]:
    mid = len(statistics_df) // 2
    if mid <= 0:
        return 0.0, 0.0
    recent = float(statistics_df.iloc[mid:]["completed_items"].mean())
    historical = float(statistics_df.iloc[:mid]["completed_items"].mean())
    return recent, historical


def _add_h1_h2_h3(
    signals: list[dict[str, Any]],
    statistics_df: pd.DataFrame,
    budget_data: dict[str, Any] | None,
    pert_data: dict[str, Any] | None,
) -> None:
    if not budget_data:
        return

    cv = _velocity_cv(statistics_df)

    if (
        cv > 40
        and "created_items" in statistics_df.columns
        and statistics_df["created_items"].sum()
        > statistics_df["completed_items"].sum() * 0.2
    ):
        signals.append(
            {
                "id": "unstable_delivery_scope_creep",
                "severity": "danger",
                "message": (
                    "Unstable Delivery + Scope Creep - High velocity "
                    f"variation ({cv:.1f}%) combined with increasing scope "
                    "creates critical delivery risk"
                ),
                "recommendation": (
                    "Dual intervention required: (1) Stabilize velocity "
                    "through consistent team capacity, better story sizing, "
                    "and reduced context switching, (2) Implement strict "
                    "change control to prevent scope additions until delivery "
                    "stabilizes. Consider freezing new features until "
                    "predictability improves."
                ),
            }
        )

    if pert_data:
        runway_weeks = budget_data.get("runway_weeks", 0)
        pert_opt = pert_data.get("pert_optimistic_days", 0)
        pert_pess = pert_data.get("pert_pessimistic_days", 0)
        if (
            runway_weeks
            and not math.isinf(runway_weeks)
            and runway_weeks < 6
            and pert_opt > 0
            and pert_pess > 0
            and (pert_pess - pert_opt) / 7.0 > 4
        ):
            signals.append(
                {
                    "id": "budget_forecast_uncertainty",
                    "severity": "danger",
                    "message": (
                        "Budget Risk + Forecast Uncertainty - Limited "
                        f"budget ({runway_weeks:.1f}w) combined with "
                        "unpredictable delivery creates critical planning risk"
                    ),
                    "recommendation": (
                        "Urgently stabilize project: (1) Define and commit to "
                        "minimum viable scope that fits budget, (2) Increase "
                        "forecast accuracy by breaking stories into smaller "
                        "pieces and reducing WIP, (3) Secure budget contingency "
                        "or prepare for partial delivery. Risk of budget overrun "
                        "or incomplete delivery is high."
                    ),
                }
            )

    if pert_data and len(statistics_df) >= 4:
        recent_v, hist_v = _velocity_split(statistics_df)
        runway_weeks = budget_data.get("runway_weeks", 0)
        pert_forecast_weeks = (
            pert_data.get("pert_time_items", 0) / 7.0
            if pert_data.get("pert_time_items")
            else 0
        )
        if (
            hist_v > 0
            and recent_v > hist_v * 1.15
            and runway_weeks
            and not math.isinf(runway_weeks)
            and pert_forecast_weeks > 0
            and runway_weeks > pert_forecast_weeks + 3
        ):
            velocity_increase = (recent_v / hist_v - 1) * 100
            surplus_weeks = runway_weeks - pert_forecast_weeks
            signals.append(
                {
                    "id": "performance_surplus",
                    "severity": "success",
                    "message": (
                        "Performance Surplus - Team accelerating "
                        f"({velocity_increase:.1f}% increase) while "
                        f"budget has {surplus_weeks:.1f}w headroom"
                    ),
                    "recommendation": (
                        "Opportunity to maximize value delivery: "
                        "(1) Bring forward high-value roadmap items from "
                        "future releases, (2) Invest in technical debt "
                        "reduction or architecture improvements, "
                        "(3) Enhance product quality, UX, or documentation. "
                        "Coordinate with stakeholders to capitalize on this "
                        "favorable position."
                    ),
                }
            )


def _add_h4_wip_lead_time(
    signals: list[dict[str, Any]],
    flow_metrics: dict[str, Any] | None,
) -> None:
    if not flow_metrics or not flow_metrics.get("has_data"):
        return
    wip = flow_metrics.get("avg_wip", 0) or 0
    lead_time = flow_metrics.get("median_flow_time", 0) or 0
    if wip >= 20 and lead_time > 7:
        signals.append(
            {
                "id": "high_wip_long_lead_time",
                "severity": "warning",
                "message": (
                    f"High WIP + Long Lead Time - {wip:.0f} average items in "
                    f"flight with {lead_time:.0f}-day median lead time "
                    "indicates systemic bottleneck"
                ),
                "recommendation": (
                    "Reduce work-in-progress to improve flow: "
                    "(1) Set explicit WIP limits per stage (target < 10 "
                    "active items), (2) Identify and resolve blocked items "
                    "before starting new work, (3) Break large items into "
                    "smaller deliverables, (4) Run a flow efficiency workshop "
                    "to identify the primary constraint stage."
                ),
            }
        )


def _add_h5_bug_velocity_drain(
    signals: list[dict[str, Any]],
    statistics_df: pd.DataFrame,
    bug_metrics: dict[str, Any] | None,
) -> None:
    if not bug_metrics or not bug_metrics.get("has_data"):
        return
    bug_pct = bug_metrics.get("bug_investment_pct", 0) or 0
    if bug_pct < 25:
        return
    recent_v, hist_v = _velocity_split(statistics_df)
    if hist_v > 0 and recent_v < hist_v * 0.9:
        decline_pct = (1 - recent_v / hist_v) * 100
        signals.append(
            {
                "id": "bug_velocity_drain",
                "severity": "warning",
                "message": (
                    f"Bug Load Draining Velocity - {bug_pct:.0f}% of team "
                    "throughput consumed by bugs while delivery velocity "
                    f"has declined {decline_pct:.0f}%"
                ),
                "recommendation": (
                    "Shift capacity to stabilize quality: "
                    "(1) Dedicate a focused sprint to bug resolution before "
                    "new feature work, (2) Identify root causes of bug "
                    "introduction (gaps in testing, unclear requirements), "
                    "(3) Implement bug prevention practices (code review, "
                    "automated tests), (4) Set a bug investment ceiling "
                    "(e.g., 20%) and track adherence weekly."
                ),
            }
        )


def _add_h6_quality_scope_pressure(
    signals: list[dict[str, Any]],
    statistics_df: pd.DataFrame,
    bug_metrics: dict[str, Any] | None,
) -> None:
    if not bug_metrics or not bug_metrics.get("has_data"):
        return
    resolution_rate = bug_metrics.get("resolution_rate", 100) or 100
    if resolution_rate >= 50:
        return
    if "created_items" not in statistics_df.columns:
        return
    created = statistics_df["created_items"].sum()
    completed = statistics_df["completed_items"].sum()
    if created <= completed:
        return
    signals.append(
        {
            "id": "quality_scope_pressure",
            "severity": "danger",
            "message": (
                f"Quality Crisis under Scope Pressure - {resolution_rate:.0f}% "
                "bug resolution rate while backlog is expanding faster than "
                "it is being completed"
            ),
            "recommendation": (
                "Immediate dual action required: "
                "(1) Freeze non-critical scope additions to create capacity "
                "for bug resolution, (2) Triage open bugs and close or "
                "defer low-impact items to reduce burden, "
                "(3) Introduce a quality gate — no new feature work until "
                "resolution rate exceeds 65%, (4) Escalate to stakeholders: "
                "growing scope plus deteriorating quality is unsustainable."
            ),
        }
    )


def _add_h7_dora_velocity_divergence(
    signals: list[dict[str, Any]],
    statistics_df: pd.DataFrame,
    dora_metrics: dict[str, Any] | None,
) -> None:
    if not dora_metrics or not dora_metrics.get("has_data", True):
        return
    tier = (dora_metrics.get("overall_tier") or "").lower()
    if tier not in ("low", "medium"):
        return
    recent_v, hist_v = _velocity_split(statistics_df)
    if hist_v <= 0 or recent_v <= hist_v * 1.1:
        return
    velocity_increase = (recent_v / hist_v - 1) * 100
    signals.append(
        {
            "id": "dora_velocity_divergence",
            "severity": "info",
            "message": (
                f"Delivery Speed Outpacing Process Maturity - Velocity "
                f"increased {velocity_increase:.0f}% but DORA tier is "
                f"{tier.capitalize()}, indicating engineering practices are "
                "not keeping pace with delivery speed"
            ),
            "recommendation": (
                "Invest in engineering foundations to sustain the pace: "
                "(1) Improve deployment pipeline automation to reduce lead "
                "time and failure rate, (2) Add automated tests to protect "
                "quality at higher velocity, (3) Establish change failure "
                "rate and MTTR targets for the team, "
                "(4) Schedule a technical health sprint before the next "
                "velocity push."
            ),
        }
    )
