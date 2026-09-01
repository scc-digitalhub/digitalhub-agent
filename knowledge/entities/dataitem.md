---
type: entity_specification
entity: dataitem
version: "0.16"
tags: [dataitem, table, croissant, dataset, files, upload, download, s3, crud]
tools:
  - register_dh_dataitem
  - log_dh_dataitem
  - get_dh_dataitem
  - download_dh_dataitem
  - upload_dh_dataitem
  - list_dh_dataitems
  - export_dh_dataitem
  - import_dh_dataitem
  - delete_dh_dataitem
description: "Specification and reference for the DigitalHub DataItem entity, covering datasets, tables, Croissant formats, and storage upload/download."
---

# DigitalHub DataItem Specification & Storage Guide

A **DataItem** represents a data resource inside a DigitalHub project. It bridges data files, tabular records, and ML metadata schemas with backend storage (e.g., S3, local volumes, SQL engines).

---

## 1. Supported DataItem Kinds

| Kind | Description | Use Cases |
| :--- | :--- | :--- |
| **`dataitem`** | Unstructured files, images, directories, or raw blobs | Raw logs, audio, image sets, zip archives, text files |
| **`table`** | Tabular datasets (CSV, Parquet, SQL tables, Pandas DataFrames) | Feature tables, clean relational datasets, SQL views |
| **`croissant`** | ML dataset standard with rich metadata specification | HuggingFace datasets, machine learning training sets |

---

## 2. Core Architectural Distinction: Register vs. Log

Understanding this difference is critical for proper tool selection:

- **`register_dh_dataitem` (`dh.new_dataitem`)**:
  - **Metadata-only registration**: Creates a DataItem reference pointing to an existing file path, remote URI, or bucket location *without* reading, copying, or uploading file content.
  - Use when the file already resides in cloud storage or an external URI.

- **`log_dh_dataitem` (`dh.log_dataitem`)**:
  - **Upload + Registration**: Takes a local file, local directory, or Pandas DataFrame, uploads it to DigitalHub managed storage, and registers the metadata record in one atomic operation.
  - Use when ingesting new files from the local filesystem or logging newly transformed DataFrames.

---

## 3. SDK API Reference (DigitalHub 0.16)

### 3.1 Register DataItem Metadata (`dh.new_dataitem`)
Creates a DataItem entity reference without uploading files.

```python
import digitalhub as dh

di = dh.new_dataitem(
    project="customer-analytics",
    name="raw-transactions",
    kind="table",
    path="s3://my-bucket/data/transactions.parquet",
    description="Transactions metadata reference"
)
```

**Parameters:**
- `project` (*str*, required): Project name.
- `name` (*str*, required): DataItem name.
- `kind` (*str*, default=`"dataitem"`): Kind of dataitem (`"dataitem"`, `"table"`, `"croissant"`).
- `path` (*str*, optional): Remote or local path URI.

**Agent Tool Mapping:** `register_dh_dataitem(project_name, name, kind, path)`

---

### 3.2 Log & Upload DataItem (`dh.log_dataitem`)
Uploads a local file/directory or registers dataset content to project storage.

```python
di = dh.log_dataitem(
    project="customer-analytics",
    name="clean-customers",
    kind="table",
    source="./data/clean_customers.csv",
    description="Cleaned customer records table"
)
```

**Parameters:**
- `project` (*str*, required): Project name.
- `name` (*str*, required): DataItem name.
- `source` (*str*, required): Local path to file or directory.
- `kind` (*str*, default=`"dataitem"`): `"dataitem"`, `"table"`, `"croissant"`.
- `path` (*str*, optional): Custom target storage path destination.
- `description` (*str*, optional): Description.

**Agent Tool Mapping:** `log_dh_dataitem(project_name, name, source, kind, path, description)`

---

### 3.3 Retrieve DataItem (`dh.get_dataitem`)
Gets a DataItem instance from backend.

```python
# Using entity name and project
di = dh.get_dataitem("clean-customers", project="customer-analytics")

# Using store URI key
di = dh.get_dataitem("store://customer-analytics/dataitem/table/clean-customers")
```

**Parameters:**
- `identifier` (*str*, required): DataItem name or store URI.
- `project` (*str*, optional): Project name.
- `entity_id` (*str*, optional): Specific version UUID.

**Agent Tool Mapping:** `get_dh_dataitem(project_name, name, version)`

---

### 3.4 Download DataItem (`di.download`)
Downloads file(s) from project storage to a destination path on the local filesystem.

```python
di = dh.get_dataitem("clean-customers", project="customer-analytics")
local_path = di.download(destination="./downloads", overwrite=True)
```

**Agent Tool Mapping:** `download_dh_dataitem(project_name, name, destination, overwrite)`

---

### 3.5 Upload to DataItem (`di.upload`)
Uploads new files to the storage location backing an existing DataItem.

```python
di = dh.get_dataitem("raw-transactions", project="customer-analytics")
di.upload(source="./updates/batch2.parquet", keep_dir_structure=False)
```

**Agent Tool Mapping:** `upload_dh_dataitem(project_name, name, source, keep_dir_structure)`

---

### 3.6 List DataItems (`dh.list_dataitems`)
Lists all DataItems in a project, with optional filtering by kind.

```python
tables = dh.list_dataitems(project="customer-analytics", kind="table")
```

**Agent Tool Mapping:** `list_dh_dataitems(project_name, kind)`

---

### 3.7 Export and Import DataItems
- **Export**: `di.export()` saves the DataItem schema/spec as a local YAML file.
- **Import**: `dh.import_dataitem(file="spec.yaml", context="customer-analytics")` recreates a DataItem from a YAML definition.

**Agent Tool Mapping:**
- `export_dh_dataitem(project_name, name)`
- `import_dh_dataitem(project_name, file, key)`

---

### 3.8 Delete DataItem (`dh.delete_dataitem`)
Deletes a specific DataItem version or all versions.

```python
dh.delete_dataitem(
    identifier="clean-customers", 
    project="customer-analytics", 
    delete_all_versions=True
)
```

**Agent Tool Mapping:** `delete_dh_dataitem(project_name, name, version, delete_all_versions)`
> **Safety Rule:** Always confirm before deleting DataItems.

---

## 4. Best Practices for Agents

1. **Choose Between Log & Register Carefully**:
   - If the user provides a local file path (`./data.csv`), use `log_dh_dataitem` to upload it.
   - If the user specifies an existing storage URI (`s3://...` or `store://...`), use `register_dh_dataitem`.
2. **Tabular Data**: Always specify `kind="table"` for CSV/Parquet/SQL datasets to enable schema inspection in downstream functions.
3. **ML Datasets**: Use `kind="croissant"` for machine learning datasets adhering to MLCommons Croissant format.
