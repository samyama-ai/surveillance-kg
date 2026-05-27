"""Download WHO GHO disease surveillance data.

Fetches countries, regions, disease indicators, case/death data,
and vaccine coverage from the WHO GHO OData API.

Usage:
    python -m etl.download_who --data-dir data
    python -m etl.download_who --data-dir data --diseases cholera,malaria,tb
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests

GHO_BASE = "https://ghoapi.azureedge.net/api"

# Key disease indicators to fetch
DISEASE_INDICATORS = {
    # Infectious diseases — case counts
    "CHOLERA_0000000001": "Number of reported cases of cholera",
    "CHOLERA_0000000002": "Number of reported deaths from cholera",
    "MALARIA002": "Estimated number of malaria cases",
    "MALARIA001": "Malaria - number of reported deaths",
    "MDG_0000000020": "Tuberculosis incidence (per 100 000 population)",
    "TB_e_mort_exc_tbhiv_num": "TB deaths (excluding HIV+TB)",
    "MENING_2": "Number of suspected meningitis cases reported",
    "MENING_1": "Number of suspected meningitis deaths reported",
    "WHS3_41": "Number of reported cases of yellow fever",
    "WHS3_43": "Reported cases of dengue fever",
    # HIV
    "HIV_0000000001": "Estimated number of people living with HIV",
    "HIV_0000000026": "Number of new HIV infections",
    "HIV_0000000006": "Number of people dying from HIV-related causes",
    # NTDs
    "NTD_YAWS1": "Number of reported cases of yaws",
    "NTD_LEPROSY0001": "Number of new leprosy cases",
}

# Vaccine coverage indicators
VACCINE_INDICATORS = {
    "WHS4_100": "DTP3 immunization coverage (%)",
    "WHS8_110": "MCV1 immunization coverage (%)",
    "bcgv": "BCG immunization coverage (%)",
    "pol3v": "Polio3 immunization coverage (%)",
    "fullv": "Full immunization coverage (%)",
    "HepB3v": "HepB3 immunization coverage (%)",
    "rotacv": "Rotavirus vaccine coverage (%)",
    "pcv3v": "PCV3 immunization coverage (%)",
}

# Mortality / general health indicators
HEALTH_INDICATORS = {
    "WHOSIS_000001": "Life expectancy at birth (years)",
    "WHOSIS_000002": "Healthy life expectancy at birth (years)",
    "MDG_0000000001": "Infant mortality rate (per 1000 live births)",
    "MDG_0000000007": "Under-five mortality rate (per 1000 live births)",
    "NCDMORT3070": "Probability of dying from NCDs between 30-70 years (%)",
    "WSH_SANITATION_SAFELY_MANAGED": "Safely managed sanitation (%)",
    "WSH_WATER_SAFELY_MANAGED": "Safely managed drinking water (%)",
}

# WHO region mapping (hardcoded — stable)
WHO_REGION_MAP = {
    "AFG": "EMR", "ALB": "EUR", "DZA": "AFR", "AGO": "AFR", "ARG": "AMR",
    "ARM": "EUR", "AUS": "WPR", "AUT": "EUR", "AZE": "EUR", "BHR": "EMR",
    "BGD": "SEAR", "BLR": "EUR", "BEL": "EUR", "BLZ": "AMR", "BEN": "AFR",
    "BTN": "SEAR", "BOL": "AMR", "BIH": "EUR", "BWA": "AFR", "BRA": "AMR",
    "BRN": "WPR", "BGR": "EUR", "BFA": "AFR", "BDI": "AFR", "KHM": "WPR",
    "CMR": "AFR", "CAN": "AMR", "CAF": "AFR", "TCD": "AFR", "CHL": "AMR",
    "CHN": "WPR", "COL": "AMR", "COM": "AFR", "COG": "AFR", "COD": "AFR",
    "CRI": "AMR", "CIV": "AFR", "HRV": "EUR", "CUB": "AMR", "CYP": "EUR",
    "CZE": "EUR", "DNK": "EUR", "DJI": "EMR", "DOM": "AMR", "ECU": "AMR",
    "EGY": "EMR", "SLV": "AMR", "GNQ": "AFR", "ERI": "AFR", "EST": "EUR",
    "SWZ": "AFR", "ETH": "AFR", "FJI": "WPR", "FIN": "EUR", "FRA": "EUR",
    "GAB": "AFR", "GMB": "AFR", "GEO": "EUR", "DEU": "EUR", "GHA": "AFR",
    "GRC": "EUR", "GTM": "AMR", "GIN": "AFR", "GNB": "AFR", "GUY": "AMR",
    "HTI": "AMR", "HND": "AMR", "HUN": "EUR", "ISL": "EUR", "IND": "SEAR",
    "IDN": "SEAR", "IRN": "EMR", "IRQ": "EMR", "IRL": "EUR", "ISR": "EUR",
    "ITA": "EUR", "JAM": "AMR", "JPN": "WPR", "JOR": "EMR", "KAZ": "EUR",
    "KEN": "AFR", "PRK": "SEAR", "KOR": "WPR", "KWT": "EMR", "KGZ": "EUR",
    "LAO": "WPR", "LVA": "EUR", "LBN": "EMR", "LSO": "AFR", "LBR": "AFR",
    "LBY": "EMR", "LTU": "EUR", "LUX": "EUR", "MDG": "AFR", "MWI": "AFR",
    "MYS": "WPR", "MDV": "SEAR", "MLI": "AFR", "MLT": "EUR", "MRT": "AFR",
    "MUS": "AFR", "MEX": "AMR", "MNG": "WPR", "MNE": "EUR", "MAR": "EMR",
    "MOZ": "AFR", "MMR": "SEAR", "NAM": "AFR", "NPL": "SEAR", "NLD": "EUR",
    "NZL": "WPR", "NIC": "AMR", "NER": "AFR", "NGA": "AFR", "MKD": "EUR",
    "NOR": "EUR", "OMN": "EMR", "PAK": "EMR", "PAN": "AMR", "PNG": "WPR",
    "PRY": "AMR", "PER": "AMR", "PHL": "WPR", "POL": "EUR", "PRT": "EUR",
    "QAT": "EMR", "ROU": "EUR", "RUS": "EUR", "RWA": "AFR", "SAU": "EMR",
    "SEN": "AFR", "SRB": "EUR", "SLE": "AFR", "SGP": "WPR", "SVK": "EUR",
    "SVN": "EUR", "SLB": "WPR", "SOM": "EMR", "ZAF": "AFR", "SSD": "AFR",
    "ESP": "EUR", "LKA": "SEAR", "SDN": "EMR", "SUR": "AMR", "SWE": "EUR",
    "CHE": "EUR", "SYR": "EMR", "TJK": "EUR", "TZA": "AFR", "THA": "SEAR",
    "TLS": "SEAR", "TGO": "AFR", "TON": "WPR", "TTO": "AMR", "TUN": "EMR",
    "TUR": "EUR", "TKM": "EUR", "UGA": "AFR", "UKR": "EUR", "ARE": "EMR",
    "GBR": "EUR", "USA": "AMR", "URY": "AMR", "UZB": "EUR", "VUT": "WPR",
    "VEN": "AMR", "VNM": "WPR", "YEM": "EMR", "ZMB": "AFR", "ZWE": "AFR",
}


def _fetch_json(url: str, params: dict | None = None, retries: int = 3) -> dict:
    """Fetch JSON from WHO API with retries."""
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1)
            else:
                print(f"  [ERROR] {url}: {e}")
                return {"value": []}


def download_countries(data_dir: Path) -> list:
    """Download country list from WHO."""
    print("Downloading countries...")
    data = _fetch_json(f"{GHO_BASE}/DIMENSION/COUNTRY/DimensionValues")
    countries = data.get("value", [])
    with open(data_dir / "countries.json", "w") as f:
        json.dump(countries, f)
    print(f"  {len(countries)} countries")
    return countries


def download_regions(data_dir: Path) -> dict:
    """Create WHO region mapping."""
    print("Creating region mapping...")
    regions = [
        {"Code": "AFR", "Title": "Africa"},
        {"Code": "AMR", "Title": "Americas"},
        {"Code": "SEAR", "Title": "South-East Asia"},
        {"Code": "EUR", "Title": "Europe"},
        {"Code": "EMR", "Title": "Eastern Mediterranean"},
        {"Code": "WPR", "Title": "Western Pacific"},
    ]
    with open(data_dir / "regions.json", "w") as f:
        json.dump(regions, f)
    with open(data_dir / "country_regions.json", "w") as f:
        json.dump(WHO_REGION_MAP, f)
    print(f"  {len(regions)} regions, {len(WHO_REGION_MAP)} country mappings")
    return WHO_REGION_MAP


def download_indicator_data(
    data_dir: Path,
    indicators: dict[str, str],
    output_file: str,
    label: str = "indicators",
) -> list:
    """Download data for multiple WHO indicators."""
    print(f"Downloading {label} ({len(indicators)} indicators)...")
    all_data = []
    diseases = []

    for code, name in indicators.items():
        data = _fetch_json(f"{GHO_BASE}/{code}")
        records = data.get("value", [])
        # Add indicator code to each record
        for r in records:
            r["IndicatorCode"] = code
            r["IndicatorName"] = name
        all_data.extend(records)
        diseases.append({"IndicatorCode": code, "IndicatorName": name})
        print(f"  {code}: {len(records)} records")
        time.sleep(0.3)  # Rate limit

    with open(data_dir / output_file, "w") as f:
        json.dump(all_data, f)
    print(f"  Total: {len(all_data)} records")
    return diseases


def download_all(data_dir: str | Path) -> dict:
    """Download all WHO GHO data."""
    data_path = Path(data_dir)
    data_path.mkdir(parents=True, exist_ok=True)

    t0 = time.time()

    # Countries + regions
    countries = download_countries(data_path)
    download_regions(data_path)

    # Disease data
    diseases = download_indicator_data(
        data_path, DISEASE_INDICATORS, "disease_data.json", "disease indicators"
    )
    with open(data_path / "diseases.json", "w") as f:
        json.dump(diseases, f)

    # Vaccine coverage
    download_indicator_data(
        data_path, VACCINE_INDICATORS, "vaccine_data.json", "vaccine coverage"
    )

    # Health indicators
    download_indicator_data(
        data_path, HEALTH_INDICATORS, "health_data.json", "health indicators"
    )

    elapsed = time.time() - t0
    print(f"\n--- Download complete in {elapsed:.0f}s ---")
    for f in sorted(data_path.glob("*.json")):
        size = f.stat().st_size
        print(f"  {f.name}: {size / 1024:.0f} KB")

    return {"countries": len(countries), "elapsed_s": round(elapsed, 1)}


def main():
    parser = argparse.ArgumentParser(description="Download WHO GHO data")
    parser.add_argument("--data-dir", default="data", help="Output directory")
    args = parser.parse_args()
    download_all(args.data_dir)


if __name__ == "__main__":
    main()
