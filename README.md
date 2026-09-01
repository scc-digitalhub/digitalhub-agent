# DigitalHub Agent

[![license](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)
![Status](https://img.shields.io/badge/status-experimental-orange)

The DigitalHub Agent is a LangGraph-based conversational agent for managing ML and data engineering workflows on [DigitalHub CORE](https://github.com/scc-digitalhub/digitalhub-core). It exposes DigitalHub SDK operations as LLM-callable tools and supports both an interactive CLI and LangGraph Studio.

Explore the full platform documentation at the [link](https://scc-digitalhub.github.io/docs/).

---

## Architecture & Open Knowledge Format (OKF)

The Agent employs the **Open Knowledge Format (OKF)** to maintain modular, versioned technical documentation and SDK reference specifications outside of the static system prompt. This drastically reduces prompt token size, avoids context degradation, and allows the agent to dynamically look up SDK parameters and conventions on demand.

```
├── agent.py               # Agent factory (LLM + tools + middleware)
├── graph.py               # LangGraph entry point
├── main.py                # CLI runner
├── prompts.py             # Lean behavioral system prompt
├── settings.py            # Environment variable loading
├── knowledge/             # OKF Knowledge Base (YAML Frontmatter + Markdown)
│   ├── index.md           # Master catalog & routing
│   ├── entities/
│   │   ├── project.md     # Project entity & SDK specifications
│   │   └── dataitem.md    # DataItem entity & storage guide
│   ├── runtimes/
│   │   └── python_function.md # Python runtime, @handler guide, build & runs
│   ├── workflows/
│   │   └── recipes.md     # End-to-end multi-step workflow recipes
│   ├── troubleshooting/   # SDK error diagnosis & remediation guides
│   │   └── sdk_errors.md
│   └── governance/        # Platform standards & naming conventions
│       └── standards.md
├── tools/
│   ├── knowledge_tools.py # OKF tools (list_knowledge_topics, get_knowledge_doc, search_knowledge)
│   ├── project_tools.py   # DigitalHub project management tools
│   ├── dataitem_tools.py  # DigitalHub dataitem management tools
│   └── function_tools.py  # DigitalHub function (python runtime) tools
├── langgraph.json         # LangGraph configuration
├── requirements.txt       # Python dependencies
└── .env.example           # Environment variable template
```

---

## Prerequisites & Installation

### Build from source

Running the Agent requires:

- Python 3.10 or higher (Python 3.12 recommended)
- `pip`
- A running DigitalHub CORE instance (or local credentials / CLI login)
- An OpenAI-compatible LLM endpoint (e.g. VS Code Copilot API extension, vLLM, Ollama, or OpenAI)

Clone the repository and install the dependencies:

```bash
git clone https://github.com/scc-digitalhub/digitalhub-agent.git
cd digitalhub-agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Setting Up LLM with VS Code Copilot API Extension

If you have a GitHub Copilot subscription, you can use the **Copilot API** VS Code extension to expose your Copilot session as an OpenAI-compatible API endpoint for the DigitalHub Agent.

### Step 1: Install Required VS Code Extensions

1. Open Visual Studio Code.
2. Go to the Extensions view (`Ctrl+Shift+X` on Windows/Linux, `Cmd+Shift+X` on macOS).
3. Search for and install:
   - **GitHub Copilot** (`github.copilot`)
   - **GitHub Copilot Chat** (`github.copilot-chat`)
   - **Copilot API** (or **GitHub Copilot API Gateway**)

### Step 2: Authenticate GitHub Copilot

1. Ensure you are signed in to your GitHub account with an active Copilot subscription in VS Code (Accounts icon at bottom-left).
2. Verify that Copilot Chat works in the VS Code sidebar.

### Step 3: Start the Copilot API Server (Local or Cloudflare Tunnel)

The extension supports two hosting modes:

#### Option 1: Local Server (Same Machine)

1. Open the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`).
2. Run **`Copilot API: Start Server`** (or click the start button in the Copilot API sidebar/status bar).
3. The server starts locally at:
   ```
   http://127.0.0.1:3030
   ```

#### Option 2: Cloudflare Tunnel (Remote / Containerized Workflows)

If you run the DigitalHub Agent inside a Docker container, remote VM, or DigitalHub runtime pod that cannot directly reach `127.0.0.1`, you can enable the built-in **Cloudflare Tunnel** option provided by the extension:

1. In VS Code settings or Command Palette, enable **`Copilot API: Enable Cloudflare Tunnel`** (or check the Cloudflare Tunnel toggle in the extension settings).
2. The extension automatically provisions a secure, public HTTPS tunnel (e.g. `https://random-subdomain.trycloudflare.com`).
3. Copy the generated Cloudflare URL from the VS Code output channel.

### Step 4: Configure Environment Variables (`.env`)

Create your `.env` file from the template:

```bash
cp .env.example .env
```

#### For Local Server:

```ini
# --- DigitalHub Core Configuration ---
# NOTE: These 3 variables are NOT needed if you have logged in via the DigitalHub CLI (`dhcli login`),
# as credentials and endpoints are automatically read from the local dhcli configuration.
# DHCORE_ENDPOINT=https://your-digitalhub-core.example.com
# DHCORE_ISSUER=https://auth.example.com/oauth/v2/issuer
# DHCORE_PERSONAL_ACCESS_TOKEN=your-digitalhub-token

# --- LLM Endpoint (Local Copilot API) ---
DEPLOYED_URL=http://127.0.0.1:3030
LLM_MODEL=gpt-5-mini
LLM_API_KEY=dummy

# --- Optional LangSmith Tracing ---
LANGSMITH_API_KEY=
LANGCHAIN_PROJECT=digitalhub-agent
```

#### For Cloudflare Tunnel:

```ini
DEPLOYED_URL=https://your-tunnel-subdomain.trycloudflare.com
LLM_MODEL=gpt-5-mini
LLM_API_KEY=API_KEY
```

---

## Authentication Options for DigitalHub

DigitalHub supports multiple authentication and configuration mechanisms:

### 1. Automatic CLI Login (Recommended)

If you log in via the DigitalHub CLI (`dhcli login`), all credentials, endpoints, and active profile configurations are saved automatically to your local `dhcli` profile (`~/.digitalhub/config`).

When using CLI login:

- **`DHCORE_ENDPOINT`**, **`DHCORE_ISSUER`**, and **`DHCORE_PERSONAL_ACCESS_TOKEN`** are **NOT required** in your `.env` file.
- The DigitalHub SDK automatically detects and uses your active `dhcli` session.

For CLI installation and login instructions, refer to the [DigitalHub CLI Documentation](https://scc-digitalhub.github.io/docs/0.16/components/cli/#macos).

### 2. Manual Environment Variables

If not using the CLI, you can set credentials in `.env` or system environment variables:

- **Personal Access Token** (exchange flow via `DHCORE_PERSONAL_ACCESS_TOKEN`)
- **Access token + refresh token** (OAuth2)
- **Access token only** (bearer)
- **Basic auth** (username + password)

For full details on all authentication methods, see the [DHCore credentials documentation](https://scc-digitalhub.github.io/sdk-docs/reference/configuration/credentials/dhcore/).

---

## Running the Project

### Option A: Interactive CLI

Activate your virtual environment and start the conversational CLI:

```bash
source .venv/bin/activate
python main.py
```

Type your requests at the `User >` prompt. Type `exit` or `quit` to stop.

**Example prompts to try:**

- _"List all projects available in DigitalHub."_
- _"Register a tabular dataset called 'customer-data' from './data/customers.csv' in project 'analytics'."_
- _"Create a Python function named 'clean-data' that drops null values and logs the result."_
- _"What is the difference between log_dataitem and register_dataitem?"_

### Option B: LangGraph Studio (Visual Debugging)

To visually inspect execution traces, tool calls, and state graphs:

```bash
langgraph dev
```

This uses `langgraph.json` to launch the LangGraph Studio interface.

---

## Security Policy

The current release is the supported version. Security fixes are released together with all other fixes in each new release.

If you discover a security vulnerability in this project, please do not open a public issue.

Instead, report it privately by emailing us at [digitalhub@fbk.eu](mailto:digitalhub@fbk.eu). Include as much detail as possible to help us understand and address the issue quickly and responsibly.

---

## Contributing

To report a bug or request a feature, please first check the existing issues to avoid duplicates. If none exist, open a new issue with a clear title and a detailed description, including any steps to reproduce if it's a bug.

To contribute code, start by forking the repository. Clone your fork locally and create a new branch for your changes. Make sure your commits follow the [Conventional Commits v1.0](https://www.conventionalcommits.org/en/v1.0.0/) specification to keep history readable and consistent.

Once your changes are ready, push your branch to your fork and open a pull request against the main branch. Be sure to include a summary of what you changed and why. If your pull request addresses an issue, mention it in the description (e.g., "Closes #123").

Please note that new contributors may be asked to sign a Contributor License Agreement (CLA) before their pull requests can be merged. This helps us ensure compliance with open source licensing standards.

We appreciate contributions and help in improving the project!

---

## Authors

This project is developed and maintained by **DSLab – Fondazione Bruno Kessler**, with contributions from the open source community. A complete list of contributors is available in the project's commit history and pull requests.

For questions or inquiries, please contact: [digitalhub@fbk.eu](mailto:digitalhub@fbk.eu)

---

## Copyright and License

Copyright © 2026 DSLab – Fondazione Bruno Kessler and individual contributors.

This project is licensed under the Apache License, Version 2.0. You may not use this file except in compliance with the License. Ownership of contributions remains with the original authors and is governed by the terms of the Apache 2.0 License, including the requirement to grant a license to the project.
