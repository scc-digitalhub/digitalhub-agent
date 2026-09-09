---
type: knowledge_catalog
name: digitalhub_knowledge_catalog
version: "0.16"
description: "Master catalog and index of DigitalHub Open Knowledge Format (OKF) documentation."
topics:
  - id: "project"
    type: "entity_specification"
    title: "DigitalHub Project Entity & SDK Guide"
    path: "entities/project.md"
    tags: [project, core, workspace, permissions, search, crud]
    summary: "Project lifecycle, CRUD operations, entity search, access sharing, and YAML export."
  - id: "dataitem"
    type: "entity_specification"
    title: "DigitalHub DataItem Entity & Storage Guide"
    path: "entities/dataitem.md"
    tags:
      [dataitem, table, croissant, dataset, files, upload, download, s3, crud]
    summary: "DataItem metadata registration vs content logging, dataset kinds (table, croissant, files), and storage upload/download."
  - id: "function"
    type: "entity_specification"
    title: "DigitalHub Function Entity & SDK Guide"
    path: "entities/function.md"
    tags:
      [
        function,
        executable,
        python,
        dbt,
        container,
        hera,
        modelserve,
        flower,
        crud,
        tasks,
        triggers,
      ]
    summary: "Function entity CRUD, generic run() method, task and trigger methods, and enumeration of supported kinds (python, guardrail, openinference, dbt, container, modelserve, flower) with links to runtime docs."
  - id: "run"
    type: "entity_specification"
    title: "DigitalHub Run Entity & Execution Guide"
    path: "entities/run.md"
    tags:
      [run, execution, lifecycle, metrics, outputs, results, invoke, logs, crud]
    summary: "Run entity CRUD (UUID-addressed, no versions), lifecycle methods (wait/stop/resume/logs), metric logging, output/result readers, and service invoke() — the entity produced by Function.run() and Workflow.run()."
  - id: "python"
    type: "runtime_specification"
    title: "DigitalHub Python Runtime & Handler Guide"
    path: "runtimes/python.md"
    tags:
      [
        runtime,
        python,
        handler,
        job,
        serve,
        build,
        inputs,
        parameters,
        requirements,
        python_version,
        nuclio,
      ]
    summary: "Python runtime spec (kind='python'): @handler decorator, reserved arguments, function spec fields (python_version, code_src, handler, requirements, base_image, init_function), and job/serve/build action parameters (task + run) with local-vs-remote execution."
  - id: "workflow"
    type: "entity_specification"
    title: "DigitalHub Workflow Entity & Hera Pipeline Guide"
    path: "entities/workflow.md"
    tags:
      [
        workflow,
        pipeline,
        dag,
        hera,
        argo,
        orchestration,
        mlops,
        crud,
        tasks,
        triggers,
      ]
    summary: "Workflow entity CRUD, Hera runtime (build/pipeline actions), pipeline definition DSL (step, DAG), tasks, triggers, and end-to-end recipe."
  - id: "trigger"
    type: "entity_specification"
    title: "DigitalHub Trigger Entity & Automation Guide"
    path: "entities/trigger.md"
    tags:
      [
        trigger,
        scheduler,
        lifecycle,
        cron,
        automation,
        event,
        orchestration,
        crud,
      ]
    summary: "Trigger entity CRUD, scheduler (Quartz cron) and lifecycle (event-driven) kinds, spec fields (task/function/workflow/schedule/key/states/template), stop/save/refresh, and creation from function/workflow objects."
  - id: "artifact"
    type: "entity_specification"
    title: "DigitalHub Artifact Entity & Storage Guide"
    path: "entities/artifact.md"
    tags: [artifact, files, binary, storage, upload, download, s3, crud, io]
    summary: "Artifact entity CRUD (new/log/log_generic), register-vs-log distinction, generic kind spec (path), object methods (save/refresh/export), and I/O methods (as_file/download/upload)."
  - id: "model"
    type: "entity_specification"
    title: "DigitalHub Model Entity & ML Storage Guide"
    path: "entities/model.md"
    tags:
      [
        model,
        ml,
        mlflow,
        sklearn,
        huggingface,
        metrics,
        storage,
        upload,
        download,
        crud,
        io,
      ]
    summary: "Model entity CRUD (new/log + framework-specific log_mlflow/log_sklearn/log_huggingface), kinds (model/mlflow/sklearn/huggingface) with base + kind-specific spec, I/O methods, and log_metric/log_metrics for training tracking."
  - id: "secret"
    type: "entity_specification"
    title: "DigitalHub Secret Entity & Credentials Guide"
    path: "entities/secret.md"
    tags: [secret, credentials, kubernetes, security, key_value, crud, io]
    summary: "Secret entity CRUD (single kind), project-scoped key/value credentials backed by Kubernetes Secret Manager, metadata-only export, and set_secret_value/read_secret_value I/O methods."
  - id: "troubleshooting"
    type: "troubleshooting_guide"
    title: "DigitalHub SDK Troubleshooting & Error Recovery Guide"
    path: "troubleshooting/sdk_errors.md"
    tags: [troubleshooting, errors, exceptions, self_healing, debugging]
    summary: "Diagnosis and remediation steps for common SDK runtime exceptions, configuration errors, and build failures."
  - id: "governance"
    type: "governance_standard"
    title: "DigitalHub Platform Governance & Standards"
    path: "governance/standards.md"
    tags:
      [governance, standards, naming_conventions, labels, compliance, security]
    summary: "Platform standards for resource naming, mandatory metadata labeling, and operational security."
