import json
import os
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
import pandas as pd
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize LLM with API key from environment
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite", 
    temperature=0.0,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

# Load all Synthea data from data1/ folder
def load_all_data():
    """Load all Synthea CSV files from data1/ folder"""
    data_dir = "data1"
    patients_df = pd.read_csv(f"{data_dir}/patients.csv").set_index("Id")
    claims_df = pd.read_csv(f"{data_dir}/claims.csv")
    claim_lines_df = pd.read_csv(f"{data_dir}/claim_lines.csv")
    return patients_df, claims_df, claim_lines_df

# Load data at startup
patients, claims, claim_lines = load_all_data()

def fetch_patient_data(patient_id):
    """Fetch patient data, claims, and claim lines from Synthea data"""
    # Validate patient exists
    if patient_id not in patients.index:
        raise ValueError(f"Patient ID {patient_id} not found in patients.csv")
    
    # Helper function to convert numpy types to native Python types
    def to_native_type(val):
        if pd.isna(val):
            return None
        # Convert numpy types to native Python types
        if hasattr(val, 'item'):
            return val.item()
        return val
    
    # Get patient data
    patient_row = patients.loc[patient_id]
    patient_dict = {
        "Id": str(patient_id),
        "SSN": str(to_native_type(patient_row.get("SSN", ""))) if pd.notna(patient_row.get("SSN")) else "",
        "BIRTHDATE": str(to_native_type(patient_row.get("BIRTHDATE", ""))) if pd.notna(patient_row.get("BIRTHDATE")) else "",
        "FIRST": str(to_native_type(patient_row.get("FIRST", ""))) if pd.notna(patient_row.get("FIRST")) else "",
        "LAST": str(to_native_type(patient_row.get("LAST", ""))) if pd.notna(patient_row.get("LAST")) else "",
        "ADDRESS": str(to_native_type(patient_row.get("ADDRESS", ""))) if pd.notna(patient_row.get("ADDRESS")) else "",
        "CITY": str(to_native_type(patient_row.get("CITY", ""))) if pd.notna(patient_row.get("CITY")) else "",
        "STATE": str(to_native_type(patient_row.get("STATE", ""))) if pd.notna(patient_row.get("STATE")) else "",
        "ZIP": str(to_native_type(patient_row.get("ZIP", ""))) if pd.notna(patient_row.get("ZIP")) else "",
        "PHONE": str(to_native_type(patient_row.get("PHONE", ""))) if pd.notna(patient_row.get("PHONE")) else "",
        "EMAIL": str(to_native_type(patient_row.get("EMAIL", ""))) if pd.notna(patient_row.get("EMAIL")) else ""
    }
    
    # Get all claims for this patient
    patient_claims = claims[claims["patient_id"] == patient_id]
    claims_list = []
    
    for _, claim_row in patient_claims.iterrows():
        claim_dict = {
            "claim_id": str(to_native_type(claim_row.get("claim_id", ""))),
            "primary_diagnosis_code": str(to_native_type(claim_row.get("primary_diagnosis_code", ""))) if pd.notna(claim_row.get("primary_diagnosis_code")) else "",
            "primary_diagnosis_description": str(to_native_type(claim_row.get("primary_diagnosis_description", ""))) if pd.notna(claim_row.get("primary_diagnosis_description")) else "",
            "total_claim_cost": float(to_native_type(claim_row.get("total_claim_cost", 0))),
            "admission_date": str(to_native_type(claim_row.get("admission_date", ""))) if pd.notna(claim_row.get("admission_date")) else "",
            "discharge_date": str(to_native_type(claim_row.get("discharge_date", ""))) if pd.notna(claim_row.get("discharge_date")) else "",
            "service_date": str(to_native_type(claim_row.get("service_date", ""))) if pd.notna(claim_row.get("service_date")) else "",
            "encounter_class": str(to_native_type(claim_row.get("encounter_class", ""))) if pd.notna(claim_row.get("encounter_class")) else ""
        }
        claims_list.append(claim_dict)
    
    # Get claim lines for this patient's claims
    if len(claims_list) > 0:
        claim_ids = [c["claim_id"] for c in claims_list]
        patient_claim_lines = claim_lines[claim_lines["claim_id"].isin(claim_ids)]
        claim_lines_list = []
        
        for _, line_row in patient_claim_lines.iterrows():
            line_dict = {
                "claim_id": str(to_native_type(line_row.get("claim_id", ""))),
                "line_id": int(to_native_type(line_row.get("line_id", 0))),
                "cpt_hcpcs_code": str(to_native_type(line_row.get("cpt_hcpcs_code", ""))) if pd.notna(line_row.get("cpt_hcpcs_code")) else "",
                "description": str(to_native_type(line_row.get("description", ""))) if pd.notna(line_row.get("description")) else "",
                "charge_amount": float(to_native_type(line_row.get("charge_amount", 0))),
                "units": int(to_native_type(line_row.get("units", 1))),
                "reason_code": str(to_native_type(line_row.get("reason_code", ""))) if pd.notna(line_row.get("reason_code")) else "",
                "reason_description": str(to_native_type(line_row.get("reason_description", ""))) if pd.notna(line_row.get("reason_description")) else ""
            }
            claim_lines_list.append(line_dict)
    else:
        claim_lines_list = []
    
    # Tasks list (empty for now - can be loaded from tasks.csv if available)
    tasks_list = []
    
    return {
        "patient": patient_dict,
        "claims": claims_list,
        "claim_lines": claim_lines_list,
        "tasks": tasks_list
    }

