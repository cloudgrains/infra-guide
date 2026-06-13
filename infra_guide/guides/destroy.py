"""
Guide for the 'destroy' command.
"""


def get_guide() -> dict:
    """
    Returns guide information for the destroy command.

    Returns:
        dict: Guide data with description, flags, best practices, and warnings
    """
    return {
        "risk": "high",
        "description": (
            "The 'destroy' command terminates and removes all resources managed by your "
            "configuration. It's the opposite of 'apply' - instead of creating or updating "
            "infrastructure, it tears everything down. This is a DESTRUCTIVE operation that "
            "cannot be easily undone. Use with extreme caution, especially in production "
            "environments."
        ),
        "flags": [
            {
                "flag": "-auto-approve",
                "description": "Skip interactive approval (EXTREMELY DANGEROUS!)",
            },
            {"flag": "-target=resource", "description": "Destroy only specific resources"},
            {"flag": "-var 'key=value'", "description": "Set a variable in the configuration"},
            {"flag": "-var-file=path", "description": "Load variable values from a file"},
            {
                "flag": "-parallelism=n",
                "description": "Limit concurrent resource deletions (default: 10)",
            },
            {"flag": "-refresh=false", "description": "Skip refreshing state before destroying"},
            {
                "flag": "-lock=false",
                "description": "Don't lock state during operation (not recommended)",
            },
        ],
        "examples": [
            "infra-guide destroy",
            "infra-guide destroy --yes",
            "infra-guide destroy -- --target=aws_instance.temporary",
        ],
        "best_practices": [
            "ALWAYS run 'plan -destroy' first to see what will be deleted",
            "Triple-check you're in the correct directory and workspace",
            "Back up state files and any data before destroying",
            "Export or snapshot any critical data from databases/storage before destroying",
            "Use '-target' to destroy specific resources if you don't want to destroy everything",
            "Consider using lifecycle prevention rules for critical resources",
            "Verify with team members before destroying shared infrastructure",
            "Document the reason for destruction",
            "In production, require multi-person approval before destroying",
        ],
        "warnings": [
            "🔥 EXTREME DANGER: THIS COMMAND DELETES ALL YOUR INFRASTRUCTURE!",
            "💀 DATA LOSS: Databases, storage, and all data will be PERMANENTLY DELETED!",
            "⚠️  No undo: Destroyed resources cannot be easily recovered",
            "💰 Orphaned resources: Some resources may not be deleted if state is out of sync",
            "⏰ Time consuming: Large infrastructures can take significant time to destroy",
            "🔐 Compliance risk: Ensure you have approval to delete resources",
            "🌐 Dependencies: External systems may break if they depend on these resources",
            "💸 Cost implications: While destroying saves costs, snapshots/backups may still incur charges",
            "NEVER use -auto-approve for destroy in production!",
        ],
    }
