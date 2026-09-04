---
type: entity_specification
entity: secret
version: "0.15"
tags: [secret, credentials, kubernetes, security, key_value, crud, io]
tools:
  - new_dh_secret
  - get_dh_secret
  - import_dh_secret
  - list_dh_secrets
  - update_dh_secret
  - delete_dh_secret
  - save_dh_secret
  - refresh_dh_secret
  - export_dh_secret
  - set_dh_secret_value
  - read_dh_secret_value
description: "Specification and reference for the DigitalHub Secret entity: project-scoped key/value credentials backed by Kubernetes Secret Manager, with CRUD and set/read value operations."
---

# DigitalHub Secret Specification & SDK Guide

A **Secret** is a project-scoped, named key/value pair used to store sensitive
values (external API keys, storage credentials, database passwords, ...) so
they do not have to be embedded in function code. Secrets are backed by an
underlying secret manager; currently **Kubernetes Secret Manager** is the only
supported backend. Each project has its own Kubernetes secret object where all
its key/value pairs are stored.

---

## 1. Conceptual Model

A secret entity holds:

- **Metadata** — `name` (= the key inside the project's Kubernetes secret), `description`, `labels`, version (UUID).
- **Value** — a sensitive string kept in the secret manager (never returned by `list_secrets` or exported to YAML).

Secrets belong to a **Project** and are versioned like any other DigitalHub
entity. Specs are immutable; the sensitive **value** is _not_ part of the spec
and is mutated via a dedicated method (`set_secret_value`).

### 1.1 Read vs. list semantics

| Operation              | Returns entity metadata | Returns sensitive value |
| :--------------------- | :---------------------: | :---------------------: |
| `list_dh_secrets`      |           ✅            |           ❌            |
| `get_dh_secret`        |           ✅            |           ❌            |
| `export_dh_secret`     |    ✅ (to YAML file)    |           ❌            |
| `read_dh_secret_value` |           ❌            |           ✅            |

---

## 2. Supported Kinds

The `secret` entity has a single implicit kind — there is no `kinds` axis in
the SDK (unlike `function`, `dataitem`, `model`, etc.).

---

## 3. Secret Lifecycle

```text
[ 1. Create secret with value ]
        |  new_dh_secret(name, secret_value=...)
        v
[ 2. Persisted in backend + secret manager ]
        |
        v
[ 3. Consume from a function/workflow ]
        |  reference via 'secrets=[<name>]' in run/task specs
        v
[ 4. Rotate value ]
        |  set_dh_secret_value(name, new_value)
        v
[ 5. Read (audit / migration) ]
        |  read_dh_secret_value(name)
        v
[ 6. Delete ]
        |  delete_dh_secret(name, delete_all_versions=True)
```

---

## 4. SDK API Reference (DigitalHub 0.15)

### 4.1 Create — `dh.new_secret`

Creates the Secret entity and writes the value into the project's secret manager.

> **CRITICAL**: `secret_value` is **mandatory** in the DigitalHub SDK. Secrets cannot be created without providing a value.

```python
import digitalhub as dh

sec = dh.new_secret(
    project="my-project",
    name="openai-api-key",
    secret_value="sk-...",
    description="OpenAI API key for LLM function",
    labels=["team:mlops", "env:prod"],
)
```

**Parameters:**

- `project` (_str_, required) — project name.
- `name` (_str_, required) — becomes the key inside the project's Kubernetes secret (must be lowercase alphanumeric kebab-case).
- `secret_value` (_str_, required) — the sensitive payload string.
- `uuid` (_str_, optional) — specific version ID.
- `description` (_str_, optional) — human-readable description.
- `labels` (_list[str]_, optional) — resource tags.
- `embedded` (_bool_, default `False`)
- `**kwargs`: additional spec keyword arguments.

**Agent tool:** `new_dh_secret(project, name, secret_value, uuid, description, labels, embedded, kwargs)`

### 4.2 Read

#### `get_secret`

Fetch a single secret by name or key.

```python
sec = dh.get_secret("openai-api-key", project="my-project")
sec = dh.get_secret("store://my-project/secret/secret/openai-api-key:<id>")
```

**Agent tool:** `get_dh_secret(identifier, project, entity_id)`

#### `get_secret_versions`

Returns all versions of a secret.
**Agent tool:** `get_dh_secret_versions(identifier, project)`

#### `list_secrets`

Lists latest secret versions of a project. **No filters** are supported for
this call — the only parameter is `project`.
**Agent tool:** `list_dh_secrets(project)`

#### `import_secret`

Load a secret from a local YAML file or a store key. The YAML contains only
metadata — the sensitive value must be set separately via `set_dh_secret_value`.
**Agent tool:** `import_dh_secret(file, key, reset_id, context)`

### 4.3 Update / Delete

#### `update_secret`

Metadata-only update; the sensitive value is mutated via `set_secret_value`.
**Agent tool:** `update_dh_secret(project_name, name)`

#### `delete_secret`

Delete one version or all versions. Removes the corresponding key/value from
the project's Kubernetes secret.

```python
dh.delete_secret("openai-api-key", project="my-project", delete_all_versions=True)
```

**Agent tool:** `delete_dh_secret(identifier, project, entity_id, delete_all_versions)`

> Note: unlike `delete_function` / `delete_workflow` / `delete_artifact` / `delete_model`, `delete_secret` does **not** accept a `cascade` argument.

---

## 5. Secret Object Methods

### 5.1 CRUD-object methods

| Method      | Purpose                                           | Agent tool          |
| :---------- | :------------------------------------------------ | :------------------ |
| `save()`    | Persist / update the entity in the backend        | `save_dh_secret`    |
| `refresh()` | Reload state from backend                         | `refresh_dh_secret` |
| `export()`  | Export **metadata** as YAML in the context folder | `export_dh_secret`  |

> `export()` produces a metadata-only YAML descriptor — the sensitive value is
> **not** included, so re-imported YAMLs must be paired with a
> `set_dh_secret_value` call to restore the actual credential.

### 5.2 I/O methods

| Method                | Purpose                                                | Agent tool             |
| :-------------------- | :----------------------------------------------------- | :--------------------- |
| `set_secret_value(v)` | Update (write) the secret's stored value               | `set_dh_secret_value`  |
| `read_secret_value()` | Read the secret's stored value from the secret manager | `read_dh_secret_value` |

`set_secret_value` parameters:

- `value` (str, required): new sensitive value; overwrites any previous one.

`read_secret_value` parameters: none. Returns the sensitive value as a `str`.

### 5.3 Kind-specific methods

None. Secrets have no additional kind-specific methods.

---

## 6. End-to-end Recipes

### 6.1 Create a new secret and consume it in a function job

```python
import digitalhub as dh

sec = dh.new_secret(
    project="my-project",
    name="openai-api-key",
    secret_value="sk-...",
)

fn = dh.get_function("classify", project="my-project")
run = fn.run(
    action="job",
    secrets=["openai-api-key"],   # by-name reference; the runtime mounts the value as env var
    parameters={"prompt": "Hello"},
)
```

Agent-tool equivalent:

```
new_dh_secret(project="my-project", name="openai-api-key", secret_value="sk-...")
run_dh_python_job(project_name="my-project", name="classify",
                  secrets=["openai-api-key"],
                  parameters={"prompt": "Hello"})
```

### 6.2 Rotate a secret value

```python
sec = dh.get_secret("openai-api-key", project="my-project")
sec.set_secret_value("sk-new-rotated-key")
```

Agent-tool equivalent:

```
set_dh_secret_value(project_name="my-project", name="openai-api-key",
                    value="sk-new-rotated-key")
```

### 6.3 Read a secret value for audit or migration

```python
sec = dh.get_secret("openai-api-key", project="my-project")
value = sec.read_secret_value()
# Do NOT log or persist 'value' — treat as sensitive.
```

Agent-tool equivalent:

```
read_dh_secret_value(project_name="my-project", name="openai-api-key")
```

### 6.4 Bulk migration of secrets from environment variables

```python
import os
import digitalhub as dh

for key in ("OPENAI_API_KEY", "HF_TOKEN", "AWS_SECRET_ACCESS_KEY"):
    dh.new_secret(
        project="my-project",
        name=key.lower().replace("_", "-"),
        secret_value=os.environ[key],
        labels=["source:env-migration"],
    )
```

### 6.5 Delete all versions of a secret

```python
dh.delete_secret("openai-api-key", project="my-project", delete_all_versions=True)
```

Agent-tool equivalent:

```
delete_dh_secret(identifier="openai-api-key", project="my-project",
                 delete_all_versions=True)
```

---

## 7. Operational Guidance for the Agent

- **Never echo, log, or persist a secret value** returned by `read_dh_secret_value` — treat the return value as sensitive and drop it from tool traces once used.
- **Do not solicit secret values through user-prompt tools** (e.g. `vscode_askQuestions`). Instruct the user to paste the value directly into a terminal or provide it inline; then call the tool once.
- **Use the entity `name` as the reference key** when attaching secrets to a function/workflow run (`secrets=["<name>"]` in `run_dh_function`, `run_dh_python_job`, `run_dh_workflow`, etc.). The runtime materialises the value at execution time.
- **No filters on `list_dh_secrets`** — the only parameter is `project`. Combine with `get_dh_secret` for detail lookups.
- **No `cascade` on delete** — `delete_dh_secret` differs from most other delete tools; there is no cascade flag.
- **Metadata immutability** — the entity spec is immutable across versions; use `set_dh_secret_value` to rotate the sensitive value in place. New metadata (description/labels) requires a new version via `new_dh_secret`.
- **YAML export is metadata-only** — after `import_dh_secret`, you must pair the import with a `set_dh_secret_value` call to restore the sensitive value.
- **Backend requirement** — secrets rely on Kubernetes Secret Manager; on non-Kubernetes deployments the SDK calls will fail with a backend error.
- **Difference vs. other entities** — Secret has no `kinds` axis and no `path`/artifact-store surface. Do not confuse it with `Artifact` (binary files) or platform credentials for stores (S3/SQL/Git) which are configured via environment variables, not secret entities.
