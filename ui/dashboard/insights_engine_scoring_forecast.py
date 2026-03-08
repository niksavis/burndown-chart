"""Insights Engine - Deadline and Budget Forecast Scoring."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from data.recommendations.budget_signals import build_budget_forecast_signals_from_pert


def _build_deadline_budget_forecast_insights(
    pert_data: dict[str, Any] | None,
    deadline: str | None,
    budget_data: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Build deadline risk and budget-vs-forecast alignment insights."""
    insights: list[dict[str, Any]] = []

    if pert_data and deadline:
        try:
            deadline_date = pd.to_datetime(deadline)
            if not pd.isna(deadline_date):
                current_date = datetime.combine(
                    datetime.now().date(), datetime.min.time()
                )
                days_to_deadline = max(0, (deadline_date - current_date).days)

                pert_most_likely_days = pert_data.get("pert_time_items", 0)
                pert_optimistic_days = pert_data.get("pert_optimistic_days", 0)
                pert_pessimistic_days = pert_data.get("pert_pessimistic_days", 0)

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
                                "Escalate immediately. Options: (1) Descope to "
                                "MVP and reduce scope by "
                                f"{(days_over / pert_most_likely_days * 100):.2f}%, "
                                "(2) Request deadline extension, (3) Increase "
                                "team capacity (with ramp-up risk). Review "
                                "deadline feasibility with stakeholders."
                            ),
                        }
                    )
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
                                f"scenario completes {days_over:.2f} days "
                                "after deadline"
                            ),
                            "recommendation": (
                                "Immediate action required. Deadline is "
                                "mathematically unattainable without dramatic "
                                "changes: (1) Aggressively descope to critical "
                                "MVP features only, (2) Negotiate deadline "
                                "extension immediately, (3) Consider increasing "
                                "team size (requires ramp-up time). No realistic "
                                "path exists with current parameters."
                            ),
                        }
                    )
                elif (
                    days_to_deadline > 0
                    and pert_pessimistic_days > 0
                    and pert_pessimistic_days < days_to_deadline
                ):
                    buffer_days = days_to_deadline - pert_pessimistic_days
                    insights.append(
                        {
                            "severity": "success",
                            "message": (
                                "High Deadline Confidence - Even pessimistic "
                                f"forecast completes {buffer_days:.2f} days "
                                "before deadline "
                                f"({(buffer_days / days_to_deadline * 100):.2f}% "
                                "buffer)"
                            ),
                            "recommendation": (
                                "Strong position. Consider: (1) Committing to "
                                "stretch goals or additional features, (2) "
                                "Adding low-risk quality enhancements, (3) "
                                "Building buffer for technical debt or "
                                "documentation. Use confidence to negotiate "
                                "valuable scope additions."
                            ),
                        }
                    )

                if budget_data and pert_most_likely_days > 0:
                    baseline_end = budget_data.get("baseline", {}).get(
                        "allocated_end_date"
                    )
                    if baseline_end:
                        baseline_date = pd.to_datetime(baseline_end)
                        forecast_date = current_date + pd.Timedelta(
                            days=pert_most_likely_days
                        )
                        slippage_days = (forecast_date - baseline_date).days

                        if slippage_days > 14:
                            slippage_weeks = slippage_days / 7.0
                            descoping_pct = slippage_days / pert_most_likely_days * 100
                            allocated_weeks = budget_data.get("baseline", {}).get(
                                "time_allocated_weeks", 0
                            )
                            insights.append(
                                {
                                    "severity": "warning",
                                    "message": (
                                        "Forecast Slippage - Project expected "
                                        f"to complete {slippage_weeks:.2f} "
                                        "weeks after planned end date"
                                    ),
                                    "recommendation": (
                                        "Re-evaluate scope priorities and adjust "
                                        "timeline expectations. Current velocity "
                                        "suggests "
                                        f"{(pert_most_likely_days / 7.0):.2f} weeks "
                                        "needed vs "
                                        f"{allocated_weeks:.2f} "
                                        "weeks allocated. Consider descoping "
                                        f"{descoping_pct:.2f}% "
                                        "of remaining work or extending timeline."
                                    ),
                                }
                            )

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
                                f"range (+/-{range_weeks:.2f} weeks) indicates "
                                "delivery uncertainty"
                            ),
                            "recommendation": (
                                "Improve predictability by: (1) Stabilizing "
                                "team capacity and reducing interruptions, "
                                "(2) Breaking down large stories into smaller "
                                "chunks, (3) Reducing work-in-progress limits, "
                                "(4) Addressing recurring blockers. Use Monte "
                                "Carlo projections for stakeholder communication "
                                "to set realistic expectations."
                            ),
                        }
                    )
        except Exception:
            pass

    if pert_data and budget_data:
        try:
            budget_forecast_signals = build_budget_forecast_signals_from_pert(
                budget_data, pert_data
            )
            for signal in budget_forecast_signals:
                metrics = signal["metrics"]
                if signal["id"] == "budget_exhaustion_before_completion":
                    insights.append(
                        {
                            "severity": signal["severity"],
                            "message": (
                                "Budget Exhaustion Before Completion - Budget "
                                "runs out "
                                f"{metrics['shortfall_weeks']:.2f} weeks before "
                                "forecast completion"
                            ),
                            "recommendation": (
                                "Critical misalignment detected. Forecast "
                                "requires "
                                f"{metrics['pert_forecast_weeks']:.2f} weeks "
                                "but only "
                                f"{metrics['runway_weeks']:.2f} weeks of budget "
                                "remain. Required actions: (1) Reduce burn "
                                "rate by scaling down team, (2) Secure "
                                "additional budget "
                                f"({metrics['shortfall_pct']:.2f}% increase "
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
                                f"{metrics['surplus_weeks']:.2f} weeks of "
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

    return insights
