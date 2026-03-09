"""Private helper functions for recommendation signal processing.

Extracts large inline sections from calculate_recommendations into focused
private helpers to keep module size within the 500-line limit.
Part of data/report/generator.py split.
"""

from typing import Any

from data.types import MetricsResult


def _build_deadline_scenario_insights(
    dashboard_metrics: MetricsResult,
    deadline: str | None,
    insights: list[dict],
) -> None:
    """Build PERT-based deadline scenario insights.

    Uses the same calculation method as the app (insights_engine.py).
    Appends insight dicts to the shared insights list in-place.

    Args:
        dashboard_metrics: Dashboard metrics dict (velocity, health, forecast)
        deadline: Deadline date string (YYYY-MM-DD) or None
        insights: Mutable list to append insight dicts to
    """
    if deadline:
        try:
            from datetime import datetime

            import pandas as pd

            deadline_date = pd.to_datetime(deadline)
            if not pd.isna(deadline_date):
                current_date = datetime.combine(
                    datetime.now().date(), datetime.min.time()
                )
                days_to_deadline = max(0, (deadline_date - current_date).days)

                # Use raw PERT days (same as app's pert_most_likely_days)
                pert_most_likely_days = dashboard_metrics.get("pert_time_items", 0)

                # Get PERT range for advanced scenarios
                # Calculate optimistic/pessimistic using PERT formula
                # Optimistic = pert_time * 0.7,
                # Pessimistic = pert_time * 1.3 (approximate)
                pert_optimistic_days = (
                    pert_most_likely_days * 0.7 if pert_most_likely_days else 0
                )
                pert_pessimistic_days = (
                    pert_most_likely_days * 1.3 if pert_most_likely_days else 0
                )

                # A3: Deadline At Risk (CRITICAL)
                if days_to_deadline > 0 and pert_most_likely_days > days_to_deadline:
                    days_over = pert_most_likely_days - days_to_deadline
                    weeks_over = days_over / 7.0
                    insights.append(
                        {
                            "severity": "danger",
                            "message": (
                                "Deadline At Risk - Current forecast shows "
                                f"completion {days_over:.2f} days "
                                f"({weeks_over:.2f} weeks) after deadline"
                            ),
                            "recommendation": (
                                "Escalate immediately. Options: "
                                "(1) Descope to MVP, "
                                "(2) Request deadline extension, "
                                "(3) Increase team capacity (with ramp-up "
                                "risk). Review deadline feasibility with "
                                "stakeholders."
                            ),
                        }
                    )

                # G2: Optimistic Scenario Misses Deadline (CRITICAL)
                elif (
                    days_to_deadline > 0
                    and pert_optimistic_days > 0
                    and pert_optimistic_days > days_to_deadline
                ):
                    days_over = pert_optimistic_days - days_to_deadline
                    insights.append(
                        {
                            "severity": "danger",
                            "message": (
                                "Deadline Unachievable - Even best-case "
                                f"scenario completes {days_over:.0f} days "
                                "after deadline"
                            ),
                            "recommendation": (
                                "Immediate action required. Deadline is "
                                "mathematically unattainable without dramatic "
                                "changes: (1) Aggressively descope to critical "
                                "MVP features only, (2) Negotiate deadline "
                                "extension immediately, (3) Consider increasing "
                                "team size (requires ramp-up time). No "
                                "realistic path exists with current parameters."
                            ),
                        }
                    )

                # G1: Pessimistic Scenario Still Meets Deadline (SUCCESS)
                elif (
                    days_to_deadline > 0
                    and pert_pessimistic_days > 0
                    and pert_pessimistic_days < days_to_deadline
                ):
                    buffer_days = days_to_deadline - pert_pessimistic_days
                    buffer_pct = (
                        (buffer_days / days_to_deadline * 100)
                        if days_to_deadline > 0
                        else 0
                    )
                    insights.append(
                        {
                            "severity": "success",
                            "message": (
                                "High Deadline Confidence - Even pessimistic "
                                "forecast completes "
                                f"{buffer_days:.0f} days before deadline "
                                f"({buffer_pct:.0f}% buffer)"
                            ),
                            "recommendation": (
                                "Strong position. Consider: "
                                "(1) Committing to stretch goals or additional "
                                "features, (2) Adding low-risk quality "
                                "enhancements, (3) Building buffer for technical "
                                "debt or documentation. Use confidence to "
                                "negotiate valuable scope additions."
                            ),
                        }
                    )

                # A2: Forecast Confidence Warning (MEDIUM)
                if (
                    pert_optimistic_days > 0
                    and pert_pessimistic_days > 0
                    and (pert_pessimistic_days - pert_optimistic_days) / 7.0 > 4
                ):
                    range_weeks = (pert_pessimistic_days - pert_optimistic_days) / 7.0
                    insights.append(
                        {
                            "severity": "warning",
                            "message": (
                                "Low Forecast Confidence - Wide prediction "
                                f"range (±{range_weeks:.0f} weeks) indicates "
                                "delivery uncertainty"
                            ),
                            "recommendation": (
                                "Improve predictability by: "
                                "(1) Stabilizing team capacity and reducing "
                                "interruptions, (2) Breaking down large stories "
                                "into smaller chunks, (3) Reducing "
                                "work-in-progress limits, (4) Addressing "
                                "recurring blockers. Use Monte Carlo projections "
                                "for stakeholder communication to set realistic "
                                "expectations."
                            ),
                        }
                    )
        except Exception:
            pass


