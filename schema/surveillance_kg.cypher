// Disease Surveillance Knowledge Graph — Schema
//
// 7 Node Labels, 7 Edge Types
// Source: WHO Global Health Observatory (GHO) OData API

// --- Indexes ---
CREATE INDEX ON :Country(iso_code);
CREATE INDEX ON :Country(name);
CREATE INDEX ON :Disease(indicator_code);
CREATE INDEX ON :Disease(name);
CREATE INDEX ON :Region(who_code);
CREATE INDEX ON :DiseaseReport(id);
CREATE INDEX ON :VaccineCoverage(id);
CREATE INDEX ON :AMRProfile(id);
CREATE INDEX ON :HealthIndicator(indicator_code);

// --- Node Labels ---
// Country:          iso_code, name, who_region
// Region:           who_code, name (WHO regions: AFR, AMR, SEAR, EUR, EMR, WPR)
// Disease:          indicator_code, name, category (infectious, ncd, injury)
// DiseaseReport:    id, year, value, low, high (annual case/death count per country per disease)
// VaccineCoverage:  id, year, coverage_pct, antigen (DTP3, MCV1, BCG, etc.)
// AMRProfile:       id, year, pathogen, antibiotic, resistance_pct
// HealthIndicator:  indicator_code, name, category, year, value (generic WHO indicators)

// --- Edge Types ---
// IN_REGION:        Country -> Region
// REPORTED:         Country -> DiseaseReport
// REPORT_OF:        DiseaseReport -> Disease
// HAS_COVERAGE:     Country -> VaccineCoverage
// COVERAGE_FOR:     VaccineCoverage -> Disease
// HAS_AMR:          Country -> AMRProfile
// HAS_INDICATOR:    Country -> HealthIndicator

// --- Cross-KG Bridge Properties ---
// Disease.name       -> Clinical Trials KG Condition.name
// Disease.icd_code   -> Clinical Trials KG Condition.mesh_id (partial)
// Country.iso_code   -> Health Determinants KG Region.iso_code (future)
