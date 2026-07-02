# infra-guide

<p align="center">
  <img src="https://raw.githubusercontent.com/iamtejas23/infra-guide/main/img/infra-guide.png" alt="infra-guide logo" width="360">
</p>

<p align="center">
  <a href="https://pypi.org/project/infra-guide/"><img src="https://img.shields.io/pypi/v/infra-guide?color=blue&label=PyPI" alt="PyPI version"></a>
  <a href="https://pypi.org/project/infra-guide/"><img src="https://img.shields.io/pypi/dm/infra-guide?color=blue&label=downloads" alt="PyPI downloads"></a>
  <a href="https://github.com/iamtejas23/infra-guide/actions/workflows/publish.yml"><img src="https://github.com/iamtejas23/infra-guide/actions/workflows/publish.yml/badge.svg" alt="CI"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python 3.8+"></a>
</p>

A product-grade CLI and interactive command center for Terraform and OpenTofu. Blends guide-first workflows, direct subcommands, workspace diagnostics, policy checks, and automation-friendly commands — so the tool works equally well for learning and day-to-day operations.

## Features

- **Interactive TUI dashboard** — themed readiness panel, workspace info, recent commands, and favorites
- **Direct CLI subcommands** — `init`, `plan`, `apply`, `destroy`, `fmt`, `state`, `workspace`, `cicd`, `output`, `policy`, and more
- **Doctor mode** — workspace health checks with actionable recommendations and optional drift detection
- **Policy checks** — built-in security policy engine (no-public-S3, open security groups, missing tags, encryption, versioning)
- **Web command center** — launch a local browser UI (`infra-guide web`) powered by the same backend as the TUI
- **Themes** — `aurora` (default), `sunset`, `forest`, `mono`, `neon` — persisted across sessions
- **Shell completion** — one-line setup for bash, zsh, and fish
- **Update notifications** — background PyPI check after each command, cached for 24 h
- **Cost insight** — analyzes saved plan JSON for AWS cost-impact hints before `apply`
- **Command history and favorites** — rerun support inside the TUI
- **Local-only** — no telemetry, no credential handling, no cloud calls beyond what your IaC tool makes

## Installation

```bash
pip install infra-guide
# or
pipx install infra-guide
```

## Quick start

```bash
# interactive mode
infra-guide

# direct CLI
infra-guide doctor
infra-guide plan --out tfplan
infra-guide apply --plan-file tfplan --yes
```

## Shell completion

```bash
# bash — add to ~/.bashrc
eval "$(infra-guide completion bash)"

# zsh — add to ~/.zshrc
eval "$(infra-guide completion zsh)"

# fish — add to ~/.config/fish/config.fish
infra-guide completion fish | source
```

## Commands

| Command | Description | Risk |
| --- | --- | --- |
| `status` | Fast workspace summary | Low |
| `doctor [--with-drift]` | Health diagnostics and recommendations | Low |
| `guide <command>` | Best practices for init, plan, apply, destroy | Low |
| `history [--favorites] [--clear]` | Recent commands and favorites | Low |
| `theme [--list] [--set NAME]` | Show or change the active theme | Low |
| `web [--port N] [--no-browser]` | Launch local browser command center | Low |
| `validate` | Pre-flight validation checks | Low |
| `drift` | Detect infrastructure drift | Low |
| `state [--list\|--tree\|--detail ADDR]` | Explore state resources | Low |
| `output [NAME] [--json\|--raw]` | Show infrastructure output values | Low |
| `policy [--plan-file PATH]` | Check plan against built-in security policies | Low |
| `init [--upgrade] [--reconfigure]` | Initialize providers, modules, backend | Low |
| `plan [--out PATH] [--detailed-exitcode]` | Preview changes | Low |
| `apply [--plan-file PATH] [--yes]` | Apply changes with cost insight | Medium |
| `destroy [--yes]` | Delete managed infrastructure | High |
| `workspace [--list\|--select\|--create\|--delete]` | Manage workspaces | Medium |
| `fmt [--check] [--diff]` | Format HCL files | Low |
| `cicd [--skip-init] [--skip-validation]` | Pipeline-friendly init/validate/plan flow | Medium |
| `completion <bash\|zsh\|fish>` | Output shell completion script | Low |

