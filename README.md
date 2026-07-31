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
pipeline (`etl.who_loader`).

## Documentation

New here? Start with the guides:

| Guide | What it covers |
|-------|----------------|
| **[GETTING_STARTED.md](GETTING_STARTED.md)** | prerequisites (Python ≥ 3.10) · install · run the engine (Docker) · load the graph · first query |
| **[docs/QUERYING.md](docs/QUERYING.md)** | ask questions via **MCP (Claude)**, the **HTTP API**, or the **Samyama CLI** |
| [schema/surveillance_kg.cypher](schema/surveillance_kg.cypher) | full node/edge schema |

## Quick Start

**Full walkthrough → [GETTING_STARTED.md](GETTING_STARTED.md).** Needs **Python ≥ 3.10** and **Docker**:

```bash
pip install -r requirements.txt
docker run --rm -p 8080:8080 -p 6379:6379 public.ecr.aws/f9f6l5u4/samyama-graph:1.1.0
```

**Load — snapshot (fastest):**
```bash
curl -LO https://github.com/samyama-ai/samyama-graph/releases/download/kg-snapshots-v4/surveillance.sgsnap
curl -X POST http://localhost:8080/api/tenants -H 'Content-Type: application/json' -d '{"id":"surveillance","name":"Disease Surveillance KG"}'
curl -X POST http://localhost:8080/api/tenants/surveillance/snapshot/import -F "file=@surveillance.sgsnap"
```

**Load — from the checked-in WHO GHO data (offline, no download):**
```bash
python -m etl.who_loader --data-dir data --url http://localhost:8080   # → surveillance tenant
```

**Query** (Claude / HTTP / CLI) → see [docs/QUERYING.md](docs/QUERYING.md).

## Use with Claude (MCP)

This repo has no bespoke MCP server, but the `samyama` package ships a generic one:

```bash
samyama-mcp-serve --url http://localhost:8080 --graph surveillance                 # serve the tenant
samyama-mcp-serve --url http://localhost:8080 --graph surveillance --list-tools     # see the tools
```

Register it with Claude and ask in natural language — full steps in **[docs/QUERYING.md](docs/QUERYING.md)**.

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
