"""
Guide for the 'init' command.
"""


def get_guide() -> dict:
    """
    Returns guide information for the init command.
    
    Returns:
        dict: Guide data with description, flags, best practices, and warnings
    """
    return {
        "description": (
            "The 'init' command initializes a working directory containing Terraform/OpenTofu "
            "configuration files. This is the first command that should be run after writing a "
            "new configuration or cloning an existing one from version control. It downloads and "
            "installs provider plugins, initializes the backend, and prepares the working directory "
            "for use."
        ),
        "flags": [
            {
                "flag": "-upgrade",
                "description": "Upgrade modules and plugins to the latest acceptable versions"
            },
            {
                "flag": "-reconfigure",
                "description": "Reconfigure backend, ignoring any saved configuration"
            },
            {
                "flag": "-migrate-state",
                "description": "Reconfigure backend and attempt to migrate state"
            },
            {
                "flag": "-backend-config=path",
                "description": "Path to a backend configuration file"
            },
            {
                "flag": "-get=false",
                "description": "Disable downloading modules"
            },
            {
                "flag": "-lock=false",
                "description": "Don't hold a state lock during backend migration"
            }
        ],
        "best_practices": [
            "Always run 'init' when you first clone a repository or after adding new provider requirements",
            "Run 'init -upgrade' when you want to update provider versions to the latest compatible versions",
            "Commit the '.terraform.lock.hcl' file to version control to ensure consistent provider versions across your team",
            "Do not commit the '.terraform' directory to version control - add it to .gitignore",
            "If working in a team, coordinate before running 'init -upgrade' to avoid unexpected changes"
        ],
        "warnings": [
            "The init command may modify the .terraform.lock.hcl file",
            "Running with -upgrade may change provider versions and potentially break configurations",
            "The .terraform directory can become large - ensure it's in your .gitignore",
            "Backend reconfiguration can affect state storage - be careful with production environments"
        ]
    }
