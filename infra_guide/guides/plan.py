"""
Guide for the 'plan' command.
"""


def get_guide() -> dict:
    """
    Returns guide information for the plan command.
    
    Returns:
        dict: Guide data with description, flags, best practices, and warnings
    """
    return {
        "risk": "low",
        "description": (
            "The 'plan' command creates an execution plan, showing what actions would be taken "
            "to reach the desired state defined in your configuration files. It compares the "
            "current state with the desired state and shows you what will be created, updated, "
            "or destroyed. This is a read-only operation that doesn't modify any infrastructure - "
            "it's a safe way to preview changes before applying them."
        ),
        "flags": [
            {
                "flag": "-out=path",
                "description": "Save the plan to a file for later execution with 'apply'"
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
                "description": "Focus planning on specific resources (use sparingly)"
            },
            {
                "flag": "-destroy",
                "description": "Create a plan to destroy all resources"
            },
            {
                "flag": "-refresh=false",
                "description": "Skip refreshing state before planning"
            },
            {
                "flag": "-detailed-exitcode",
                "description": "Return detailed exit code (2 if changes, 0 if no changes)"
            }
        ],
        "examples": [
            "infra-guide plan",
            "infra-guide plan --out tfplan",
            "infra-guide plan -- --target=module.network",
        ],
        "best_practices": [
            "Always run 'plan' before 'apply' to understand what changes will be made",
            "Review the plan output carefully, especially the resources being destroyed",
            "Save important plans with '-out' flag for exact reproducibility",
            "Use 'plan' in CI/CD pipelines to validate configurations",
            "Pay attention to the resource count summary at the end (create, update, destroy)",
            "For production changes, have a peer review the plan output"
        ],
        "warnings": [
            "Plan output may contain sensitive data - be careful when sharing logs",
            "A successful plan doesn't guarantee apply will succeed (network issues, permissions, etc.)",
            "The actual state may change between 'plan' and 'apply' if others are making changes",
            "Some providers may have side effects even during plan (though this is rare)",
            "Avoid using -target in production as it can lead to inconsistent infrastructure"
        ]
    }
