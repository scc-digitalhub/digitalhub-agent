---
type: governance_standard
domain: standards_and_governance
version: "0.16"
tags: [governance, standards, naming_conventions, labels, compliance, security]
description: "Platform governance standards, resource naming conventions, mandatory metadata, and security guidelines."
---

# DigitalHub Platform Governance & Standards

This document defines platform standards for resource naming, metadata labeling, environment isolation, and operational safety.

---

## 1. Resource Naming Conventions

All resource names in DigitalHub must adhere to lowercase alphanumeric kebab-case:

- **Valid characters**: `[a-z0-9-]` (lowercase letters, numbers, hyphens).
- **Invalid characters**: Uppercase letters, spaces, underscores, periods, and special symbols.

| Entity       | Pattern                      | Examples                                             |
| :----------- | :--------------------------- | :--------------------------------------------------- |
| **Project**  | `<team>-<domain>`            | `finance-analytics`, `ml-fraud-detection`            |
| **DataItem** | `<descriptor>-<type>`        | `raw-transactions`, `cleaned-features-v1`            |
| **Function** | `<action>-<target>-fn`       | `preprocess-transactions-fn`, `train-churn-model-fn` |
| **Model**    | `<target>-<algorithm>-model` | `churn-xgboost-model`, `sales-forecast-arima-model`  |

---

## 2. Mandatory Metadata & Labeling

Every resource registered on the platform should include standardized labels for traceability:

```python
labels = [
    "env:production",       # Environment: 'development', 'staging', 'production'
    "owner:data-team",      # Owning team or user
    "stage:etl"             # Workflow stage: 'ingestion', 'etl', 'training', 'serving'
]
```

---

## 3. Environment Isolation & Safety Rules

1. **Destructive Operation Safeguards**:
   - Deletion of Projects, DataItems, or Functions in `production` environments MUST be explicitly verified with the user.
2. **Credential Hygiene**:
   - Never embed hardcoded API keys, database passwords, or personal access tokens in function source code strings or YAML specs.
   - Use DigitalHub Secret entities or environment injection for secrets.

---

## 4. Cross-References

- [Project Guide](../entities/project.md)
- [DataItem Guide](../entities/dataitem.md)
- [Python Function Guide](../runtimes/python.md)
