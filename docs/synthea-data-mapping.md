# Synthea Data Mapping Documentation

This document describes the Synthea data structure used in the MediGuard AI system and how it maps to the project's requirements.

## Required Synthea Tables/CSV Files

The system requires the following CSV files exported from Synthea, placed in the `data1/` folder:

### 1. patients.csv
**Purpose**: Patient demographics for identity verification and fraud detection

**Required Fields**:
- `Id` (UUID) - Primary key, patient identifier
- `SSN` - Social Security Number (for identity consistency checks)
- `BIRTHDATE` - Date of birth (YYYY-MM-DD format)
- `FIRST` - First name
- `LAST` - Last name
- `ADDRESS` - Street address
- `CITY` - City
- `STATE` - State
- `ZIP` - ZIP code
- `PHONE` - Phone number
- `EMAIL` - Email address

**Optional but Recommended**:
- `PREFIX`, `MIDDLE`, `SUFFIX` - Name components
- `RACE`, `ETHNICITY`, `GENDER` - Demographics
- `HEALTHCARE_EXPENSES`, `HEALTHCARE_COVERAGE` - Financial data

### 2. claims.csv
**Purpose**: Claim-level data for fraud pattern detection

**Required Fields**:
- `claim_id` (UUID) - Primary key, claim identifier
- `patient_id` (UUID) - Foreign key to patients.csv
- `primary_diagnosis_code` - ICD-10 or SNOMED diagnosis code
- `primary_diagnosis_description` - Human-readable diagnosis description
- `total_claim_cost` - Total cost of the claim (numeric)
- `admission_date` - Claim admission date (ISO 8601 format)
- `discharge_date` - Claim discharge date (ISO 8601 format)
- `service_date` - Service date (ISO 8601 format)
- `encounter_class` - Type of encounter (ambulatory, wellness, etc.)

**Optional but Recommended**:
- `provider_id` - Provider identifier
- `organization_id` - Organization identifier
- `payer` - Insurance payer identifier
- `base_encounter_cost` - Base cost before adjustments
- `payer_coverage` - Amount covered by payer

### 3. claim_lines.csv
**Purpose**: Detailed billing line items for procedure-level fraud detection

**Required Fields**:
- `claim_id` (UUID) - Foreign key to claims.csv
- `line_id` - Line item identifier
- `patient_id` (UUID) - Foreign key to patients.csv
- `cpt_hcpcs_code` - CPT or HCPCS procedure code
- `description` - Procedure description
- `charge_amount` - Charge amount for this line item (numeric)
- `units` - Number of units billed
- `service_date` - Service date for this line item

**Optional but Recommended**:
- `code_system` - Code system (e.g., "http://snomed.info/sct")
- `reason_code` - Reason code for the procedure
- `reason_description` - Reason description

## Data Relationships

```
patients.csv (Id)
    ↓
claims.csv (patient_id → patients.Id)
    ↓
claim_lines.csv (claim_id → claims.claim_id, patient_id → patients.Id)
```

## How Data is Used by Agents

### Agent 1: Claims & Identity Fraud Agent

**Input Data**:
- Patient demographics from `patients.csv` (SSN, DOB, name, address)
- All claims from `claims.csv` for the patient
- All claim lines from `claim_lines.csv` for those claims

**Analysis Performed**:
1. **Identity Consistency**: Compares patient information (SSN, DOB, name, address) across multiple claims to detect inconsistencies
2. **Suspicious Patterns**: Identifies rapid claim sequences, unusual claim frequencies
3. **Amount Analysis**: Flags claims with unusually high `total_claim_cost` values
4. **Diagnosis-Procedure Matching**: Checks if procedures in `claim_lines.csv` match diagnoses in `claims.csv`

**Output**:
```json
{
  "fraud_risk_score": 45,
  "identity_misuse_flag": true,
  "reasons": [
    "Duplicate patient information across multiple claims",
    "Suspicious diagnosis-procedure combination detected"
  ]
}
```

## Data Loading

The system loads all CSV files at startup using the `load_all_data()` function:

```python
patients_df = pd.read_csv("data1/patients.csv").set_index("Id")
claims_df = pd.read_csv("data1/claims.csv")
claim_lines_df = pd.read_csv("data1/claim_lines.csv")
```

Data is stored as pandas DataFrames for efficient querying and filtering.

## Generating Synthea Data

To generate data using Synthea:

1. Install Synthea: https://github.com/synthetichealth/synthea
2. Run Synthea to generate synthetic patient data
3. Export the following tables to CSV format:
   - `patients`
   - `claims` (or `encounters` if using encounter-based data)
   - `claim_lines` (or `procedure` if using procedure-based data)
4. Place CSV files in the `data1/` folder
5. Ensure column names match the required fields listed above

## Notes

- Patient IDs are UUIDs (not simple sequential IDs like P0000501)
- Dates should be in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)
- Numeric fields (costs, amounts) should be numeric types, not strings
- Missing values should be handled gracefully (empty strings or NaN)