# Define agent prompts
identity_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are MediGuard Identity & Claims Fraud Agent. You MUST respond with ONLY valid JSON, no markdown, no explanations, just raw JSON."),
    ("human", """Patient Information: {patient}
Claims: {claims}
Claim Lines: {claim_lines}

Analyze this patient's data for fraud and identity misuse. Check for:
1. Duplicate or inconsistent patient information across claims (compare SSN, DOB, name, address)
2. Suspicious diagnosis-procedure combinations (procedures that don't match diagnoses)
3. Claims with unusually high or unrealistic amounts (compare total_claim_cost to typical ranges)
4. Patterns commonly associated with identity misuse (multiple claims with different patient details, rapid claim sequences, etc.)

Return ONLY a JSON object with these exact fields:
- fraud_risk_score (number 0-100) - overall fraud risk assessment
- identity_misuse_flag (boolean) - true if identity misuse is detected, false otherwise
- reasons (array of strings) - list of specific reasons/flags found

Example: {{"fraud_risk_score": 45, "identity_misuse_flag": true, "reasons": ["Duplicate patient information across multiple claims", "Suspicious diagnosis-procedure combination detected"]}}""")
])

billing_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are MediGuard Billing Fraud Agent. You MUST respond with ONLY valid JSON, no markdown, no explanations."),
    ("human", """Identity Analysis: {identity}

Return ONLY a JSON object with these exact fields:
- billing_risk_score (number 0-100)
- billing_flags (array of strings)
- billing_explanation (string)

Example: {{"billing_risk_score": 15, "billing_flags": ["normal_range"], "billing_explanation": "No billing anomalies"}}""")
])

discharge_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are MediGuard Discharge Agent. You MUST respond with ONLY valid JSON, no markdown, no explanations."),
    ("human", """Tasks: {tasks}

Return ONLY a JSON object with these exact fields:
- discharge_ready (boolean)
- blockers (array of strings)
- delay_hours (number)

Example: {{"discharge_ready": true, "blockers": [], "delay_hours": 0}}""")
])

# Create chains
identity_chain = identity_prompt | llm
billing_chain = billing_prompt | llm
discharge_chain = discharge_prompt | llm

