
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import shap
import joblib

from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline

from xgboost import XGBClassifier

#stop pop ups
import matplotlib
matplotlib.use('Agg')

# Load dataset
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "diabetic_data.csv")

df = pd.read_csv(DATA_PATH)


print(df.shape)
print(df["readmitted"].value_counts())
df.head()

# Convert readmission outcome to binary
df["readmitted_binary"] = df["readmitted"].apply(lambda x: 1 if x == "<30" else 0)

# Remove ID columns
df = df.drop(columns=["encounter_id", "patient_nbr", "readmitted"])

# Replace missing indicators
df = df.replace("?", np.nan)

# Drop rows with missing values
# Replace missing values
df = df.replace("?", np.nan)

# Fill missing categorical values with "Unknown"
for col in df.select_dtypes(include=["object"]).columns:
    df[col] = df[col].fillna("Unknown")

# Fill numeric missing values with median
for col in df.select_dtypes(include=["int64","float64"]).columns:
    df[col] = df[col].fillna(df[col].median())
# Separate features and target
#X = df.drop("readmitted_binary", axis=1)
#y = df["readmitted_binary"]

# SELECT ONLY GUI FEATURES

# ----------------------------
# GUI-compatible features only
# ----------------------------

selected_features = [
    "age",
    "gender",
    "time_in_hospital",
    "num_medications",
    "number_diagnoses",
    "number_inpatient",
    "number_emergency",
    "number_outpatient",
    "A1Cresult",
    "insulin",
    "change",
    "diabetesMed",
    "weight"
]

X = df[selected_features]

y = df["readmitted_binary"]

print(X.shape)

# Identify categorical and numeric variables
categorical_cols = X.select_dtypes(include=["object"]).columns
numeric_cols = X.select_dtypes(include=["int64","float64"]).columns

# Preprocessing pipeline
preprocessor = ColumnTransformer(
    transformers=[
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_cols),
        ("num", "passthrough", numeric_cols)
    ]
)

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

scale_pos_weight = len(y_train[y_train == 0]) / len(y_train[y_train == 1])

xgb_model = XGBClassifier(
    n_estimators=300,
    max_depth=5,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    scale_pos_weight=scale_pos_weight,  # 🔥 KEY FIX
    random_state=42,
    eval_metric="logloss"
)

# Build pipeline
model_pipeline = Pipeline(
    steps=[
        ("preprocess", preprocessor),
        ("model", xgb_model)
    ]
)

# Train model
model_pipeline.fit(X_train, y_train)

# Predictions
y_pred = model_pipeline.predict(X_test)
y_prob = model_pipeline.predict_proba(X_test)[:,1]

# Evaluation
print("Accuracy:", accuracy_score(y_test, y_pred))
print("ROC-AUC:", roc_auc_score(y_test, y_prob))
print(classification_report(y_test, y_pred))

# Get trained model
model = model_pipeline.named_steps["model"]

# Feature importance
importances = model.feature_importances_

#plt.figure(figsize=(10,6))
#plt.bar(range(len(importances)), importances)
#plt.title("XGBoost Feature Importance")
#plt.show()

# SHAP explanations
X_test_processed = model_pipeline.named_steps["preprocess"].transform(X_test)

explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test_processed)

shap.summary_plot(shap_values, X_test_processed)


# Save model
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(BASE_DIR, "xgboost_readmission_model.pkl")

# Save model
joblib.dump(model_pipeline, MODEL_PATH)
