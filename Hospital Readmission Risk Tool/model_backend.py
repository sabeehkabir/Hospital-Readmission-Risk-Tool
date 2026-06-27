import pandas as pd
import joblib
import shap
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "xgboost_readmission_model.pkl")

model_pipeline = joblib.load(MODEL_PATH)
model = model_pipeline.named_steps["model"]
preprocessor = model_pipeline.named_steps["preprocess"]
explainer = shap.TreeExplainer(model)

# Default values for all columns the pipeline was trained on but your UI doesn't collect
MISSING_COLUMN_DEFAULTS = {
    "race": "Caucasian",
    "admission_type_id": 1,
    "discharge_disposition_id": 1,
    "admission_source_id": 7,
    "num_lab_procedures": 40,
    "num_procedures": 1,
"medical_specialty": "Unknown",  
"payer_code": "Unknown",          
"max_glu_serum": "Unknown",     
    "diag_1": "Unknown",
"diag_2": "Unknown",
"diag_3": "Unknown",
    "metformin": "No",
    "repaglinide": "No",
    "nateglinide": "No",
    "chlorpropamide": "No",
    "glimepiride": "No",
    "acetohexamide": "No",
    "glipizide": "No",
    "glyburide": "No",
    "tolbutamide": "No",
    "pioglitazone": "No",
    "rosiglitazone": "No",
    "acarbose": "No",
    "miglitol": "No",
    "troglitazone": "No",
    "tolazamide": "No",
    "examide": "No",
    "citoglipton": "No",
    "glyburide-metformin": "No",
    "glipizide-metformin": "No",
    "glimepiride-pioglitazone": "No",
    "metformin-rosiglitazone": "No",
    "metformin-pioglitazone": "No",
}
def bin_weight(weight_lbs):
    if weight_lbs <= 0:
        return "?"
    elif weight_lbs <= 25:
        return "[0-25)"
    elif weight_lbs <= 50:
        return "[25-50)"
    elif weight_lbs <= 75:
        return "[50-75)"
    elif weight_lbs <= 100:
        return "[75-100)"
    elif weight_lbs <= 125:
        return "[100-125)"
    elif weight_lbs <= 150:
        return "[125-150)"
    elif weight_lbs <= 175:
        return "[150-175)"
    elif weight_lbs <= 200:
        return "[175-200)"
    else:
        return ">200"

def rule_based_readmission_risk(patient_data: dict):

    # Build row from UI inputs
    ui_fields = {
"age": f"[{patient_data['Age']})",          # wraps "0-10" → "[0-10)"
        "gender": patient_data["Sex"],
        "time_in_hospital": patient_data["Time_in_Hospital"],
        "num_medications": patient_data["Medications"],
        "number_diagnoses": patient_data["Diagnoses"],
        "number_inpatient": patient_data["Inpatient_Visits"],
        "number_emergency": patient_data["Emergency_Visits"],
        "number_outpatient": patient_data["Outpatient_Visits"],
        "A1Cresult": patient_data["A1C"],
        "insulin": patient_data["Insulin"],
"change": "Ch" if patient_data["Medication_Change"] == "Yes" else "No",  # fixes Yes→Ch
        "diabetesMed": patient_data["Diabetes_Med"],
        "weight": bin_weight(patient_data["Weight_lbs"]),
    }

    # Merge: UI fields override defaults for any overlap
    full_row = {**MISSING_COLUMN_DEFAULTS, **ui_fields}
    input_df = pd.DataFrame([full_row])

    probability = model_pipeline.predict_proba(input_df)[0][1]
    risk_percent = round(probability * 100, 1)

    if risk_percent >= 70:
        category = "High"
    elif risk_percent >= 40:
        category = "Moderate"
    else:
        category = "Low"

    processed_input = preprocessor.transform(input_df)
    shap_values = explainer.shap_values(processed_input)
    feature_names = preprocessor.get_feature_names_out()

    shap_pairs = sorted(
        zip(feature_names, shap_values[0]),
        key=lambda x: abs(x[1]),
        reverse=True
    )

    top_features = [x[0] for x in shap_pairs[:5]]

    return {
        "readmission_risk_percent": risk_percent,
        "risk_category": category,"explanation": f"XGBoost predicts {risk_percent:.1f}% readmission risk.",
        "top_features": top_features,
        "protective_factors": [],
        "recommended_action": "Review diabetes follow-up and utilization history."
    }