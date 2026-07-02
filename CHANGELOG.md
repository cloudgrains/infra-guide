# Changelog

All notable changes to infra-guide are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

### Added
- `completion` subcommand — outputs shell completion scripts for bash, zsh, and fish
- Background PyPI update checker with 24-hour XDG-cache TTL; shows upgrade banner after each CLI command when a newer version is available
- Policy-as-code engine (`infra_guide/policy_checker.py`) with six built-in rules: `no-public-s3`, `no-public-ingress`, `require-tags`, `require-encryption`, `require-versioning`, `no-default-vpc`
- `policy` CLI subcommand and TUI menu entry (item 16) — check current directory or a saved plan JSON
- `output` CLI subcommand and TUI menu entry (item 15) — display infrastructure output values with `--json` and `--raw` options
- `neon` theme — electric purple and hot-pink accents for a retro-futuristic vibe
- Rotating tips in the dashboard bottom panel cycling by minute
- Relative timestamps and colour-coded exit codes in the history panel
- Improved goodbye screen using `box.DOUBLE` with brand colour, version, and GitHub link
- Comprehensive test suite: 73 tests across validators, project inspector, tool detector, policy checker, command runner, state explorer, preferences, cost estimator, web backend, and CLI

### Fixed
- `state_explorer.py` — resource type extraction now uses `split('.')[-2]` so module paths like `module.network.aws_vpc.main` return `aws_vpc` instead of `module`
- `cost_estimator.py` — removed duplicate `aws_eks_` entry from `HIGH_IMPACT_PREFIXES`
- `validators.py` — file opened with `encoding="utf-8", errors="ignore"` to avoid crashes on non-UTF-8 HCL; removed unused `List` import
- `cicd.py` — added `timeout=30` to subprocess call in `validate_pipeline()`; removed unused `json` import; removed f-prefix from Rich markup strings with no interpolation (`F541`)
- `cli.py` — removed dead-code fallback branch in `main()` that was always shadowed by the command list

### Changed
- Dashboard bottom panel shows rotating tips instead of static placeholder text
- History panel uses relative time strings ("5m ago", "2h ago") and green/red exit code chips

---

## [0.8.0] — 2026-06-30

### Added
- OIDC Trusted Publishing on PyPI — `publish.yml` now uses `pypa/gh-action-pypi-publish` with `id-token: write` permission; no API token required
- Lint gate in CI — `black --check` and `flake8` must pass before the build-and-publish job runs
- Tag-to-version verification step in `publish.yml` — pipeline aborts if the git tag does not match `pyproject.toml` version
- `packaging` dependency added to dev extras for the version verification script

### Changed
- `publish.yml` — `on: push: tags` pattern updated to `v*.*.*`
- Python version pinned to 3.12 in CI

---

## [0.7.0] — 2026-06-28

### Added
- Web command center (`infra-guide web`) — local browser UI with workspace dashboard, command execution, history, favorites, and state explorer data
- `CostEstimator` — analyzes saved plan JSON for AWS cost-impact hints before `apply`
- `workspace` subcommand — list, create, select, and delete Terraform/OpenTofu workspaces
- `cicd` subcommand — pipeline-friendly init → validate → plan flow
- `fmt` subcommand — format HCL files with `--check` and `--diff` options
- `state` subcommand — state overview, flat list, tree view, and per-resource detail
- `drift` subcommand — infrastructure drift detection
- `validate` subcommand — pre-flight validation checks
- `output` subcommand — show infrastructure output values
- Passthrough args (`--`) forwarding to the IaC tool

### Changed
- `doctor` health check expanded to 7 checks covering configuration files, initialization, syntax, formatting, backend config, provider versions, and state presence

---

## [0.6.0] — 2026-06-15

### Added
- Initial public release
- Interactive TUI dashboard with project readiness panel, backend and lock-file status, workspace indicator, recent commands, and favorites
- `doctor` subcommand with health checks and actionable recommendations
- `guide` subcommand for `init`, `plan`, `apply`, and `destroy`
- `history` subcommand with `--favorites` and `--clear` flags
- `theme` subcommand with `aurora`, `sunset`, `forest`, and `mono` themes
- `status` subcommand — fast workspace summary without running the IaC tool
- Direct `init`, `plan`, `apply`, and `destroy` subcommands with full flag support
- XDG Base Directory spec compliance for preferences and cache files
- `PreferencesStore` — persists theme, history, and favorites to `~/.config/infra-guide/preferences.json`
- `ProjectInspector` — collects workspace metadata (tf files, modules, backend, lock, state)
- `ToolDetector` — auto-detects tofu or terraform; prefers OpenTofu when both are installed
