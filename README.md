# infra-guide 🚀

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

**infra-guide** is an interactive, colorful terminal UI (TUI) tool designed to help Terraform and OpenTofu beginners learn and execute infrastructure-as-code commands with confidence. It provides helpful guides, best practices, and warnings before executing any command.

## ✨ Features

- 🎯 **Auto-Detection**: Automatically detects whether you have Terraform or OpenTofu installed
- 📚 **Interactive Guides**: Detailed explanations for each command before execution
- 🎨 **Beautiful TUI**: Rich, colorful interface with a modern dark theme
- ⚡ **No Setup Required**: No cloud credentials, no network calls, no telemetry
- 🛡️ **Safety First**: Confirmation prompts and warnings before destructive operations
- 📖 **Beginner-Friendly**: Best practices and common flags explained clearly
- 🔄 **Command Support**: init, plan, apply, destroy with detailed guidance

## 🎬 Demo

```
🚀 infra-guide - Interactive Infrastructure Guide
📦 Using: terraform (v1.6.0)

┌─────────────────────── Main Menu ───────────────────────┐
│ Option  Command      Description                         │
│ 1       init         🔧 Initialize a working directory   │
│ 2       plan         📋 Show changes required            │
│ 3       apply        ✅ Create or update infrastructure  │
│ 4       destroy      💥 Destroy infrastructure           │
│ 5       exit         🚪 Exit infra-guide                 │
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

1. **Initialize your project**
   ```
   Select option 1 (init)
   Review the guide
   Confirm execution
   ```

2. **Preview changes**
   ```
   Select option 2 (plan)
   Review the guide and understand what will change
   Confirm execution
   ```

3. **Apply changes**
   ```
   Select option 3 (apply)
   Read warnings carefully
   Confirm execution
   ```

## 🎯 Supported Commands

| Command | Description | Risk Level |
|---------|-------------|------------|
| `init` | Initialize working directory | 🟢 Low |
| `plan` | Preview infrastructure changes | 🟢 Low |
| `apply` | Create/update infrastructure | 🟡 Medium |
| `destroy` | Delete all infrastructure | 🔴 High |

## 🔒 Security & Privacy

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

- [ ] Add support for workspace management
- [ ] Include `terraform validate` and `terraform fmt` commands
- [ ] Add interactive flag selection for commands
- [ ] Support for custom command templates
- [ ] Configuration file for user preferences
- [ ] Color theme customization
- [ ] Command history and favorites
- [ ] Export command explanations to markdown
- [ ] Integration with popular CI/CD platforms
- [ ] Multi-language support

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
