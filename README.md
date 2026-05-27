# surveillance-kg

Disease Surveillance Knowledge Graph built from the WHO Global Health Observatory
(GHO). Models countries, WHO regions, notifiable diseases, annual disease reports
and childhood vaccine coverage so outbreak / surveillance questions can be answered
in Cypher on the Samyama engine.

![Disease surveillance demo](demo/surveillance.gif)

- **7 node labels**: Country, Region, Disease, DiseaseReport, VaccineCoverage, AMRProfile, HealthIndicator
- **7 edge types**: IN_REGION, REPORTED, REPORT_OF, HAS_COVERAGE, COVERAGE_FOR, HAS_AMR, HAS_INDICATOR
- **Source**: WHO Global Health Observatory (GHO) OData API (public indicators)
- **Cross-KG bridge**: `Country.iso_code` joins to health-systems-kg and health-determinants-kg

See `schema/surveillance_kg.cypher` for the full schema and `etl/` for the ingest
pipeline (`etl.who_loader.load_who_data`).

## Demo

A narrated walkthrough (load WHO GHO surveillance data → most-reported diseases →
cholera outbreak hotspots → childhood-vaccine immunity gaps):

```bash
python -m demo.demo                                            # run live
asciinema rec --overwrite --cols 92 --rows 32 --idle-time-limit 2.0 \
  -c "bash -c 'source ~/projects/venv/bin/activate && PYTHONUNBUFFERED=1 python -m demo.demo'" \
  demo/surveillance.cast                                       # re-record
agg demo/surveillance.cast demo/surveillance.gif               # cast → gif
```

The demo scopes the reporting window to 2016-2019 for a snappy load; every value is
real WHO GHO data (no synthetic records).
