# Getting Started — Disease Surveillance Knowledge Graph

From `git clone` to your first answer. The **snapshot path** is the fastest, but because the WHO GHO
JSON is checked into `data/`, **build-from-source also works offline** (no download needed).

---

## 1. Prerequisites

- **Python ≥ 3.10** (required by the `samyama` SDK; macOS ships 3.9 — use `python3.10`+).
- **git**
- **Docker** — to run the Samyama engine (needed for the snapshot import and for serving MCP / CLI / API).

## 2. Install

```bash
git clone https://github.com/samyama-ai/surveillance-kg.git
cd surveillance-kg
python3 -m venv .venv && source .venv/bin/activate     # Python >= 3.10
pip install -r requirements.txt
```

## 3. Run the engine (Docker)

```bash
docker run --rm -p 8080:8080 -p 6379:6379 public.ecr.aws/f9f6l5u4/samyama-graph:1.1.0
```

## 4. Load the graph — into the `surveillance` tenant

### Option A — snapshot (recommended, ~seconds)
```bash
curl -LO https://github.com/samyama-ai/samyama-graph/releases/download/kg-snapshots-v4/surveillance.sgsnap
curl -X POST http://localhost:8080/api/tenants -H 'Content-Type: application/json' \
  -d '{"id":"surveillance","name":"Disease Surveillance KG"}'
curl -X POST http://localhost:8080/api/tenants/surveillance/snapshot/import -F "file=@surveillance.sgsnap"
```

### Option B — build from the checked-in WHO GHO data
```bash
python -m etl.who_loader --data-dir data --url http://localhost:8080     # → surveillance tenant
```
*(The `data/` JSON is already in the repo, so this needs no network. To refresh it from the WHO GHO
API: `python -m etl.download_who --data-dir data`. Omit `--url` to build an in-memory graph instead.)*

## 5. Ask your first question

Fastest is **Claude over MCP** — see **[docs/QUERYING.md](docs/QUERYING.md)**. Quick check over HTTP —
the most-reported diseases:

```bash
curl -s -X POST http://localhost:8080/api/query -H 'Content-Type: application/json' -d '{
  "graph": "surveillance",
  "query": "MATCH (c:Country)-[:REPORTED]->(r:DiseaseReport)-[:REPORT_OF]->(d:Disease) RETURN d.name AS disease, count(r) AS reports ORDER BY reports DESC LIMIT 5"
}'
# → Tuberculosis incidence (788), TB deaths excl. HIV+TB (708), dengue fever (683), yellow fever (674), ...
```

## 6. The ETL pipeline

- Data source: **WHO Global Health Observatory (GHO)** OData API (public indicators), checked into `data/`.
- `etl/download_who.py` — (re)fetches the raw WHO GHO JSON into `data/`.
- `etl/who_loader.py` — builds the graph (Country, Region, Disease, DiseaseReport, VaccineCoverage +
  IN_REGION / REPORTED / REPORT_OF / HAS_COVERAGE). Run `python -m etl.who_loader --help`.

## Next
- **[docs/QUERYING.md](docs/QUERYING.md)** — MCP (Claude), HTTP API, and the Samyama CLI
- **[schema/surveillance_kg.cypher](schema/surveillance_kg.cypher)** — full schema