## Usage examples

### Doctor and status

```bash
infra-guide status                # fast workspace panel
infra-guide doctor                # full health check
infra-guide doctor --with-drift   # health check + drift detection
```

### Plan, apply, and destroy

```bash
infra-guide plan --out tfplan
infra-guide apply --plan-file tfplan --yes
infra-guide destroy --yes

# pass raw flags through to the IaC tool after --
infra-guide plan -- --target=module.network
infra-guide init -- --backend-config=env/dev.backend.hcl
```

### Policy as code

```bash
# check the current directory against built-in security policies
infra-guide policy

# check a saved plan JSON
infra-guide plan --out tfplan.json
infra-guide policy --plan-file tfplan.json
```

Policies included out of the box:

| ID | Description | Severity |
| --- | --- | --- |
| `no-public-s3` | S3 buckets must not have a public ACL | High |
| `no-public-ingress` | Security groups must not allow 0.0.0.0/0 ingress | Critical |
| `require-tags` | Resources must have `Environment` and `Owner` tags | Medium |
| `require-encryption` | AWS resources should have encryption enabled | High |
| `require-versioning` | S3 buckets should have versioning enabled | Medium |
| `no-default-vpc` | Resources should not reference the default VPC | Low |

### Themes

```bash
infra-guide theme --list
infra-guide theme --set neon      # aurora | sunset | forest | mono | neon
```

### Output values

```bash
infra-guide output                 # all outputs
infra-guide output bucket_name     # single output
infra-guide output --json          # raw JSON
```

### State exploration

```bash
infra-guide state                  # overview
infra-guide state --list           # flat list
infra-guide state --tree           # grouped tree view
infra-guide state --detail aws_instance.web
```

### Web command center

```bash
infra-guide web               # opens http://localhost:8765
infra-guide web --port 9000
infra-guide web --no-browser  # server only
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

## Suggested workflow

```bash
infra-guide doctor               # 1. understand workspace health
infra-guide init                 # 2. initialize if needed
infra-guide plan --out tfplan    # 3. preview and save
infra-guide policy               # 4. check against security policies
infra-guide apply --plan-file tfplan --yes  # 5. apply
```

## Security and privacy

- No telemetry
- No credential handling inside infra-guide
- Network calls: only the background PyPI version check (cached 24 h, skipped on `--no-color`)
- Open source and auditable

## Development

```bash
git clone https://github.com/iamtejas23/infra-guide.git
cd infra-guide
python3 -m venv venv && source venv/bin/activate
pip install -e ".[dev]"
pytest
black infra_guide/
flake8 infra_guide/ --max-line-length=100
```

## Project structure

```text
infra-guide/
├── infra_guide/
│   ├── cli.py               # entry point and argument parser
│   ├── ui.py                # Rich-based TUI
│   ├── runner.py            # subprocess wrapper
│   ├── detector.py          # tool detection (tofu / terraform)
│   ├── project_inspector.py # workspace metadata
│   ├── validators.py        # pre-flight checks
│   ├── drift_detector.py    # drift detection
│   ├── state_explorer.py    # state file browser
│   ├── workspace_manager.py # workspace CRUD
│   ├── policy_checker.py    # built-in policy engine
│   ├── cost_estimator.py    # plan cost analysis
│   ├── cicd.py              # CI/CD pipeline runner
│   ├── completion.py        # shell completion scripts
│   ├── update_checker.py    # background PyPI version check
│   ├── preferences.py       # theme and history persistence
│   ├── web.py               # browser command center
│   └── guides/              # command guide modules
├── tests/
├── pyproject.toml
└── README.md
```

## License

MIT — see [LICENSE](LICENSE).
