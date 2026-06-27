import streamlit as st
from model_backend import rule_based_readmission_risk
import datetime

st.set_page_config(page_title="Clinical Dashboard", layout="wide")

# SESSION STATE INIT

if "agreed" not in st.session_state:
    st.session_state["agreed"] = False

if "patient_history" not in st.session_state:
    st.session_state["patient_history"] = []

if "patient_data" not in st.session_state:
    st.session_state["patient_data"] = None

# DISCLAIMER PAGE

if not st.session_state["agreed"]:
    st.title("⚠️ Disclaimer")

    st.markdown("""
    This application is for **educational purposes only** and is not intended 
    for medical diagnosis or treatment.

    By proceeding, you acknowledge:
    - This is NOT a clinical decision tool
    - Do NOT make medical decisions based on this app
    - Data is not stored securely
    """)

    agree = st.checkbox("I have read and agree to the terms")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Continue"):
            if agree:
                st.session_state["agreed"] = True
                st.rerun()
            else:
                st.warning("You must agree to continue.")

    with col2:
        if st.button("Decline"):
            st.error("You must accept the disclaimer to use this application.")

    st.stop()

# SIDEBAR - NAVIGATION

if "page" not in st.session_state:
    st.session_state["page"] = "Patient Input"

page = st.sidebar.radio(
    "Navigation",
    ["Patient Input", "Summary", "History"],
    index=["Patient Input", "Summary", "History"].index(st.session_state["page"])
)

# keep session in sync
st.session_state["page"] = page



# HELPER FUNCTIONS

def convert_weight_to_lbs(weight, unit):
    return weight * 2.20462 if unit == "kg" else weight

def a1c_to_category(a1c_value):
    if a1c_value < 4.1:
        return "Unknown"  # below normal range = treat as missing
    elif a1c_value < 7.0:
        return "Norm"
    elif a1c_value < 8.0:
        return ">7"
    else:
        return ">8"


# PATIENT INPUT PAGE

if page == "Patient Input":
    st.title("🩺 Patient Intake Form")
    st.markdown("Enter the patient's clinical data below.")

    with st.container():
        st.subheader("👤 Demographics")
        col1, col2, col3 = st.columns(3)

        with col1:
            age = st.selectbox(
    "Age Group",
    ["0-10","10-20","20-30","30-40","40-50","50-60","60-70","70-80","80-90","90-100"]
    )
        with col2:
            sex = st.radio("Sex", ["Male", "Female"], horizontal=True)
        with col3:
            weight_unit = st.selectbox("Weight Unit", ["lbs", "kg"])
            weight_input = st.number_input(f"Weight ({weight_unit})", min_value = 0.0)
            weight_lbs = convert_weight_to_lbs(weight_input, weight_unit)
            st.caption(f"Stored as: {weight_lbs:.2f} lbs")

        st.markdown("<hr style='border-top: 2px solid #0d6efd;'>", unsafe_allow_html=True)

    # HOSPITAL STAY
    
    with st.container():
        st.subheader("🏥 Hospital Stay")
        col1, col2 = st.columns(2)

        with col1:
            time_in_hospital = st.slider("Time in Hospital (days)", 0, 30, 1)
        with col2:
            num_inpatient = st.slider("Inpatient Visits", 0, 50, 0)

        st.markdown("<hr style='border-top: 2px solid #0d6efd;'>", unsafe_allow_html=True)

    # VISIT HISTORY
    

    with st.container():
        st.subheader("📊 Visit History")
        col1, col2, col3 = st.columns(3)

        with col1:
            num_emergency = st.slider("Emergency Visits", 0, 50, 0)
        with col2:
            num_outpatient = st.slider("Outpatient Visits", 0, 50, 0)
        with col3:
            num_diagnoses = st.slider("Diagnoses Count", 0, 50, 1)

        st.markdown("<hr style='border-top: 2px solid #0d6efd;'>", unsafe_allow_html=True)

    
    # MEDICATIONS
    
    with st.container():
        st.subheader("💊 Medications & Treatments")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            num_medications = st.slider("Number of Medications", 0, 50, 1)
            
        with col2:
            med_change = st.radio("Medication Change", ["Yes", "No"], horizontal=True)
        with col3:
            diabetes_med = st.radio("Diabetes Medication", ["Yes", "No"], horizontal=True)
        with col4:
            insulin = st.radio("Insulin Usage", ["Yes", "No"], horizontal=True)


        st.markdown("<hr style='border-top: 2px solid #0d6efd;'>", unsafe_allow_html=True)

    
    # LAB RESULTS
    

    with st.container():
        st.subheader("🧪 Lab Results")
        a1c_numeric = st.slider("A1C (%)", 0.0, 14.0, 6.5, 0.1)

        # Map slider value to category for backend
        a1c_category = a1c_to_category(a1c_numeric)
        #st.caption(f"Category stored for backend: {a1c_category}")

        if a1c_category in [">7", ">8"]:
            st.warning(f"⚠️ High A1C result: {a1c_numeric:.1f}% ({a1c_category})")
        if a1c_category in ["Norm", "None"]:
            st.warning(f"Normal A1C result: {a1c_numeric:.1f}%")

        st.markdown("<hr style='border-top: 2px solid #0d6efd;'>", unsafe_allow_html=True)
