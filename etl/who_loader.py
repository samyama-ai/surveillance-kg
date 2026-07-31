"""WHO GHO Disease Surveillance loader.

Loads countries, regions, diseases, disease reports, and vaccine coverage
from pre-downloaded WHO GHO JSON files into Samyama graph.

Usage:
    # From pre-downloaded JSON files:
    from etl.who_loader import load_who_data
    load_who_data(client, data_dir, registry)
"""

from __future__ import annotations

import json
import os

from etl.helpers import (
    Registry,
    ProgressReporter,
    batch_create_nodes,
    batch_create_edges,
    create_index,
)


# Default tenant/graph. Matches the published snapshot's tenant, so
# build-from-source and the snapshot import agree.
GRAPH = "surveillance"


def load_who_data(
    client,
    data_dir: str,
    registry: Registry,
    tenant: str = GRAPH,
    years: set[int] | None = None,
) -> dict:
    """Load WHO GHO surveillance data into the graph.

    Expects JSON files in data_dir:
      countries.json, regions.json, country_regions.json,
      diseases.json, disease_data.json, vaccine_data.json

    If ``years`` is given, only DiseaseReport / VaccineCoverage records whose
    reporting year is in that set are loaded (the real WHO records, just scoped
    to a time window). Countries, regions and diseases are always loaded in full.
    """
    print("Disease Surveillance KG: WHO GHO")

    create_index(client, "Country", "iso_code", tenant)
    create_index(client, "Country", "name", tenant)
    create_index(client, "Disease", "indicator_code", tenant)
    create_index(client, "Region", "who_code", tenant)

    country_nodes = 0
    region_nodes = 0
    disease_nodes = 0
    report_nodes = 0
    vaccine_nodes = 0
    in_region_edges = 0
    reported_edges = 0
    report_of_edges = 0
    coverage_edges = 0

    # ── Countries ──
    countries_path = os.path.join(data_dir, "countries.json")
    if os.path.exists(countries_path):
        with open(countries_path) as f:
            countries = json.load(f)
        batch = []
        for c in countries:
            code = c.get("Code", "").strip()
            name = c.get("Title", "").strip()
            if not code or not name:
                continue
            if code in registry.drugs:  # reuse drugs set for country dedup
                continue
            registry.drugs.add(code)
            batch.append(("Country", {"iso_code": code, "name": name}))
            if len(batch) >= 50:
                batch_create_nodes(client, batch, tenant)
                country_nodes += len(batch)
                batch = []
        if batch:
            batch_create_nodes(client, batch, tenant)
            country_nodes += len(batch)
        print(f"  Countries: {country_nodes}")

    # ── Regions ──
    regions_path = os.path.join(data_dir, "regions.json")
    if os.path.exists(regions_path):
        with open(regions_path) as f:
            regions = json.load(f)
        batch = []
        for r in regions:
            code = r.get("Code", "").strip()
            name = r.get("Title", "").strip()
            if not code or not name:
                continue
            batch.append(("Region", {"who_code": code, "name": name}))
        if batch:
            batch_create_nodes(client, batch, tenant)
        region_nodes = len(batch)
        print(f"  Regions: {region_nodes}")

    # ── Country → Region edges ──
    cr_path = os.path.join(data_dir, "country_regions.json")
    if os.path.exists(cr_path):
        with open(cr_path) as f:
            country_regions = json.load(f)
        edge_batch = []
        for iso, who_region in country_regions.items():
            edge_batch.append((
                "Country", "iso_code", iso,
                "Region", "who_code", who_region,
                "IN_REGION", {},
            ))
        in_region_edges = batch_create_edges(client, edge_batch, tenant)
        print(f"  IN_REGION edges: {in_region_edges}")

    # ── Diseases ──
    diseases_path = os.path.join(data_dir, "diseases.json")
    indicator_to_name: dict[str, str] = {}
    if os.path.exists(diseases_path):
        with open(diseases_path) as f:
            diseases = json.load(f)
        batch = []
        for d in diseases:
            code = d.get("IndicatorCode", "").strip()
            name = d.get("IndicatorName", "").strip()
            if not code or not name:
                continue
            indicator_to_name[code] = name
            batch.append(("Disease", {"indicator_code": code, "name": name}))
        if batch:
            batch_create_nodes(client, batch, tenant)
        disease_nodes = len(batch)
        print(f"  Diseases: {disease_nodes}")

    # ── Disease Reports ──
    data_path = os.path.join(data_dir, "disease_data.json")
    if os.path.exists(data_path):
        with open(data_path) as f:
            disease_data = json.load(f)
        report_batch = []
        reported_batch = []
        report_of_batch = []
        for i, rec in enumerate(disease_data):
            country = str(rec.get("SpatialDim", "") or "").strip()
            year = str(rec.get("TimeDim", "") or "").strip()
            value = rec.get("NumericValue")
            if value is None:
                raw = rec.get("Value")
                try:
                    value = float(str(raw).replace(",", "").strip())
                except (TypeError, ValueError):
                    value = None
            indicator = str(rec.get("IndicatorCode", "") or "").strip()
            if not country or not year or value is None:
                continue
            if years is not None and (not year.isdigit() or int(year) not in years):
                continue
            rid = f"DR-{country}-{indicator}-{year}"
            props = {"id": rid, "year": int(year) if year.isdigit() else year}
            if isinstance(value, (int, float)):
                props["value"] = value
            report_batch.append(("DiseaseReport", props))
            reported_batch.append((
                "Country", "iso_code", country,
                "DiseaseReport", "id", rid,
                "REPORTED", {},
            ))
            report_of_batch.append((
                "DiseaseReport", "id", rid,
                "Disease", "indicator_code", indicator,
                "REPORT_OF", {},
            ))
        # Batch create in chunks of 100
        for i in range(0, len(report_batch), 100):
            chunk = report_batch[i:i+100]
            batch_create_nodes(client, chunk, tenant)
        report_nodes = len(report_batch)
        reported_edges = batch_create_edges(client, reported_batch, tenant)
        report_of_edges = batch_create_edges(client, report_of_batch, tenant)
        print(f"  Disease reports: {report_nodes} nodes, {reported_edges} REPORTED, "
              f"{report_of_edges} REPORT_OF")

    # ── Vaccine Coverage ──
    vaccine_path = os.path.join(data_dir, "vaccine_data.json")
    if os.path.exists(vaccine_path):
        with open(vaccine_path) as f:
            vaccine_data = json.load(f)
        vc_batch = []
        cov_edge_batch = []
        for rec in vaccine_data:
            country = str(rec.get("SpatialDim", "") or "").strip()
            year = str(rec.get("TimeDim", "") or "").strip()
            value = rec.get("NumericValue")
            indicator = str(rec.get("IndicatorCode", "") or "").strip()
            antigen = str(rec.get("IndicatorName", "") or "").strip()
            if not country or not year or value is None:
                continue
            if years is not None and (not year.isdigit() or int(year) not in years):
                continue
            vid = f"VC-{country}-{indicator}-{year}"
            props = {
                "id": vid,
                "year": int(year) if year.isdigit() else year,
                "coverage_pct": value,
                "antigen": antigen,
            }
            vc_batch.append(("VaccineCoverage", props))
            cov_edge_batch.append((
                "Country", "iso_code", country,
                "VaccineCoverage", "id", vid,
                "HAS_COVERAGE", {},
            ))
        for i in range(0, len(vc_batch), 100):
            chunk = vc_batch[i:i+100]
            batch_create_nodes(client, chunk, tenant)
        vaccine_nodes = len(vc_batch)
        coverage_edges = batch_create_edges(client, cov_edge_batch, tenant)
        print(f"  Vaccine coverage: {vaccine_nodes} nodes, {coverage_edges} edges")

    stats = {
        "source": "who_gho",
        "country_nodes": country_nodes,
        "region_nodes": region_nodes,
        "disease_nodes": disease_nodes,
        "disease_report_nodes": report_nodes,
        "vaccine_coverage_nodes": vaccine_nodes,
        "in_region_edges": in_region_edges,
        "reported_edges": reported_edges,
        "report_of_edges": report_of_edges,
        "coverage_edges": coverage_edges,
    }
    total_nodes = country_nodes + region_nodes + disease_nodes + report_nodes + vaccine_nodes
    total_edges = in_region_edges + reported_edges + report_of_edges + coverage_edges
    print(f"  Total: {total_nodes} nodes, {total_edges} edges")
    return stats


def main(argv: list[str] | None = None) -> None:
    """CLI entrypoint: load the shipped WHO GHO JSON into a Samyama graph.

        python -m etl.who_loader --data-dir data --url http://localhost:8080
        python -m etl.who_loader --data-dir data                 # in-memory (embedded)
    """
    import argparse

    from samyama import SamyamaClient

    parser = argparse.ArgumentParser(
        prog="surveillance-loader",
        description="Load WHO GHO disease-surveillance data into Samyama.",
    )
    parser.add_argument(
        "--data-dir", default="data",
        help="Directory with the WHO GHO JSON files (default: %(default)s).",
    )
    parser.add_argument(
        "--url", default=None,
        help="Connect to a running Samyama engine (default: in-memory embedded).",
    )
    parser.add_argument(
        "--tenant", default=GRAPH,
        help="Graph tenant name (default: %(default)s).",
    )
    args = parser.parse_args(argv)

    client = SamyamaClient.connect(args.url) if args.url else SamyamaClient.embedded()
    load_who_data(client, args.data_dir, Registry(), tenant=args.tenant)


if __name__ == "__main__":
    main()
