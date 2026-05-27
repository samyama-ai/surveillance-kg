"""Tests for WHO GHO disease surveillance loader.

TDD: sample fixture data mimicking WHO GHO API responses.
"""

import os
import json
import tempfile
import pytest


# --- Sample WHO GHO data fixtures ---

SAMPLE_COUNTRIES = [
    {"Code": "IND", "Title": "India"},
    {"Code": "NGA", "Title": "Nigeria"},
    {"Code": "BRA", "Title": "Brazil"},
]

SAMPLE_REGIONS = [
    {"Code": "SEAR", "Title": "South-East Asia"},
    {"Code": "AFR", "Title": "Africa"},
    {"Code": "AMR", "Title": "Americas"},
]

# Country -> region mapping
SAMPLE_COUNTRY_REGIONS = {
    "IND": "SEAR",
    "NGA": "AFR",
    "BRA": "AMR",
}

SAMPLE_DISEASES = [
    {"IndicatorCode": "CHOLERA_0000000001", "IndicatorName": "Number of reported cases of cholera"},
    {"IndicatorCode": "MALARIA002", "IndicatorName": "Estimated number of malaria cases"},
    {"IndicatorCode": "MDG_0000000020", "IndicatorName": "Tuberculosis incidence (per 100 000 population)"},
]

SAMPLE_DISEASE_DATA = [
    {"SpatialDim": "IND", "TimeDim": "2023", "NumericValue": 187.0,
     "IndicatorCode": "MDG_0000000020"},
    {"SpatialDim": "IND", "TimeDim": "2022", "NumericValue": 196.0,
     "IndicatorCode": "MDG_0000000020"},
    {"SpatialDim": "NGA", "TimeDim": "2023", "NumericValue": 5866.0,
     "IndicatorCode": "CHOLERA_0000000001"},
    {"SpatialDim": "BRA", "TimeDim": "2023", "NumericValue": 150000.0,
     "IndicatorCode": "MALARIA002"},
]

SAMPLE_VACCINE_DATA = [
    {"SpatialDim": "IND", "TimeDim": "2024", "NumericValue": 94.0,
     "IndicatorCode": "WHS4_100", "IndicatorName": "DTP3 coverage"},
    {"SpatialDim": "IND", "TimeDim": "2023", "NumericValue": 91.0,
     "IndicatorCode": "WHS4_100", "IndicatorName": "DTP3 coverage"},
    {"SpatialDim": "NGA", "TimeDim": "2024", "NumericValue": 62.0,
     "IndicatorCode": "WHS4_100", "IndicatorName": "DTP3 coverage"},
]


def _write_fixture(tmpdir, filename, data):
    path = os.path.join(tmpdir, filename)
    with open(path, "w") as f:
        json.dump(data, f)
    return path


@pytest.fixture(scope="module")
def surveillance_data():
    """Create fixture data and load into embedded graph."""
    with tempfile.TemporaryDirectory() as tmpdir:
        _write_fixture(tmpdir, "countries.json", SAMPLE_COUNTRIES)
        _write_fixture(tmpdir, "regions.json", SAMPLE_REGIONS)
        _write_fixture(tmpdir, "country_regions.json", SAMPLE_COUNTRY_REGIONS)
        _write_fixture(tmpdir, "diseases.json", SAMPLE_DISEASES)
        _write_fixture(tmpdir, "disease_data.json", SAMPLE_DISEASE_DATA)
        _write_fixture(tmpdir, "vaccine_data.json", SAMPLE_VACCINE_DATA)

        try:
            from samyama import SamyamaClient
            from etl.helpers import Registry
            from etl.who_loader import load_who_data

            client = SamyamaClient.embedded()
            registry = Registry()
            stats = load_who_data(client, tmpdir, registry)
            yield client, stats, registry
        except ImportError:
            pytest.skip("samyama package not available")


def _q(client, cypher):
    try:
        r = client.query_readonly(cypher, "default")
        return [dict(zip(r.columns, row)) for row in r.records]
    except Exception:
        r = client.query(cypher, "default")
        return [dict(zip(r.columns, row)) for row in r.records]


