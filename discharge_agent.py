import pandas as pd
from pydantic import BaseModel

class DischargeOutput(BaseModel):
    patient_id: str
    discharge_ready_flag: bool
    blockers: list
    delay_hours: float
    priority_level: str
    validation: dict

def run_discharge_agent(
        patient_id,
        patients_csv="patients.csv",
        labs_csv="observations.csv",
        imaging_csv="ImagingStudies.csv",
        encounters_csv="encounters.csv"
):

    # Loading CSV files
    try:
        patients = pd.read_csv(patients_csv)
        labs = pd.read_csv(labs_csv)
        imaging = pd.read_csv(imaging_csv)
        encounters = pd.read_csv(encounters_csv)
    except Exception as e:
        return {
            "patient_id": patient_id,
            "error": "CSV load failed",
            "details": str(e)
        }

    patient = patients[patients["patient_id"] == patient_id]

    if patient.empty:
        return {
            "patient_id": patient_id,
            "discharge_ready_flag": False,
            "blockers": ["patient_not_found"],
            "delay_hours": 0,
            "priority_level": "HIGH",
            "validation": {"json_valid": False, "missing": ["patient_id"]}
        }

    blockers = []
    delay_hours = 0

    # tasks check
    task_status = patient["task"].iloc[0]

    if task_status == "Pending Lab":
        blockers.append("pending_labs")
        delay_hours += 3

    if task_status == "Pending Imaging":
        blockers.append("pending_imaging")
        delay_hours += 4

    if task_status == "Missing Consult":
        blockers.append("missing_consultation")
        delay_hours += 2

    # Lab check
    lab_rows = labs[labs["patient_id"] == patient_id]

    if lab_rows.empty:
        blockers.append("lab_results_missing")
        delay_hours += 2
    else:
        if lab_rows["value"].isna().any():
            blockers.append("pending_lab_results")
            delay_hours += 3

    # Image check
    imaging_rows = imaging[imaging["patient_id"] == patient_id]

    if imaging_rows.empty:
        blockers.append("imaging_not_done")
        delay_hours += 3
    else:
        if (imaging_rows["status"] == "pending").any():
            blockers.append("imaging_pending")
            delay_hours += 4

    # Discharge details
    encounter_rows = encounters[encounters["patient_id"] == patient_id]

    if encounter_rows.empty:
        blockers.append("no_encounter_record")
        delay_hours += 1
    else:
        if encounter_rows["stop"].isna().any():
            blockers.append("not_discharged_yet")
            delay_hours += 2

    if len(blockers) == 0:
        return {
            "patient_id": patient_id,
            "discharge_ready_flag": True,
            "blockers": [],
            "delay_hours": 0,
            "priority_level": "LOW",
            "validation": {"json_valid": True, "missing": []}
        }

    priority = "HIGH" if delay_hours > 5 else "MEDIUM"

    return {
        "patient_id": patient_id,
        "discharge_ready_flag": False,
        "blockers": blockers,
        "delay_hours": delay_hours,
        "priority_level": priority,
        "validation": {"json_valid": False, "missing": ["patient_id"]}

    }
