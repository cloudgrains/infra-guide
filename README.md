# infra-guide 🚀

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-0.2.0-blue.svg)](https://github.com/iamtejas23/infra-guide)

**infra-guide** is a production-grade, interactive terminal UI (TUI) tool for Terraform and OpenTofu that combines beginner-friendly guidance with enterprise-level features. Learn infrastructure-as-code while using professional tools like drift detection, policy validation, and CI/CD integration.

## ✨ Features

### Core Features
- 🎯 **Auto-Detection**: Automatically detects whether you have Terraform or OpenTofu installed
- 📚 **Interactive Guides**: Detailed explanations for each command before execution
- 🎨 **Beautiful TUI**: Rich, colorful interface with a modern dark theme
- ⚡ **No Setup Required**: No cloud credentials, no network calls, no telemetry
- 🛡️ **Safety First**: Confirmation prompts and warnings before destructive operations
- 📖 **Beginner-Friendly**: Best practices and common flags explained clearly

### Enterprise Features (v0.2.0) 🆕
- 🔍 **Drift Detection**: Automatically detect when infrastructure has drifted from state
- ✅ **Pre-Flight Validation**: Comprehensive checks before executing commands
- 📦 **State Explorer**: Interactive browser for exploring state files with tree view
- 📁 **Workspace Manager**: Easy management of multiple environments
- 🚀 **CI/CD Mode**: Non-interactive pipeline mode for automation
- 📊 **Resource Visualization**: View resources by type with detailed statistics
- 🔄 **Smart Validation**: Syntax checking, format validation, and configuration analysis

## 🎬 Demo

```
🚀 infra-guide - Interactive Infrastructure Guide
📦 Using: terraform (v1.6.0)

┌──────────────────── Main Menu - Enhanced Edition ───────────────────┐
│ Option  Command      Description                                     │
│ 1       init         🔧 Initialize a working directory               │
│ 2       plan         📋 Show changes required                        │
│ 3       apply        ✅ Create or update infrastructure              │
│ 4       destroy      💥 Destroy infrastructure                       │
│ 5       validate     ✓ Run pre-flight validations                   │
│ 6       drift        🔍 Detect infrastructure drift                  │
│ 7       state        📦 Explore state file                           │
│ 8       workspace    📁 Manage workspaces                            │
│ 9       cicd         🚀 CI/CD pipeline mode                          │
│ 0       exit         🚪 Exit infra-guide                             │
└─────────────────────────────────────────────────────────┘

Select an option [1/2/3/4/5] (5):
```

## 📋 Prerequisites

Before installing infra-guide, ensure you have:

1. **Python 3.8 or higher**
   ```bash
   python3 --version
   ```

2. **Either Terraform OR OpenTofu** (at least one required)
   - **Terraform**: [Download and Install](https://www.terraform.io/downloads)
   - **OpenTofu**: [Download and Install](https://opentofu.org/docs/intro/install/)

That's it! No cloud credentials, API keys, or additional setup needed.

## 🚀 Installation

### Option 1: Install with pipx (Recommended)

```bash
# Install pipx if you don't have it
sudo apt update
sudo apt install pipx

# Install infra-guide
pipx install git+https://github.com/iamtejas23/infra-guide.git

# Run the tool
infra-guide
```

### Option 2: Install from Source

```bash
# Clone the repository
git clone https://github.com/iamtejas23/infra-guide.git
cd infra-guide

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install the package
pip install .
```

### Option 3: Install from PyPI (when published)

```bash
pipx install infra-guide
```

## 📖 Usage

Simply run the command from any directory containing Terraform/OpenTofu configuration files:

```bash
infra-guide
```

### Navigation

- Use number keys (1-5) to select menu options
- Follow the on-screen prompts
- Read the guides before executing commands
- Confirm when prompted before any command execution

### Example Workflow

**Basic Workflow:**
1. **Initialize your project** - Select option 1 (init)
2. **Validate configuration** - Select option 5 (validate) for pre-flight checks
3. **Preview changes** - Select option 2 (plan)
4. **Apply changes** - Select option 3 (apply)

**Advanced Workflow:**
1. **Check for drift** - Select option 6 (drift) to detect changes outside Terraform
2. **Explore state** - Select option 7 (state) to view current infrastructure
3. **Manage environments** - Select option 8 (workspace) to switch between dev/staging/prod
4. **Run CI/CD pipeline** - Select option 9 (cicd) for automated validation

## 🎯 Supported Commands

| Command | Description | Risk Level | New in v0.2.0 |
|---------|-------------|------------|---------------|
| `init` | Initialize working directory | 🟢 Low | |
| `plan` | Preview infrastructure changes | 🟢 Low | |
| `apply` | Create/update infrastructure | 🟡 Medium | |
| `destroy` | Delete all infrastructure | 🔴 High | |
| `validate` | Run pre-flight checks | 🟢 Low | ✅ |
| `drift` | Detect infrastructure drift | 🟢 Low | ✅ |
| `state` | Explore state file | 🟢 Low | ✅ |
| `workspace` | Manage workspaces | 🟡 Medium | ✅ |
| `cicd` | Run CI/CD pipeline | 🟡 Medium | ✅ |

## � Feature Deep Dive

### 🔍 Drift Detection
Automatically detects when your actual infrastructure has diverged from the state file. This happens when changes are made outside of Terraform/OpenTofu (manual changes, other tools, etc.).

```bash
# In infra-guide, select option 6
# Shows which resources have drifted and what changed
```

### ✅ Pre-Flight Validation
Runs comprehensive checks before you execute commands:
- Configuration file existence
- Initialization status
- Syntax validation
- Code formatting
- Backend configuration
- Provider version locks
- Required variables

### 📦 State Explorer
Interactive browser for your state file:
- **Overview**: Total resources and types
- **Resource List**: All resources with addresses
- **Tree View**: Hierarchical visualization by resource type

### 📁 Workspace Manager
Easily manage multiple environments:
- List all workspaces
- Switch between workspaces
- Create new workspaces
- Delete unused workspaces
- Visual indication of current workspace

### 🚀 CI/CD Pipeline Mode
Non-interactive mode perfect for automation:
- Runs init → validate → plan automatically
- Uses detailed exit codes
- No user prompts
- Designed for continuous integration

## �🔒 Security & Privacy

- **No Telemetry**: We don't collect any data
- **No Network Calls**: Works completely offline
- **No Credentials Required**: Only wraps Terraform/OpenTofu CLI
- **Open Source**: Fully transparent, auditable code
- **Local Execution**: All commands run locally on your machine

## 🛠️ Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/iamtejas23/infra-guide.git
cd infra-guide

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black infra_guide/
```

### Type Checking

```bash
mypy infra_guide/
```

## 📁 Project Structure

```
infra-guide/
├── infra_guide/
│   ├── __init__.py          # Package initialization
│   ├── cli.py               # Main CLI entry point
│   ├── detector.py          # Tool detection logic
│   ├── ui.py                # UI components using rich
│   ├── runner.py            # Command execution
│   └── guides/
│       ├── __init__.py
│       ├── init.py          # Init command guide
│       ├── plan.py          # Plan command guide
│       ├── apply.py         # Apply command guide
│       └── destroy.py       # Destroy command guide
├── pyproject.toml           # Project configuration
├── README.md                # This file
└── LICENSE                  # MIT License
```

## 🗺️ Roadmap

### Completed ✅
- [x] Core IaC commands (init, plan, apply, destroy)
- [x] Drift detection
- [x] Pre-flight validations
- [x] State explorer with tree visualization
- [x] Workspace management
- [x] CI/CD pipeline mode
- [x] Comprehensive error handling

### Coming Soon
- [ ] Policy-as-code integration (OPA, Sentinel)
- [ ] Cost estimation before apply
- [ ] Graph visualization of resource dependencies
- [ ] Plan diff with syntax highlighting
- [ ] Custom command templates
- [ ] Configuration file for user preferences
- [ ] Color theme customization
- [ ] Command history and favorites
- [ ] Export reports to markdown/PDF
- [ ] Integration with popular CI/CD platforms
- [ ] Multi-language support
- [ ] Cloud provider-specific guidance
- [ ] Terraform/OpenTofu module browser

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and formatting
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Rich](https://github.com/Textualize/rich) for beautiful terminal output
- Inspired by the need to make Infrastructure as Code more accessible to beginners
- Thanks to the Terraform and OpenTofu communities

## 📞 Support

- 📫 **Issues**: [GitHub Issues](https://github.com/iamtejas23/infra-guide/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/iamtejas23/infra-guide/discussions)
- 📖 **Documentation**: [GitHub Wiki](https://github.com/iamtejas23/infra-guide/wiki)

## ⭐ Star History

If you find this project useful, please consider giving it a star on GitHub!

---

**Made with ❤️ for the Infrastructure as Code community**
