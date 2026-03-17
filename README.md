# infra-guide

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-0.3.0-blue.svg)](https://github.com/iamtejas23/infra-guide)

`infra-guide` is a product-style CLI and interactive command center for Terraform and OpenTofu. It blends guide-first workflows, direct subcommands, workspace diagnostics, and automation-friendly commands so the tool works for both learning and day-to-day operations.

## Features

- Real CLI surface with working `--help`, subcommands, and passthrough args
- Interactive dashboard with readiness, backend, lock file, workspace, and state signals
- `doctor` mode for project health checks and actionable recommendations
- Guide mode for `init`, `plan`, `apply`, and `destroy`
- Direct support for `init`, `plan`, `apply`, `destroy`, `fmt`, `state`, `workspace`, and `cicd`
- Drift detection, validation, state exploration, and workspace management
- Local-only execution with no telemetry and no cloud credentials required

## Demo

```text
infra-guide  Command Center  v0.3.0
Tool: tofu (OpenTofu v1.11.5)
Workspace: default
Directory: ./envs/dev

Environment      Project Signals     Next Step
Workspace: dev   Config files: 8     Ready to operate
Readiness: READY Backend: YES        Recommended flow:
                 Lock file: YES      doctor -> plan -> apply

Command Palette
1  doctor     Workspace health check with guidance   LOW
2  init       Initialize providers and backend       LOW
3  plan       Preview infrastructure changes         LOW
4  apply      Apply changes to infrastructure        MEDIUM
5  destroy    Remove managed infrastructure          HIGH
```

## Installation

### pipx

```bash
pipx install infra-guide
infra-guide --help
```

### From source

```bash
git clone https://github.com/iamtejas23/infra-guide.git
cd infra-guide
python3 -m venv venv
source venv/bin/activate
pip install .
infra-guide
```

## Usage

### Interactive mode

```bash
infra-guide
```

### Direct CLI mode

```bash
infra-guide status
infra-guide doctor --with-drift
infra-guide guide plan
infra-guide init --upgrade
infra-guide plan --out tfplan
infra-guide apply --plan-file tfplan --yes
infra-guide workspace --select staging
infra-guide fmt --check
```

### Passing through raw flags

```bash
infra-guide plan -- --target=module.network
infra-guide init -- --backend-config=env/dev.backend.hcl
infra-guide destroy -- --target=aws_instance.temporary
```

## Suggested workflow

1. Run `infra-guide doctor` to understand workspace readiness.
2. Run `infra-guide init` if the directory has not been initialized.
3. Run `infra-guide plan --out tfplan` to preview and save changes.
4. Run `infra-guide apply --plan-file tfplan --yes` when ready to execute.

## Commands

| Command | Description | Risk |
| --- | --- | --- |
| `status` | Show a fast workspace summary | Low |
| `doctor` | Run health diagnostics and recommendations | Low |
| `guide <command>` | Show best practices and examples for a command | Low |
| `init` | Initialize providers, modules, and backend | Low |
| `plan` | Preview infrastructure changes | Low |
| `apply` | Create or update infrastructure | Medium |
| `destroy` | Delete managed infrastructure | High |
| `validate` | Run pre-flight checks | Low |
| `drift` | Detect infrastructure drift | Low |
| `state` | Show state overview, list, tree, or resource detail | Low |
| `workspace` | List, create, select, or delete workspaces | Medium |
| `fmt` | Format Terraform/OpenTofu files | Low |
| `cicd` | Run a pipeline-friendly init/validate/plan flow | Medium |

## Feature notes

### Doctor and status

```bash
infra-guide status
infra-guide doctor
infra-guide doctor --with-drift
```

`status` is lightweight. `doctor` adds validation and exits non-zero when critical checks fail.

### State explorer

```bash
infra-guide state
infra-guide state --list
infra-guide state --tree
infra-guide state --detail aws_instance.web
```

### Workspace management

```bash
infra-guide workspace --list
infra-guide workspace --create dev
infra-guide workspace --select prod
infra-guide workspace --delete staging
```

### CI/CD mode

```bash
infra-guide cicd
infra-guide cicd --skip-init
infra-guide cicd --skip-validation
```

## Security and privacy

- No telemetry
- No network calls beyond your Terraform/OpenTofu usage
- No credential handling inside infra-guide
- Local execution only
- Open source and auditable

## Development

```bash
git clone https://github.com/iamtejas23/infra-guide.git
cd infra-guide
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
pytest
black infra_guide/
mypy infra_guide/
```

## Project structure

```text
infra-guide/
├── infra_guide/
│   ├── cli.py
│   ├── project_inspector.py
│   ├── runner.py
│   ├── ui.py
│   ├── validators.py
│   ├── drift_detector.py
│   ├── state_explorer.py
│   ├── workspace_manager.py
│   ├── cicd.py
│   └── guides/
├── pyproject.toml
└── README.md
```
