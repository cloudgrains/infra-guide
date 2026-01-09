"""
Guide for the 'apply' command.
"""


def get_guide() -> dict:
    """
    Returns guide information for the apply command.
    
    Returns:
        dict: Guide data with description, flags, best practices, and warnings
    """
    return {
        "description": (
            "The 'apply' command executes the actions proposed in a plan to reach the desired "
            "state of your infrastructure. It will create, update, or delete resources as needed "
            "to match your configuration. This command modifies real infrastructure, so it should "
            "be used with caution. By default, it shows you the plan and asks for confirmation "
            "before proceeding."
        ),
        "flags": [
            {
                "flag": "-auto-approve",
                "description": "Skip interactive approval (dangerous - use with caution!)"
            },
            {
                "flag": "path/to/planfile",
                "description": "Apply a previously saved plan file"
            },
            {
                "flag": "-var 'key=value'",
                "description": "Set a variable in the configuration"
            },
            {
                "flag": "-var-file=path",
                "description": "Load variable values from a file"
            },
            {
                "flag": "-target=resource",
                "description": "Apply changes only to specific resources (use sparingly)"
            },
            {
                "flag": "-parallelism=n",
                "description": "Limit concurrent resource operations (default: 10)"
            },
            {
                "flag": "-lock=false",
                "description": "Don't lock state during operation (not recommended)"
            }
        ],
        "best_practices": [
            "Always run 'plan' first and review the output before running 'apply'",
            "Never use '-auto-approve' in production without proper safeguards",
            "Use saved plan files (from 'plan -out') for critical production changes",
            "Enable backend state locking to prevent concurrent modifications",
            "Keep backups of state files before major changes",
            "Test changes in a development/staging environment first",
            "Use version control for all configuration files",
            "Document why changes are being made (commit messages, tickets, etc.)"
        ],
        "warnings": [
            "⚠️  THIS COMMAND MODIFIES REAL INFRASTRUCTURE - DOUBLE CHECK BEFORE PROCEEDING!",
            "Resources may be DESTROYED and recreated if certain attributes change",
            "Some changes cannot be reversed (like deleting databases without backups)",
            "Cost implications: New resources may incur charges",
            "Downtime risk: Some updates require resource replacement",
            "State file will be modified - ensure it's properly backed up",
            "Failed applies may leave infrastructure in an incomplete state",
            "-auto-approve bypasses all safety checks - use only in trusted automation"
        ]
    }
