import importlib
import math

import pytest

from data.demo.contracts import CONTRACTS, CalculationContract
from devtools.diagnostics import check_contract


@pytest.mark.parametrize(
    "actual, passed",
    [(6.5, True), (5.0, False), (None, False), (math.nan, False), (math.inf, False)],
)
def test_diagnostic_exposes_wrong_and_unavailable_values(
    actual: float | None, passed: bool
) -> None:
    contract = next(
        contract
        for contract in CONTRACTS
        if contract.calculation == "fractional-points"
    )
    result = check_contract(contract, actual)
    assert result["passed"] is passed
    assert result["expected"] == 6.5
    assert result["backlog"] == "burndownchart-imp021"
    assert result["actual"] == (
        str(actual)
        if isinstance(actual, float) and not math.isfinite(actual)
        else actual
    )


def test_missing_budget_is_distinct_from_measured_zero() -> None:
    contract = CalculationContract(
        "budget", "missing-signals", "budget", "configured", None, "budget", "dashboard"
    )
    assert check_contract(contract, None)["passed"]
    assert not check_contract(contract, 0)["passed"]


def test_contracts_have_unique_addresses_and_real_producer_references() -> None:
    addresses = [(contract.scenario, contract.calculation) for contract in CONTRACTS]
    assert len(addresses) == len(set(addresses))
    for contract in CONTRACTS:
        module, name = contract.producer.rsplit(".", 1)
        if ".sqlite.budget.BudgetMixin" in module:
            module, class_name = module.rsplit(".", 1)
            owner = getattr(importlib.import_module(module), class_name)
        else:
            owner = importlib.import_module(module)
        assert callable(getattr(owner, name))
