---
type: workflow_recipes
version: "0.16"
tags: [recipes, pipelines, e2e, mlops, dataops, workflows]
description: "End-to-end workflow playbooks for common data engineering, machine learning training, and deployment scenarios in DigitalHub."
---

# DigitalHub End-to-End Workflow Recipes

This document provides step-by-step recipes for recurring MLOps and DataOps workflows.

---

## Recipe 1: End-to-End Data Ingestion & Transformation Pipeline

### Objective
Ingest raw CSV data, register it as a DataItem, create a Python transformation function to clean features, and execute the batch job.

### Step-by-Step Tool Execution Sequence:

1. **Create/Verify Project**:
   ```python
   # Tool: new_dh_project
   new_dh_project(name="etl-demo", description="Automated data transformation workspace")
   ```

2. **Log Raw Dataset**:
   ```python
   # Tool: log_dh_dataitem
   log_dh_dataitem(
       project_name="etl-demo",
       name="raw-sales",
       source="./data/raw_sales.csv",
       kind="table",
       description="Raw daily sales transactional records"
   )
   ```

3. **Register Python Clean Function**:
   ```python
   # Tool: new_dh_function
   code = """
from digitalhub_runtime_python import handler
import pandas as pd

@handler(outputs=["clean_sales"])
def clean_sales_data(project, raw_sales):
    df = raw_sales.as_df()
    df['amount'] = df['amount'].fillna(0.0)
    df['date'] = pd.to_datetime(df['date'])
    return df
"""
   new_dh_function(
       project="etl-demo",
       name="clean-sales-fn",
       kind="python",
       code=code,
       requirements=["pandas", "pyarrow"]
   )
   ```

4. **Build Function**:
   ```python
   # Tool: run_dh_python_build
   run_dh_python_build(project_name="etl-demo", name="clean-sales-fn")
   ```

5. **Run Batch Job**:
   ```python
   # Tool: run_dh_python_job
   run_dh_python_job(
       project_name="etl-demo",
       name="clean-sales-fn",
       inputs={"raw_sales": "raw-sales"}
   )
   ```

---

## Recipe 2: Machine Learning Model Training & Tracking

### Objective
Train a Scikit-Learn classifier on tabular data, log evaluation metrics to the active Run, and export the trained model artifact to the project.

### Tool Execution Sequence:

1. **Register Training Function**:
   ```python
   code = """
from digitalhub_runtime_python import handler
from sklearn.ensemble import GradientBoostingClassifier
import joblib, os

@handler(outputs=["eval_metrics"])
def train_pipeline(project, run, dataset, n_estimators=100):
    df = dataset.as_df()
    X = df.drop("target", axis=1)
    y = df["target"]
    
    model = GradientBoostingClassifier(n_estimators=n_estimators)
    model.fit(X, y)
    score = model.score(X, y)
    
    # Track metrics in Run
    run.log_metric("train_score", score)
    
    # Save & Log Model in Project
    os.makedirs("./output_model", exist_ok=True)
    joblib.dump(model, "./output_model/model.joblib")
    logged_model = project.log_model(
        name="sales-classifier",
        kind="sklearn",
        source="./output_model/model.joblib",
        metrics={"train_score": score}
    )
    return {"status": "trained", "score": score}
"""
   new_dh_function(
       project="etl-demo",
       name="train-classifier",
       kind="python",
       code=code,
       requirements=["scikit-learn", "pandas", "joblib"]
   )
   ```

2. **Build Function**:
   ```python
   # Tool: run_dh_python_build
   run_dh_python_build(project_name="etl-demo", name="train-classifier")
   ```

3. **Execute Training Run**:
   ```python
   # Tool: run_dh_python_job
   run_dh_python_job(
       project_name="etl-demo",
       name="train-classifier",
       inputs={"dataset": "clean_sales"},
       parameters={"n_estimators": 150}
   )
   ```

4. **Verify Run Outputs & Results**:
   ```python
   # Tool: get_dh_run_outputs / get_dh_run_results
   get_dh_run_outputs(project="etl-demo", run_id="<run_id>")
   get_dh_run_results(project="etl-demo", run_id="<run_id>")
   ```
