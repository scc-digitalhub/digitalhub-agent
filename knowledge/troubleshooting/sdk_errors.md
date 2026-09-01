---
type: troubleshooting_guide
domain: error_recovery
version: "0.16"
tags: [troubleshooting, errors, exceptions, self_healing, debugging]
description: "Diagnosis and remediation guide for common DigitalHub SDK exceptions and runtime errors."
---

# DigitalHub SDK Troubleshooting & Error Recovery Guide

This guide maps common DigitalHub SDK runtime errors and exceptions to their root causes and actionable remediation steps.

---

## 1. Authentication & Configuration Errors

### 1.1 `ClientError: Required configuration key 'DHCORE_ENDPOINT' is missing`

- **Cause**: The SDK client cannot locate the `DHCORE_ENDPOINT` environment variable or active profile.
- **Remediation**:
  1. Verify `.env` file exists and contains `DHCORE_ENDPOINT=https://...` and authentication tokens.
  2. In Python, ensure `from dotenv import load_dotenv; load_dotenv()` is executed before initializing DigitalHub.

### 1.2 `AuthenticationError: Token expired or invalid credentials`

- **Cause**: The personal access token or OAuth2 session token is invalid or expired.
- **Remediation**: Refresh credentials in `.env` or re-authenticate using `dh.refresh_token()`.

---

## 2. Project Errors

### 2.1 `ProjectNotFoundError: Project '<project-name>' does not exist`

- **Cause**: Attempted to access, register, or execute resources in a project that has not been created.
- **Remediation**:
  1. Call `list_dh_projects()` to inspect available projects.
  2. If the project does not exist, call `new_dh_project(name=...)` before proceeding with entity creation.

---

## 3. DataItem Errors

### 3.1 `InvalidSourcePath: Local file not found: '<path>'`

- **Cause**: `log_dh_dataitem` was invoked with a local `source` path that does not exist on disk.
- **Remediation**:
  1. Check if the file exists locally.
  2. If the data is already stored remotely (e.g. `s3://...` or `https://...`), switch to `register_dh_dataitem` (`dh.new_dataitem`) with the `path` parameter instead of `log_dh_dataitem`.

### 3.2 `DataItemExistsError: DataItem with name '<name>' already exists`

- **Cause**: Attempted to log or create a DataItem with an existing name when `drop_existing=False`.
- **Remediation**: Fetch the latest version with `get_dh_dataitem` or create a new version / specify a unique name.

---

## 4. Python Function & Runtime Errors

### 4.1 `ExecutionError: Function must be built before execution`

- **Cause**: Attempted to run `job_dh_function` or `serve_dh_function` on a function that has not completed a container `build` step.
- **Remediation**:
  1. Execute `build_dh_function(project_name=..., function_name=...)`.
  2. Wait for the build run to succeed (`COMPLETED` state).
  3. Re-run `job_dh_function`.

### 4.2 `HandlerExecutionError: Missing required positional argument`

- **Cause**: The handler function signature expects specific parameters or inputs that were not passed in `inputs={...}` or `parameters={...}` during the job run.
- **Remediation**:
  1. Consult [Python Function Runtime Guide](../runtimes/python_function.md) for parameter vs input semantics.
  2. Ensure all data entities are passed in `inputs={"arg_name": "entity_name"}` and scalars in `parameters={"arg_name": value}`.
  3. Note: `project` and `run` parameters are auto-injected by name and do not need to be passed in `inputs` or `parameters`.

### 4.3 `ModuleNotFoundError: No module named '<package>'`

- **Cause**: The function code imports a package that is not present in the base image and was omitted from `requirements`.
- **Remediation**:
  1. Update function definition with `requirements=["<package-name>"]`.
  2. Re-trigger `build_dh_function`.

---

## 5. Cross-References

- [Project Guide](../entities/project.md)
- [DataItem Guide](../entities/dataitem.md)
- [Python Function Guide](../runtimes/python_function.md)
- [Workflow Recipes](../workflows/recipes.md)
