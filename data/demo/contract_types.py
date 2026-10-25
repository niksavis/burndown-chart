from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CalculationContract:
    calculation: str
    scenario: str
    source: str
    field: str
    expected: Any
    producer: str
    surface: str
    backlog: str = ""
    selection: str = "All eight recorded weeks"
    derivation: str = "Synthetic source enumeration"


def make_contracts(
    source: str,
    producer: str,
    surface: str,
    cases: tuple[tuple[str, str, Any], ...],
    *,
    scenario: str = "complete",
    backlog: str = "",
    selection: str = "All eight recorded weeks",
    derivation: str,
) -> tuple[CalculationContract, ...]:
    return tuple(
        CalculationContract(
            name,
            scenario,
            source,
            field,
            expected,
            producer,
            surface,
            backlog,
            selection,
            derivation,
        )
        for name, field, expected in cases
    )