def _build_budget_forecast_insights(
    extended_metrics: dict[str, Any],
    dashboard_metrics: MetricsResult,
    deadline: str | None,
    insights: list[dict],
) -> None:
    """Build budget vs forecast alignment insights.

    Appends budget exhaustion or surplus insight dicts in-place.

    Args:
        extended_metrics: Extended metrics dict (DORA, Flow, Bug, Budget)
        dashboard_metrics: Dashboard metrics dict
        deadline: Deadline date string for context check
        insights: Mutable list to append insight dicts to
    """
    if "budget" in extended_metrics and deadline:
        try:
            from data.recommendations.budget_signals import (
                build_budget_forecast_signals_from_dashboard,
            )

            budget = extended_metrics["budget"]
            if budget.get("has_data"):
                budget_forecast_signals = build_budget_forecast_signals_from_dashboard(
                    budget, dashboard_metrics
                )
                for signal in budget_forecast_signals:
                    metrics = signal["metrics"]
                    if signal["id"] == "budget_exhaustion_before_completion":
                        insights.append(
                            {
                                "severity": signal["severity"],
                                "message": (
                                    "Budget Exhaustion Before Completion - "
                                    "Budget runs out "
                                    f"{metrics['shortfall_weeks']:.1f} weeks "
                                    "before forecast completion"
                                ),
                                "recommendation": (
                                    "Critical misalignment detected. Forecast "
                                    "requires "
                                    f"{metrics['pert_forecast_weeks']:.1f} weeks "
                                    "but only "
                                    f"{metrics['runway_weeks']:.1f} weeks of budget "
                                    "remain. Required actions: "
                                    "(1) Reduce burn rate by scaling down team, "
                                    "(2) Secure additional budget "
                                    f"({metrics['shortfall_pct']:.0f}% increase "
                                    "needed), or (3) Aggressively descope to fit "
                                    "runway."
                                ),
                            }
                        )
                    elif signal["id"] == "budget_surplus_likely":
                        insights.append(
                            {
                                "severity": signal["severity"],
                                "message": (
                                    "Budget Surplus Likely - Project forecast "
                                    "suggests "
                                    f"{metrics['surplus_weeks']:.1f} weeks of "
                                    "unspent budget"
                                ),
                                "recommendation": (
                                    "Consider value-adding opportunities: "
                                    "(1) Adding high-priority backlog items within "
                                    "scope, (2) Investing in technical debt "
                                    "reduction or quality improvements, "
                                    "(3) Enhancing UX/documentation, or "
                                    "(4) Reallocating surplus to other initiatives. "
                                    "Confirm assumptions and opportunities with "
                                    "stakeholders."
                                ),
                            }
                        )
        except Exception:
            pass
