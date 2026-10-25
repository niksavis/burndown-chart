# Synthetic calculation catalogue

`data.demo.contracts.CONTRACTS` is the executable catalogue.
The diagnostic report includes each field, source selection, derivation and backlog reference.
Run it with `.venv/bin/python dev.py diagnose`.
An unsuccessful exit status preserves known numerical disagreements.
No current wrong result becomes a golden expected value.

| Family | Source of independent expectations | Contract file |
| --- | --- | --- |
| Scope totals and delivery rates | Enumerated48items/96points,32items/64points completed | `contracts.py` |
| Every recorded week | Four completions/eight points, six creations/twelve points, cumulative net2/4 | `weekly_contracts.py` |
| Scope growth and stability | Zero initial backlog, creation/delivery1.5, explicit threshold calibration | `scope_contracts.py` |
| Daily/weekly forecasts and pace | Constant4items/8points perweek,16/32remaining,28day completion | `forecast_contracts.py` |
| Statistics and confidence | Known constant, singleton, alternating-zero and changing delivery sequences | `contracts.py`, `forecast_contracts.py` |
| Mounted Dashboard probability | Values observed at the real render boundary, using explicit conditional forecast inputs | `forecast_contracts.py` |
| Flow and DORA | Four work types, explicit20issue lead-time sample, eight production releases, two failures | `contracts.py` |
| Active Work and Sprint |46epic children, two unparented; known tracked membership and moved/reopened issues | `work_contracts.py` |
| Bugs | Eight bugs,54hour resolution; stalled4open with known ages and closure rates | `contracts.py`, `ancillary_contracts.py` |
| Health | Empty availability, stage bands, and explicit policy calibrations | `health_contracts.py` |
| Recommendations | Created/completed populations, stable and accelerating/declining sequences | `recommendation_contracts.py` |
| Historical budget | Recorded completion cohorts allocated at their effective historical cost | `budget_contracts.py` |
| Exported report | Same source population, units and selected weeks as the app | `report_contracts.py` |
| EWMA and current-week blend | Constant observations and configured Thursday60/40 weights | `ancillary_contracts.py` |

Some distinctions are necessary to interpret the catalogue:

- A missing named output is an error. An emitted unavailable value can satisfy an unavailable contract.
- Recorded zero delivery remains an observation. An absent week is not a measured zero.
- A sample statistic needs its actual sample size. One observation cannot supply a measured sample standard deviation.
- Constant-rate probability contracts are conditional model checks. They do not claim unconditional certainty about future work.
- The selected20issue lead sample is separate from pooled or weekly DORA populations.
- Budget allocation contracts use each completed weekly cohort and its effective cost. They do not claim cash expenditure measurements.
- Calendar-deadline calibrations explicitly use midnight January29 through midnight February26.
  The launcher business evaluation time remains January29 noonUTC.
- Health calibrations expose normalization defects without adopting the app's current composite67as an oracle.
- Production filtering belongs to the actual weekly and rendering paths as well as direct calculator calls.

The specialist completion review identified remaining adapter and availability coverage.
Those items remain listed in [Offline development](offline_development.md#remaining-coverage-work).
