# Portland travel-time log

Hourly travel times for 12 fixed origin-destination pairs around the
**Sept 11 2026 I-5 southbound Rose Quarter closure**, logged from the TomTom
Routing API by a GitHub Actions cron job.

## Why

ODOT closes I-5 southbound between the I-405 and I-84 interchanges for up to
five weeks starting September 11, 2026. PORTAL's loop detectors archive what
happens on the **freeways**, but nobody archives **surface-street** travel
times; live map services show them and throw them away. The agent-based model
at [portland-traffic-abm](https://github.com/darcy0408/portland-traffic-abm)
makes pre-registered predictions about how closure traffic redistributes onto
surface streets, and those predictions can only be graded against data that
starts **before** the closure. This repository is that before-baseline, and
its commit history is the provable timestamp.

## What is logged

One row per pair per hour in `data/traveltimes_YYYY-MM.csv`:
live travel time, free-flow time, historic-typical time, delay, and route
length (a jump in length means the router switched to a detour route).
Pairs, coordinates, and the reason each pair exists are frozen in
`pairs.json`. Two far-field control pairs are included so closure effects
can be separated from region-wide drift (weather, season, API changes).

## Discipline

- The pairs were frozen before logging began and are never edited, only added.
- This data **grades** the model's registered predictions. It is never used
  to tune the model.
- Rows with `status=error:*` record failed API calls; they are kept, not
  cleaned, so gaps are visible.

## Operations

The workflow needs one repository secret, `TOMTOM_API_KEY` (a free
developer.tomtom.com key). Without it every run fails loudly. The
`workflow_dispatch` button on the Actions tab runs a manual smoke test.
