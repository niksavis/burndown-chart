import json
import math
from typing import Any

from data.demo.contracts import CONTRACTS, CalculationContract
from data.metrics_snapshots import clear_snapshots_cache
from data.persistence import PersistenceBackend
from data.persistence.factory import get_backend
from devtools.calculation_sources import CalculationSources
from utils.runtime import demo_mode


def read_actual(backend: PersistenceBackend, contract: CalculationContract) -> Any:
    profile_id = f"demo-{contract.scenario}"
    if contract.source == "scope":
        scope = backend.get_scope(profile_id, "main")
        return scope.get(contract.field) if scope is not None else None
    if contract.source == "statistics":
        values = backend.get_statistics(profile_id, "main")
        return sum(row[contract.field] for row in values) if values else None
    if contract.source == "budget":
        budget = backend.get_budget_settings(profile_id, "main")
        return True if budget is not None else None
    raise ValueError(f"Unknown diagnostic source: {contract.source}")


def check_contract(contract: CalculationContract, actual: Any) -> dict[str, Any]:
    if isinstance(actual, (int, float)) and isinstance(contract.expected, (int, float)):
        passed = math.isclose(actual, contract.expected, rel_tol=1e-9, abs_tol=1e-9)
    else:
        passed = actual == contract.expected
    if isinstance(actual, float) and not math.isfinite(actual):
        actual = str(actual)
    return {
        "calculation": contract.calculation,
        "scenario": contract.scenario,
        "expected": contract.expected,
        "actual": actual,
        "passed": passed,
        "producer": contract.producer,
        "surface": contract.surface,
        "backlog": contract.backlog,
        "selection": contract.selection,
        "derivation": contract.derivation,
    }


def diagnose(backend: PersistenceBackend) -> list[dict[str, Any]]:
    sources = CalculationSources(backend)
    previous_profile = backend.get_app_state("active_profile_id")
    previous_query = backend.get_app_state("active_query_id")
    try:
        results = []
        for contract in CONTRACTS:
            actual = (
                read_actual(backend, contract)
                if contract.source in {"scope", "statistics", "budget"}
                else sources.read(contract)
            )
            results.append(check_contract(contract, actual))
        return results
    finally:
        backend.set_app_state("active_profile_id", previous_profile)
        backend.set_app_state("active_query_id", previous_query)
        clear_snapshots_cache()


def main() -> int:
    if not demo_mode():
        raise ValueError("Diagnostics require the isolated dev.py launcher")
    results = diagnose(get_backend())
    failed = sum(not result["passed"] for result in results)
    print(json.dumps({"checks": results, "failed": failed}, indent=2, allow_nan=False))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