class TestCountryNodes:
    def test_countries_created(self, surveillance_data):
        client, stats, _ = surveillance_data
        rows = _q(client, "MATCH (c:Country) RETURN c.name ORDER BY c.name")
        names = [r["c.name"] for r in rows]
        assert "India" in names
        assert "Nigeria" in names
        assert "Brazil" in names

    def test_country_count(self, surveillance_data):
        client, _, _ = surveillance_data
        rows = _q(client, "MATCH (c:Country) RETURN count(*) AS c")
        assert rows[0]["c"] == 3

    def test_country_has_iso_code(self, surveillance_data):
        client, _, _ = surveillance_data
        rows = _q(client, "MATCH (c:Country {name: 'India'}) RETURN c.iso_code")
        assert rows[0]["c.iso_code"] == "IND"


class TestRegionNodes:
    def test_regions_created(self, surveillance_data):
        client, _, _ = surveillance_data
        rows = _q(client, "MATCH (r:Region) RETURN r.name ORDER BY r.name")
        names = [r["r.name"] for r in rows]
        assert "South-East Asia" in names
        assert "Africa" in names

    def test_in_region_edges(self, surveillance_data):
        client, _, _ = surveillance_data
        rows = _q(client, """
            MATCH (c:Country {name: 'India'})-[:IN_REGION]->(r:Region)
            RETURN r.name
        """)
        assert rows[0]["r.name"] == "South-East Asia"


class TestDiseaseNodes:
    def test_diseases_created(self, surveillance_data):
        client, _, _ = surveillance_data
        rows = _q(client, "MATCH (d:Disease) RETURN d.name ORDER BY d.name")
        names = [r["d.name"] for r in rows]
        assert any("cholera" in n.lower() for n in names)
        assert any("malaria" in n.lower() for n in names)
        assert any("tuberculosis" in n.lower() for n in names)


class TestDiseaseReports:
    def test_reports_created(self, surveillance_data):
        client, _, _ = surveillance_data
        rows = _q(client, "MATCH (dr:DiseaseReport) RETURN count(*) AS c")
        assert rows[0]["c"] >= 4

    def test_report_linked_to_country(self, surveillance_data):
        client, _, _ = surveillance_data
        rows = _q(client, """
            MATCH (c:Country {name: 'India'})-[:REPORTED]->(dr:DiseaseReport)
            RETURN dr.year, dr.value ORDER BY dr.year DESC
        """)
        assert len(rows) >= 1

    def test_report_linked_to_disease(self, surveillance_data):
        client, _, _ = surveillance_data
        rows = _q(client, """
            MATCH (dr:DiseaseReport)-[:REPORT_OF]->(d:Disease)
            RETURN d.name, dr.value LIMIT 5
        """)
        assert len(rows) >= 1


class TestVaccineCoverage:
    def test_coverage_created(self, surveillance_data):
        client, _, _ = surveillance_data
        rows = _q(client, "MATCH (vc:VaccineCoverage) RETURN count(*) AS c")
        assert rows[0]["c"] >= 3

    def test_coverage_linked_to_country(self, surveillance_data):
        client, _, _ = surveillance_data
        rows = _q(client, """
            MATCH (c:Country {name: 'India'})-[:HAS_COVERAGE]->(vc:VaccineCoverage)
            RETURN vc.year, vc.coverage_pct ORDER BY vc.year DESC
        """)
        assert len(rows) >= 2
        assert rows[0]["vc.coverage_pct"] == 94.0


class TestCrossQueries:
    def test_country_disease_reports(self, surveillance_data):
        client, _, _ = surveillance_data
        rows = _q(client, """
            MATCH (c:Country)-[:IN_REGION]->(r:Region)
            MATCH (c)-[:REPORTED]->(dr:DiseaseReport)-[:REPORT_OF]->(d:Disease)
            RETURN c.name, r.name, d.name, dr.value
            LIMIT 5
        """)
        assert len(rows) >= 1

    def test_low_vaccine_coverage(self, surveillance_data):
        client, _, _ = surveillance_data
        rows = _q(client, """
            MATCH (c:Country)-[:HAS_COVERAGE]->(vc:VaccineCoverage)
            WHERE vc.coverage_pct < 80
            RETURN c.name, vc.coverage_pct
        """)
        assert len(rows) >= 1
        assert any(r["c.name"] == "Nigeria" for r in rows)


class TestStats:
    def test_stats_returned(self, surveillance_data):
        _, stats, _ = surveillance_data
        assert stats["source"] == "who_gho"
        assert stats["country_nodes"] == 3
        assert stats["region_nodes"] == 3
        assert stats["disease_nodes"] == 3
        assert stats["disease_report_nodes"] >= 4
        assert stats["vaccine_coverage_nodes"] >= 3
