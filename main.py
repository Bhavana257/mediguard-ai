import json
import os
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
import pandas as pd
from dotenv import load_dotenv
from agents.discharge_agent import run_discharge_agent

# Load environment variables from .env file
load_dotenv()

# Initialize LLM with API key from environment
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite", 
    temperature=0.0,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

# Load patient data
patients = pd.read_csv("data/patients.csv").set_index("patient_id")

def fetch_patient_data(patient_id):
    """Fetch patient data and simulate claims/tasks and include labs/imaging/encounters"""
    # patients is already loaded at top as `patients = pd.read_csv("data/patients.csv").set_index("patient_id")`
    p = patients.loc[patient_id].to_dict()

    # Claims (existing simple simulation)
    claims = [
        {
            "claim_id": f"C{i}",
            "diagnosis": p["diagnosis"],
            "procedure": p["procedure"],
            "amount": p["amount"]
        }
        for i in range(1, 6)
    ]

    # Tasks: keep the existing approach
    tasks = [{"task": p["task"]}] if p.get("task") and p["task"] != "None" else []

    # Read supporting CSVs (expected to be in data/)
    try:
        labs_df = pd.read_csv("data/observations.csv")
    except Exception:
        labs_df = pd.DataFrame()
    try:
        imaging_df = pd.read_csv("data/ImagingStudies.csv")
    except Exception:
        imaging_df = pd.DataFrame()
    try:
        encounters_df = pd.read_csv("data/encounters.csv")
    except Exception:
        encounters_df = pd.DataFrame()

    # Filter rows for this patient — column name might be `patient_id` or `id`
    def filter_by_patient(df):
        if df.empty:
            return df
        if "patient_id" in df.columns:
            return df[df["patient_id"] == patient_id]
        if "id" in df.columns:
            return df[df["id"] == patient_id]
        # if no matching column, return empty DataFrame
        return df.iloc[0:0]

    patient_labs = filter_by_patient(labs_df)
    patient_imaging = filter_by_patient(imaging_df)
    patient_encounters = filter_by_patient(encounters_df)

    return {
        "patient": p,
        "claims": claims,
        "tasks": tasks,
        "labs": patient_labs.to_dict(orient="records"),
        "imaging": patient_imaging.to_dict(orient="records"),
        "encounters": patient_encounters.to_dict(orient="records"),
    }


# Define agent prompts
identity_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are MediGuard Identity & Claims Fraud Agent. You MUST respond with ONLY valid JSON, no markdown, no explanations, just raw JSON."),
    ("human", """Patient: {patient}
Claims: {claims}

Return ONLY a JSON object with these exact fields:
- identity_risk_score (number 0-100)
- flags (array of strings)
- explanation (string)

Example: {{"identity_risk_score": 25, "flags": ["multiple_claims"], "explanation": "Low risk patient"}}""")
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
    ("system",
     "You are MediGuard Discharge Agent. Analyze the patient's tasks, labs, imaging and encounters and return STRICT JSON only (no markdown)."),
    ("human",
     """Patient: {patient}
Tasks: {tasks}
Labs (list): {labs}
Imaging (list): {imaging}
Encounters (list): {encounters}

Return EXACTLY a JSON object with fields:
- discharge_ready (boolean)
- blockers (array of short strings)
- delay_hours (number)
- priority_level (LOW|MEDIUM|HIGH)

Example output:
{"discharge_ready": false, "blockers": ["pending_lab_results","imaging_pending"], "delay_hours": 5, "priority_level": "MEDIUM"}""")
])
discharge_chain = discharge_prompt | llm



# Create chains
identity_chain = identity_prompt | llm
billing_chain = billing_prompt | llm
discharge_chain = discharge_prompt | llm

# LangGraph nodes
# LangGraph nodes
def identity_node(state):
    """Identity and claims fraud detection"""
    data = fetch_patient_data(state["patient_id"])
    response = identity_chain.invoke({
        "patient": json.dumps(data["patient"]), 
        "claims": json.dumps(data["claims"])
    })
    # Clean the response - remove markdown code blocks if present
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
    """LLM-based discharge analysis agent using structured patient data"""
    data = fetch_patient_data(state["patient_id"])

    # Build the payload (strings or JSON) — stringify lists to be safe
    response = discharge_chain.invoke({
        "patient": json.dumps(data["patient"]),
        "tasks": json.dumps(data["tasks"]),
        "labs": json.dumps(data["labs"]),
        "imaging": json.dumps(data["imaging"]),
        "encounters": json.dumps(data["encounters"])
    })

    content = response.content.strip()
    # strip markdown code blocks if present
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()

    # Parse LLM output to JSON; handle parse errors gracefully
    try:
        discharge_result = json.loads(content)
    except Exception as e:
        # fallback: minimal structured failure output
        discharge_result = {
            "discharge_ready": False,
            "blockers": ["llm_parse_error"],
            "delay_hours": 0,
            "priority_level": "MEDIUM",
            "error": str(e),
            "raw": content[:1000]
        }

    # Merge into final result (keep identity & billing keys)
    combined = {
        **state.get("identity", {}),
        **state.get("billing", {}),
        **discharge_result
    }

    return {
        **state,
        "discharge": discharge_result,
        "final": combined
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
    """Main function to analyze a patient"""
    result = app.invoke({"patient_id": patient_id})
    return result["final"]

if __name__ == "__main__":
    # Demo run
    print("🏥 MediGuard AI Agent - Starting Analysis...")
    print(f"📋 Analyzing Patient: P0000501\n")
    
    result = analyze_patient("P0000501")
    
    print("=" * 60)
    print("📊 ANALYSIS RESULTS")
    print("=" * 60)
    print(json.dumps(result, indent=2))
