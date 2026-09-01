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
    tags: [dataitem, table, croissant, dataset, files, upload, download, s3, crud]
    summary: "DataItem metadata registration vs content logging, dataset kinds (table, croissant, files), and storage upload/download."
  - id: "python_function"
    type: "runtime_specification"
    title: "DigitalHub Function (Python Runtime) & Handler Guide"
    path: "runtimes/python_function.md"
    tags: [function, python, handler, build, job, serve, ml, metrics, models, runs, tasks]
    summary: "Python function lifecycle, @handler decorator, input/parameter handling, model/metric logging, build/job execution."
  - id: "recipes"
    type: "workflow_recipes"
    title: "DigitalHub End-to-End Workflow Recipes"
    path: "workflows/recipes.md"
    tags: [recipes, pipelines, e2e, mlops, dataops, workflows]
    summary: "Step-by-step playbooks for data ingestion, ML model training pipelines, and real-time function serving."
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
    tags: [governance, standards, naming_conventions, labels, compliance, security]
    summary: "Platform standards for resource naming, mandatory metadata labeling, and operational security."
---

# DigitalHub Knowledge Catalog (OKF)

Welcome to the DigitalHub Open Knowledge Format (OKF) Knowledge Base. This knowledge base provides modular, structured, and version-controlled technical documentation for the DigitalHub SDK (v0.16).

## Available Documentation Topics

| Topic ID | Entity / Domain | Document Type | Description |
| :--- | :--- | :--- | :--- |
| **`project`** | `Project` | Entity Specification | Complete reference for creating, listing, searching, sharing, and exporting DigitalHub projects. |
| **`dataitem`** | `DataItem` | Entity Specification | Complete guide for managing datasets (`table`, `croissant`, `dataitem`), uploading/downloading files, and storage interactions. |
| **`python_function`** | `Function` (Python) | Runtime Specification | Full guide on writing `@handler` code, function creation, container builds, batch jobs, real-time serving, and metric/model logging. |
| **`recipes`** | `Workflows` | Workflow Recipes | Complete end-to-end recipes for multi-step data engineering and MLOps pipelines. |
| **`troubleshooting`** | `Error Recovery` | Troubleshooting Guide | SDK exception recovery, configuration debugging, and self-healing recommendations. |
| **`governance`** | `Standards` | Governance Standard | Naming conventions, mandatory label schemas, and security standards. |

## How to Retrieve Knowledge
Use the knowledge tools to query these documents dynamically:
- `list_knowledge_topics()`: View all available knowledge topics and summaries.
- `get_knowledge_doc(topic, section=None)`: Read full documentation or specific section for a topic.
- `search_knowledge(query)`: Search across all documents for specific SDK functions, parameters, or concepts.