---

# DigitalHub Knowledge Catalog (OKF)

Welcome to the DigitalHub Open Knowledge Format (OKF) Knowledge Base. This knowledge base provides modular, structured, and version-controlled technical documentation for the DigitalHub SDK (v0.16).

## Available Documentation Topics

| Topic ID              | Entity / Domain  | Document Type         | Description                                                                                                                                                               |
| :-------------------- | :--------------- | :-------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **`project`**         | `Project`        | Entity Specification  | Complete reference for creating, listing, searching, sharing, and exporting DigitalHub projects.                                                                          |
| **`dataitem`**        | `DataItem`       | Entity Specification  | Complete guide for managing datasets (`table`, `croissant`, `dataitem`), uploading/downloading files, and storage interactions.                                           |
| **`function`**        | `Function`       | Entity Specification  | Function entity CRUD, generic `run()`, tasks and triggers, and the kinds table (`python`, `dbt`, `container`, `modelserve`, `flower`, ...) linking to each runtime.       |
| **`run`**             | `Run`            | Entity Specification  | Execution entity: CRUD, lifecycle (`wait`/`stop`/`resume`/`logs`), metrics, outputs/results, and `invoke` for served endpoints — the entity produced by `Function.run()`. |
| **`python`**          | Python runtime   | Runtime Specification | Python runtime (kind `python`): `@handler` decorator, function spec (`python_version`, `code_src`, `handler`, `requirements`, ...), and `job`/`serve`/`build` actions.    |
| **`workflow`**        | `Workflow`       | Entity Specification  | DAG-based pipeline orchestration, Hera runtime `build`/`pipeline` actions, pipeline DSL (`step`, `DAG`), tasks and triggers.                                              |
| **`trigger`**         | `Trigger`        | Entity Specification  | Scheduler (Quartz cron) and lifecycle (event-driven) triggers, CRUD, `stop()`, template/inputs, and creation from functions/workflows.                                    |
| **`artifact`**        | `Artifact`       | Entity Specification  | Binary/file artifacts: register-vs-log, generic `artifact` kind spec (`path`), CRUD, and I/O methods (`as_file`, `download`, `upload`).                                   |
| **`model`**           | `Model`          | Entity Specification  | ML models: generic + `mlflow`/`sklearn`/`huggingface` kinds, framework-specific log helpers, I/O methods, and metrics tracking (`log_metric`, `log_metrics`).             |
| **`secret`**          | `Secret`         | Entity Specification  | Project-scoped key/value credentials (Kubernetes Secret Manager), CRUD, metadata-only YAML export, and `set_secret_value`/`read_secret_value` I/O.                        |
| **`troubleshooting`** | `Error Recovery` | Troubleshooting Guide | SDK exception recovery, configuration debugging, and self-healing recommendations.                                                                                        |
| **`governance`**      | `Standards`      | Governance Standard   | Naming conventions, mandatory label schemas, and security standards.                                                                                                      |

## How to Retrieve Knowledge

Use the knowledge tools to query these documents dynamically:

- `list_knowledge_topics()`: View all available knowledge topics and summaries.
- `get_knowledge_doc(topic, section=None)`: Read full documentation or specific section for a topic.
- `search_knowledge(query)`: Search across all documents for specific SDK functions, parameters, or concepts.