#
# SUBMIT BUTTON
#

    if st.button("🔍 Analyze Patient"):

        base_data = {
            "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
            "Age": age,
            "Sex": sex,
            "Weight_lbs": weight_lbs,
            "Time_in_Hospital": time_in_hospital,
            "Inpatient_Visits": num_inpatient,
            "Emergency_Visits": num_emergency,
            "Outpatient_Visits": num_outpatient,
            "Diagnoses": num_diagnoses,
            "Medications": num_medications,
            "Insulin": insulin,
            "Medication_Change": med_change,
            "Diabetes_Med": diabetes_med,
            "A1C": a1c_category
        }

        # 🔹 Run model
        with st.spinner("Analyzing readmission risk..."):
            prediction = rule_based_readmission_risk(base_data)

        # 🔹 Store full record
        full_record = {
            **base_data,
            "prediction": prediction
        }

        st.session_state["patient_data"] = full_record
        st.session_state["patient_history"].insert(0, full_record)

        # limit history
        st.session_state["patient_history"] = st.session_state["patient_history"][:10]

        # 🔹 Redirect to Summary page
        st.session_state["page"] = "Summary"
        st.rerun()


# SUMMARY PAGE

elif page == "Summary":
    st.title("📋 Patient Summary")

    data = st.session_state.get("patient_data")

    if data is None or not isinstance(data, dict):
        st.warning("No patient selected.")
        st.stop()
    else:
        data = st.session_state["patient_data"]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Age", data["Age"])
        col2.metric("Diagnoses", data["Diagnoses"])
        col3.metric("Medications", data["Medications"])
        col4.metric("Hospital Days", data["Time_in_Hospital"])

        st.markdown("---")

        # 🔹 Prediction section (NOW CORRECTLY TIED TO PATIENT)
        pred = data.get("prediction", {})

        st.subheader("🧠 Readmission Risk Prediction")

        col1, col2 = st.columns(2)
        col1.metric("Risk (%)", f"{pred.get('readmission_risk_percent', 0):.2f}%")
        col2.metric("Category", pred.get("risk_category", "N/A"))

        # Color indicator
        if pred.get("risk_category") == "High":
            st.error("🔴 High Risk Patient")
        elif pred.get("risk_category") == "Moderate":
            st.warning("🟡 Moderate Risk")
        else:
            st.success("🟢 Low Risk")

        st.markdown("### 🧾 Explanation")
        st.write(pred.get("explanation", ""))

        st.markdown("### ⚠️ Top Risk Factors")
        st.write(pred.get("top_features", []))

        st.markdown("### 🛡️ Protective Factors")
        st.write(pred.get("protective_factors", []))

        st.markdown("### 📌 Recommended Action")
        st.write(pred.get("recommended_action", ""))

        st.markdown("---")

        st.subheader("📊 Full Patient Data")
        st.json(data)           
#
# HISTORY PAGE
#
elif page == "History":
    st.title("🕘 Patient History")

    history = st.session_state["patient_history"]

    if len(history) == 0:
        st.warning("No patient history available.")
    else:
        for i, record in enumerate(history):

            risk_cat = record.get("prediction", {}).get("risk_category", "N/A")

            with st.expander(
                f"{record.get('timestamp','N/A')} | Age {record.get('Age','N/A')} | Risk {risk_cat}"
                ):
                col1, col2 = st.columns(2)

                # 🔹 Prediction summary
                pred = record.get("prediction", {})

                with col1:
                    st.metric("Risk (%)", f"{pred.get('readmission_risk_percent', 0):.2f}%")
                    st.metric("Category", pred.get("risk_category", "N/A"))

                # 🔹 Load button
                with col2:
                    if st.button("🔍 Load Patient", key=f"load_{i}"):
                        st.session_state["patient_data"] = record
                        st.success("Patient loaded! Go to Summary page.")

                st.markdown("---")

                # 🔹 Explanation
                st.markdown("### 🧾 Explanation")
                st.write(pred.get("explanation", ""))

                # 🔹 Risk factors
                st.markdown("### ⚠️ Risk Factors")
                st.write(pred.get("top_features", []))

                st.markdown("### 🛡️ Protective Factors")
                st.write(pred.get("protective_factors", []))

                st.markdown("### 📌 Recommendation")
                st.write(pred.get("recommended_action", ""))

                st.markdown("---")

                # 🔹 Full patient data
                st.markdown("### 📊 Full Patient Data")
                st.json(record)

    # Clear history button
    if st.button("🗑 Clear History"):
        st.session_state["patient_history"] = []
        st.rerun()


# MODEL OUTPUT

