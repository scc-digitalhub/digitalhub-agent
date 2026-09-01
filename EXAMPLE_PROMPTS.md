# DigitalHub Agent - Example Prompts & Test Suite

Copy and paste these prompts directly into the agent CLI (`python main.py`), Jupyter Notebook (`agentic_etl_tutorial.ipynb`), or LangGraph Studio to test end-to-end workflows across Projects and all 3 Dataitem kinds (`table`, `dataitem`, `croissant`).

> **Note:** The tools are now pure SDK wrappers. The LLM must handle object representations directly and resolve any native SDK errors.

---

### Step 1: Project Creation & Multi-Kind Data Registration

```text
1. Create a DigitalHub project named 'my-agentic-testing' with description 'Test Suite'.
2. Register a 'table' kind dataitem named 'raw_bologna_traffic' with path 'https://opendata.comune.bologna.it/api/explore/v2.1/catalog/datasets/rilevazione-flusso-veicoli-tramite-spire-anno-2023/exports/csv?limit=50000&lang=it&timezone=Europe%2FRome&use_labels=true&delimiter=%3B'.
3. Log a generic file 'dataitem' named 'sensor_logs' from local source 'logs.txt'.
4. Log a 'croissant' dataset named 'zalando-datasets' from source 'https://huggingface.co/api/datasets/zalando-datasets/fashion_mnist/croissant'.
```

---

### Step 2: Object Inspection & File Storage I/O

```text
In project 'my-agentic-testing':
1. Retrieve the dataitem 'raw_bologna_traffic' and summarize its metadata structure.
2. Retrieve the dataitem 'zalando-datasets' and check its spec.
3. Upload local file 'sensor_config.json' into the dataitem 'sensor_logs'.
4. Download the dataitem 'sensor_logs' to local directory 'downloaded_logs'.
```

---

### Step 3: Search, Project Sharing & Spec Export

```text
In project 'my-agentic-testing':
1. Search for all entities matching query 'traffic'.
2. Share the project with user 'msaloni@fbk.eu'.
3. Export the dataitem 'raw_bologna_traffic' to a local YAML file.
4. Import the dataitem back from the exported YAML file.
5. Export the entire project 'my-agentic-testing' definition to YAML.
```

---

### Step 4: Listing & Teardown Cleanup

```text
1. List all available DigitalHub projects.
2. List all dataitems in project 'my-agentic-testing' filtered by kind='table'.
3. Delete the dataitem 'sensor_logs' from 'my-agentic-testing'.
4. Unshare the project from user 'msaloni@fbk.eu'.
5. Delete the project 'my-agentic-testing'.
```

---

### Step 6: Scikit-Learn ML Workflow (`mlsklearn`) - Natural Language

```text
I want to train a machine learning model on iris dataset data. 
Please create a project called 'iris-ml-project', register the dataset from 'https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv', write a python function that trains a Scikit-Learn RandomForest classifier on it, build the function, and run the job to log the metrics and final model.
```

---

### Step 7: MLflow ML Workflow (`mlmlflow`) - Natural Language

```text
I want to build an MLflow tracking pipeline for wine quality prediction.
Create a project called 'wine-mlflow-project', load dataset from 'https://raw.githubusercontent.com/mlflow/mlflow-example/master/wine-quality.csv', write a python function to train an ElasticNet regression model with alpha=0.5 and l1_ratio=0.5 using MLflow tracking, build the function, and run the job to record the model and performance metrics.
```