# LangGraph nodes
def identity_node(state):
    """Identity and claims fraud detection"""
    data = fetch_patient_data(state["patient_id"])
    
    # Invoke Agent 1 with patient, claims, and claim_lines
    response = identity_chain.invoke({
        "patient": json.dumps(data["patient"], indent=2), 
        "claims": json.dumps(data["claims"], indent=2),
        "claim_lines": json.dumps(data["claim_lines"], indent=2)
    })
    
    # Clean the response - remove markdown code blocks if present
    content = response.content.strip()
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()
    
    result = json.loads(content)
    
    # Validate output structure matches requirements
    required_fields = ["fraud_risk_score", "identity_misuse_flag", "reasons"]
    for field in required_fields:
        if field not in result:
            raise ValueError(f"Agent 1 output missing required field: {field}")
    
    # Ensure types are correct
    if not isinstance(result["fraud_risk_score"], (int, float)):
        raise ValueError("fraud_risk_score must be a number")
    if not isinstance(result["identity_misuse_flag"], bool):
        raise ValueError("identity_misuse_flag must be a boolean")
    if not isinstance(result["reasons"], list):
        raise ValueError("reasons must be an array")
    
    # Return updated state with ALL previous state preserved
    return {
        **state,
        "identity": result, 
        "raw": data
    }

def billing_node(state):
    """Billing fraud detection"""
    response = billing_chain.invoke({"identity": json.dumps(state["identity"])})
    content = response.content.strip()
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()
    result = json.loads(content)
    
    # Return updated state with ALL previous state preserved
    return {
        **state,
        "billing": result
    }

def discharge_node(state):
    """Discharge readiness assessment"""
    # Get tasks from raw data if available, otherwise use empty list
    tasks = state.get("raw", {}).get("tasks", [])
    
    response = discharge_chain.invoke({"tasks": json.dumps(tasks)})
    content = response.content.strip()
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()
    result = json.loads(content)
    
    # Return updated state with final combined results
    return {
        **state,
        "discharge": result, 
        "final": {**state.get("identity", {}), **state.get("billing", {}), **result}
    }

# Build workflow
workflow = StateGraph(dict)
workflow.add_node("identity", identity_node)
workflow.add_node("billing", billing_node)
workflow.add_node("discharge", discharge_node)

workflow.add_edge("identity", "billing")
workflow.add_edge("billing", "discharge")
workflow.add_edge("discharge", END)

workflow.set_entry_point("identity")
app = workflow.compile()

def analyze_patient(patient_id):
    """Main function to analyze a patient through all agents"""
    result = app.invoke({"patient_id": patient_id})
    return result  # Return full state, not just final

def analyze_agent1_only(patient_id):
    """Analyze a patient using only Agent 1 (Claims & Identity Fraud Agent)"""
    try:
        data = fetch_patient_data(patient_id)
        response = identity_chain.invoke({
            "patient": json.dumps(data["patient"], indent=2), 
            "claims": json.dumps(data["claims"], indent=2),
            "claim_lines": json.dumps(data["claim_lines"], indent=2)
        })
        
        # Clean the response
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        
        result = json.loads(content)
        
        # Validate output structure
        required_fields = ["fraud_risk_score", "identity_misuse_flag", "reasons"]
        for field in required_fields:
            if field not in result:
                raise ValueError(f"Agent 1 output missing required field: {field}")
        
        return result
    except ValueError as e:
        raise ValueError(f"Error analyzing patient: {str(e)}")
    except Exception as e:
        raise Exception(f"Unexpected error: {str(e)}")

def get_sample_patient_ids(limit=10):
    """Get sample patient IDs for testing"""
    return patients.index.tolist()[:limit]

if __name__ == "__main__":
    import sys
    
    print("🏥 MediGuard AI Agent - Starting Analysis...")
    
    # Get patient ID from command line or prompt
    if len(sys.argv) > 1:
        patient_id = sys.argv[1]
    else:
        # Show sample patient IDs
        sample_ids = get_sample_patient_ids(5)
        print(f"\n📋 Sample Patient IDs (first 5):")
        for i, pid in enumerate(sample_ids, 1):
            print(f"  {i}. {pid}")
        
        patient_id = input("\nEnter Patient ID (UUID): ").strip()
        if not patient_id:
            print("❌ No patient ID provided. Exiting.")
            sys.exit(1)
    
    print(f"\n📋 Analyzing Patient: {patient_id}\n")
    
    try:
        # For now, run Agent 1 only (as per plan focus)
        result = analyze_agent1_only(patient_id)
        
        print("=" * 60)
        print("📊 AGENT 1 ANALYSIS RESULTS (Claims & Identity Fraud)")
        print("=" * 60)
        print(json.dumps(result, indent=2))
    except ValueError as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)