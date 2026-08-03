# DigitalHub Agent

[![license](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)
![Status](https://img.shields.io/badge/status-experimental-orange)

The DigitalHub Agent is a LangGraph-based conversational agent for managing ML and data engineering workflows on [DigitalHub CORE](https://github.com/scc-digitalhub/digitalhub-core). It exposes DigitalHub SDK operations as LLM-callable tools and supports both an interactive CLI and LangGraph Studio.

Explore the full platform documentation at the [link](https://scc-digitalhub.github.io/docs/).

## Quick start

The Agent is meant to be used alongside a running DigitalHub CORE instance. You will also need access to an OpenAI-compatible LLM endpoint.

## Configuration

The Agent is configured via environment variables. Copy the template and fill in your values:

```bash
cp .env.example .env
```

### Parameters

The following environment variables are supported:

| KEY                            | DESCRIPTION                                               |
| ------------------------------ | --------------------------------------------------------- |
| `DHCORE_ENDPOINT`              | DigitalHub Core API URL                                   |
| `DHCORE_ISSUER`                | Authentication issuer URL                                 |
| `DHCORE_PERSONAL_ACCESS_TOKEN` | Personal access token for DigitalHub                      |
| `DEPLOYED_URL`                 | Base URL of the LLM endpoint                              |
| `LLM_MODEL`                    | Model name (e.g. `meta-llama/Meta-Llama-3.1-8B-Instruct`) |
| `LLM_API_KEY`                  | API key for the LLM endpoint                              |
| `LANGSMITH_API_KEY`            | _(optional)_ LangSmith API key for tracing                |
| `LANGCHAIN_PROJECT`            | _(optional)_ LangSmith project name                       |

### Authentication

The `.env.example` uses a personal access token (`DHCORE_PERSONAL_ACCESS_TOKEN`), but the SDK supports multiple authentication methods:

- **Personal Access Token** (exchange flow)
- **Access token + refresh token** (OAuth2)
- **Access token only** (bearer)
- **Basic auth** (username + password)

The SDK automatically selects the appropriate auth flow based on available credentials. For full details on all methods and configuration options, see the [DHCore credentials documentation](https://scc-digitalhub.github.io/sdk-docs/reference/configuration/credentials/dhcore/).

## Development

The Agent code is written in Python and structured as follows:

```
├── agent.py            # Agent factory (LLM + tools + middleware)
├── graph.py            # LangGraph entry point
├── main.py             # CLI runner
├── prompts.py          # System prompt
├── settings.py         # Environment variable loading
├── tools/
│   ├── project_tools.py    # DigitalHub project management tools
│   └── dataitem_tools.py   # DigitalHub dataitem management tools
├── langgraph.json      # LangGraph configuration
├── requirements.txt    # Python dependencies
└── .env.example        # Environment variable template
```

### Build from source

Running the Agent requires:

- Python 3.10 or higher
- pip

In order to build and run the Agent, you first need to clone this repository and install its dependencies:

```bash
git clone https://github.com/scc-digitalhub/digitalhub-agent.git
cd digitalhub-agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Running the CLI

```bash
python main.py
```

Type your commands at the `User >` prompt. Type `exit` or `quit` to stop.

### Running with LangGraph Studio

```bash
langgraph dev
```

This uses `langgraph.json` to expose the agent graph for visual debugging.

## Security Policy

The current release is the supported version. Security fixes are released together with all other fixes in each new release.

If you discover a security vulnerability in this project, please do not open a public issue.

Instead, report it privately by emailing us at digitalhub@fbk.eu. Include as much detail as possible to help us understand and address the issue quickly and responsibly.

## Contributing

To report a bug or request a feature, please first check the existing issues to avoid duplicates. If none exist, open a new issue with a clear title and a detailed description, including any steps to reproduce if it's a bug.

To contribute code, start by forking the repository. Clone your fork locally and create a new branch for your changes. Make sure your commits follow the [Conventional Commits v1.0](https://www.conventionalcommits.org/en/v1.0.0/) specification to keep history readable and consistent.

Once your changes are ready, push your branch to your fork and open a pull request against the main branch. Be sure to include a summary of what you changed and why. If your pull request addresses an issue, mention it in the description (e.g., "Closes #123").

Please note that new contributors may be asked to sign a Contributor License Agreement (CLA) before their pull requests can be merged. This helps us ensure compliance with open source licensing standards.

We appreciate contributions and help in improving the project!

## Authors

This project is developed and maintained by **DSLab – Fondazione Bruno Kessler**, with contributions from the open source community. A complete list of contributors is available in the project's commit history and pull requests.

For questions or inquiries, please contact: [digitalhub@fbk.eu](mailto:digitalhub@fbk.eu)

## Copyright and license

Copyright © 2026 DSLab – Fondazione Bruno Kessler and individual contributors.

This project is licensed under the Apache License, Version 2.0. You may not use this file except in compliance with the License. Ownership of contributions remains with the original authors and is governed by the terms of the Apache 2.0 License, including the requirement to grant a license to the project.
