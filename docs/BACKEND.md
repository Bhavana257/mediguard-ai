# Backend Documentation

This document explains all functions and components in the MediGuard AI backend system.

## Table of Contents

- [Main Workflow (`main.py`)](#main-workflow-mainpy)
- [API Server (`api_server.py`)](#api-server-api_serverpy)
- [Data Loading](#data-loading)
- [Agent Functions](#agent-functions)

---

## Main Workflow (`main.py`)

### `load_all_data()`

**Purpose:** Loads all Synthea CSV files into pandas DataFrames at application startup.

**What it does:**
- Reads `data1/patients.csv` and indexes by patient `Id` (UUID)
- Reads `data1/claims.csv` with all claim records
- Reads `data1/claim_lines.csv` with detailed billing line items
- Returns three DataFrames for efficient querying

**Returns:**
- `patients_df` - DataFrame indexed by patient UUID
- `claims_df` - DataFrame with all claims
- `claim_lines_df` - DataFrame with all claim line items

**Usage:** Called once at module import to load data into memory.

---

### `fetch_patient_data(patient_id: str)`

**Purpose:** Retrieves all data for a specific patient from the loaded DataFrames.

**Parameters:**
- `patient_id` (str): Patient UUID to fetch data for

**What it does:**
1. Validates that the patient exists in the patients DataFrame
2. Extracts patient demographics (SSN, DOB, name, address, etc.)
3. Filters claims DataFrame to get all claims for this patient
4. Filters claim_lines DataFrame to get all billing lines for those claims
5. Converts numpy/pandas types to native Python types for JSON serialization
6. Returns structured dictionary with patient, claims, and claim_lines

**Returns:**
```python
{
    "patient": {
        "Id": "uuid",
        "SSN": "999-33-6229",
        "BIRTHDATE": "2000-10-06",
        "FIRST": "John",
        "LAST": "Doe",
        # ... other fields
    },
    "claims": [
        {
            "claim_id": "uuid",
            "primary_diagnosis_code": "I10",
            "total_claim_cost": 704.20,
            # ... other fields
        }
    ],
    "claim_lines": [
        {
            "claim_id": "uuid",
            "cpt_hcpcs_code": "99214",
            "charge_amount": 215.70,
            # ... other fields
        }
    ],
    "tasks": []  # Empty list (for Agent 3)
}
```

**Raises:** `ValueError` if patient ID not found

---

### `identity_node(state: dict)`

**Purpose:** Agent 1 - Analyzes patient data for identity fraud and suspicious claims.

**What it does:**
1. Gets patient data using `fetch_patient_data()`
2. Sends patient info, claims, and claim_lines to the LLM (Gemini)
3. LLM analyzes for:
   - Duplicate/inconsistent patient information across claims
   - Suspicious diagnosis-procedure combinations
   - Unusually high claim amounts
   - Identity misuse patterns
4. Parses and validates the JSON response
5. Ensures output has required fields: `fraud_risk_score`, `identity_misuse_flag`, `reasons`

**Input State:**
```python
{
    "patient_id": "uuid"
}
```

**Output State:**
```python
{
    "patient_id": "uuid",
    "identity": {
        "fraud_risk_score": 45,
        "identity_misuse_flag": true,
        "reasons": ["Duplicate patient information", "Suspicious pattern"]
    },
    "raw": { /* patient data */ }
}
```

**Raises:** `ValueError` if LLM output doesn't match required structure

---

### `billing_node(state: dict)`

**Purpose:** Agent 2 - Analyzes billing for fraud based on identity analysis results.

**What it does:**
1. Receives identity analysis from previous agent
2. Sends identity results to LLM for billing fraud analysis
3. LLM checks for:
   - Procedures not supported by diagnosis
   - Duplicate/add-on procedures
   - Charges above normal ranges
   - Suspicious billing combinations
4. Parses JSON response
5. Returns billing analysis results

**Input State:** State from `identity_node` (includes `identity` field)

**Output State:**
```python
{
    # ... previous state ...
    "billing": {
        "billing_risk_score": 25,
        "billing_flags": ["normal_range"],
        "billing_explanation": "No billing anomalies"
    }
}
```

---

### `discharge_node(state: dict)`

**Purpose:** Agent 3 - Assesses discharge readiness and identifies blockers.

**What it does:**
1. Gets tasks from the raw data (currently empty list)
2. Sends tasks to LLM for discharge assessment
3. LLM determines:
   - If patient is ready for discharge
   - What blockers exist (pending labs, scans, paperwork)
   - Estimated delay hours
4. Parses JSON response
5. Combines all agent results into final output

**Input State:** State from `billing_node` (includes `identity`, `billing`, `raw`)

**Output State:**
```python
{
    # ... previous state ...
    "discharge": {
        "discharge_ready": false,
        "blockers": ["Pending Lab", "Missing Consult"],
        "delay_hours": 24
    },
    "final": {
        # Combined results from all agents
    }
}
```

---

### `analyze_patient(patient_id: str)`

**Purpose:** Main entry point to run all three agents in sequence.

**What it does:**
1. Invokes the LangGraph workflow with patient_id
2. Workflow runs: identity_node → billing_node → discharge_node
3. Returns the complete workflow state with all agent results

**Parameters:**
- `patient_id` (str): Patient UUID to analyze

**Returns:** Complete workflow state dictionary with identity, billing, discharge, and final results

**Usage:**
```python
result = analyze_patient("341de73b-56e5-6f58-c32f-9d56a1290e2f")
print(result["final"])  # Combined results
```

---

### `analyze_agent1_only(patient_id: str)`

**Purpose:** Runs only Agent 1 (Identity & Claims Fraud) for testing.

**What it does:**
1. Fetches patient data
2. Invokes only the identity chain (skips billing and discharge)
3. Validates output structure
4. Returns Agent 1 results only

**Parameters:**
- `patient_id` (str): Patient UUID

**Returns:** Agent 1 results dictionary

**Usage:** Useful for testing Agent 1 independently

---

### `get_sample_patient_ids(limit: int = 10)`

**Purpose:** Gets a list of sample patient IDs for testing.

**What it does:**
- Returns first N patient IDs from the loaded patients DataFrame

**Parameters:**
- `limit` (int): Number of patient IDs to return (default: 10)

**Returns:** List of patient UUID strings

---

## API Server (`api_server.py`)

### `get_sample_ids(limit: int = 10)`

**Purpose:** API endpoint to get sample patient IDs.

**Endpoint:** `GET /api/sample-ids?limit=10`

**What it does:**
- Calls `get_sample_patient_ids()` from main.py
- Returns JSON with list of patient IDs

**Response:**
```json
{
    "ids": ["uuid1", "uuid2", ...]
}
```

---

### `analyze_patient_endpoint(request: PatientAnalysisRequest)`

**Purpose:** API endpoint to run full analysis through all agents.

**Endpoint:** `POST /api/analyze`

**What it does:**
1. Validates patient exists
2. Calls `analyze_patient()` to run all agents
3. Structures response to match frontend expectations
4. Separates identity, billing, discharge, and final results

**Request Body:**
```json
{
    "patient_id": "uuid-here"
}
```

**Response:**
```json
{
    "identity": {
        "fraud_risk_score": 45,
        "identity_misuse_flag": true,
        "reasons": [...]
    },
    "billing": {
        "billing_fraud_score": 25,
        "billing_flags": [...],
        "billing_explanation": "..."
    },
    "discharge": {
        "discharge_ready": false,
        "blockers": [...],
        "delay_hours": 24
    },
    "final": {
        // Combined results
    }
}
```

**Error Responses:**
- `404` - Patient not found
- `500` - Analysis error (includes traceback)

---

### `analyze_agent1_only_endpoint(request: PatientAnalysisRequest)`

**Purpose:** API endpoint to run only Agent 1.

**Endpoint:** `POST /api/analyze/agent1`

**What it does:**
- Calls `analyze_agent1_only()` from main.py
- Returns only Agent 1 results

**Use Case:** Testing or when only identity fraud detection is needed

---

## Data Loading

### CSV Files Structure

**`data1/patients.csv`:**
- Indexed by `Id` (UUID)
- Contains: SSN, BIRTHDATE, FIRST, LAST, ADDRESS, CITY, STATE, ZIP, PHONE, EMAIL

**`data1/claims.csv`:**
- Contains: `claim_id`, `patient_id`, `primary_diagnosis_code`, `total_claim_cost`, dates
- Linked to patients via `patient_id`

**`data1/claim_lines.csv`:**
- Contains: `claim_id`, `line_id`, `cpt_hcpcs_code`, `charge_amount`, `units`
- Linked to claims via `claim_id`

### Data Flow

1. **Startup:** `load_all_data()` loads all CSVs into DataFrames
2. **Request:** `fetch_patient_data()` filters DataFrames for specific patient
3. **Analysis:** Agents receive structured data dictionaries
4. **Response:** Results are JSON-serialized and returned

---

## Agent Prompts

All agents use structured prompts that:
- Instruct LLM to return ONLY valid JSON
- Specify exact output field names and types
- Provide examples of expected output
- Include analysis instructions

**Prompt Structure:**
- System message: Role definition and JSON-only requirement
- Human message: Data to analyze + output format specification + example

---

## Error Handling

**Common Errors:**

1. **Patient Not Found:**
   - `ValueError` raised by `fetch_patient_data()`
   - Caught and returned as 404 HTTP error

2. **Invalid LLM Response:**
   - JSON parsing errors caught
   - Markdown code blocks stripped automatically
   - Validation ensures required fields exist

3. **Type Errors:**
   - Numpy types converted to native Python types
   - NaN values handled gracefully

---

## Workflow Architecture

The system uses **LangGraph** to orchestrate the agent workflow:

```
Start → identity_node → billing_node → discharge_node → End
```

Each node:
- Receives state dictionary
- Adds its results to state
- Passes updated state to next node
- Preserves all previous state data

This allows each agent to access results from previous agents while maintaining the full context.

