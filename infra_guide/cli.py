"""
Main CLI entry point for infra-guide.
"""

import sys
from infra_guide.detector import ToolDetector
from infra_guide.ui import InfraGuideUI
from infra_guide.runner import CommandRunner
from infra_guide.drift_detector import DriftDetector
from infra_guide.state_explorer import StateExplorer
from infra_guide.workspace_manager import WorkspaceManager
from infra_guide.validators import PreFlightValidator
from infra_guide.cicd import CICDRunner
from infra_guide.guides import init, plan, apply, destroy


def main():
    """Main entry point for the infra-guide CLI."""
    
    # Detect available tool
    tool = ToolDetector.detect()
    
    if tool is None:
        # No tool found - show error and exit
        temp_ui = InfraGuideUI("none", "none")
        temp_ui.show_no_tool_error()
        sys.exit(1)
    
    # Get tool version
    version = ToolDetector.get_version(tool)
    
    # Initialize UI and runner
    ui = InfraGuideUI(tool, version)
    runner = CommandRunner(tool)
    drift_detector = DriftDetector(tool)
    state_explorer = StateExplorer(tool)
    workspace_manager = WorkspaceManager(tool)
    validator = PreFlightValidator(tool)
    cicd_runner = CICDRunner(tool)
    
    # Main application loop
    while True:
        ui.clear_screen()
        ui.show_banner()
        
        choice = ui.show_menu()
        
        if choice == "1":
            handle_init(ui, runner, tool)
        elif choice == "2":
            handle_plan(ui, runner, tool)
        elif choice == "3":
            handle_apply(ui, runner, tool)
        elif choice == "4":
            handle_destroy(ui, runner, tool)
        elif choice == "5":
            handle_validate(ui, validator)
        elif choice == "6":
            handle_drift(ui, drift_detector)
        elif choice == "7":
            handle_state(ui, state_explorer)
        elif choice == "8":
            workspace_manager.show_workspace_menu()
        elif choice == "9":
            handle_cicd(ui, cicd_runner)
        elif choice == "0":
            ui.clear_screen()
            ui.show_goodbye()
            sys.exit(0)


def handle_init(ui: InfraGuideUI, runner: CommandRunner, tool: str):
    """Handle the init command."""
    ui.clear_screen()
    ui.show_banner()
    
    guide_data = init.get_guide()
    ui.show_guide(
        title="init",
        description=guide_data["description"],
        flags=guide_data["flags"],
        best_practices=guide_data["best_practices"],
        warnings=guide_data["warnings"]
    )
    
    if ui.confirm_execution(f"{tool} init"):
        ui.show_command_output_header(f"{tool} init")
        return_code = runner.execute("init")
        
        if return_code == 0:
            ui.show_success("Initialization completed successfully!")
        else:
            ui.show_error(f"Initialization failed with exit code {return_code}")
        
        ui.wait_for_enter()
    else:
        ui.show_info("Command cancelled.")
        ui.wait_for_enter()


def handle_plan(ui: InfraGuideUI, runner: CommandRunner, tool: str):
    """Handle the plan command."""
    ui.clear_screen()
    ui.show_banner()
    
    guide_data = plan.get_guide()
    ui.show_guide(
        title="plan",
        description=guide_data["description"],
        flags=guide_data["flags"],
        best_practices=guide_data["best_practices"],
        warnings=guide_data["warnings"]
    )
    
    if ui.confirm_execution(f"{tool} plan"):
        ui.show_command_output_header(f"{tool} plan")
        return_code = runner.execute("plan")
        
        if return_code == 0:
            ui.show_success("Plan completed successfully!")
        else:
            ui.show_error(f"Plan failed with exit code {return_code}")
        
        ui.wait_for_enter()
    else:
        ui.show_info("Command cancelled.")
        ui.wait_for_enter()


def handle_apply(ui: InfraGuideUI, runner: CommandRunner, tool: str):
    """Handle the apply command."""
    ui.clear_screen()
    ui.show_banner()
    
    guide_data = apply.get_guide()
    ui.show_guide(
        title="apply",
        description=guide_data["description"],
        flags=guide_data["flags"],
        best_practices=guide_data["best_practices"],
        warnings=guide_data["warnings"]
    )
    
    if ui.confirm_execution(f"{tool} apply"):
        ui.show_command_output_header(f"{tool} apply")
        return_code = runner.execute("apply")
        
        if return_code == 0:
            ui.show_success("Apply completed successfully!")
        else:
            ui.show_error(f"Apply failed with exit code {return_code}")
        
        ui.wait_for_enter()
    else:
        ui.show_info("Command cancelled.")
        ui.wait_for_enter()


def handle_destroy(ui: InfraGuideUI, runner: CommandRunner, tool: str):
    """Handle the destroy command."""
    ui.clear_screen()
    ui.show_banner()
    
    guide_data = destroy.get_guide()
    ui.show_guide(
        title="destroy",
        description=guide_data["description"],
        flags=guide_data["flags"],
        best_practices=guide_data["best_practices"],
        warnings=guide_data["warnings"]
    )
    
    if ui.confirm_execution(f"{tool} destroy"):
        ui.show_command_output_header(f"{tool} destroy")
        return_code = runner.execute("destroy")
        
        if return_code == 0:
            ui.show_success("Destroy completed successfully!")
        else:
            ui.show_error(f"Destroy failed with exit code {return_code}")
        
        ui.wait_for_enter()
    else:
        ui.show_info("Command cancelled.")
        ui.wait_for_enter()


def handle_validate(ui: InfraGuideUI, validator: PreFlightValidator):
    """Handle pre-flight validation."""
    ui.clear_screen()
    ui.show_banner()
    
    ui.show_info("Running comprehensive pre-flight checks...")
    results = validator.run_all_checks()
    validator.show_validation_report(results)
    
    ui.wait_for_enter()


def handle_drift(ui: InfraGuideUI, drift_detector: DriftDetector):
    """Handle drift detection."""
    ui.clear_screen()
    ui.show_banner()
    
    ui.show_info("Detecting infrastructure drift...")
    drift_data = drift_detector.detect_drift()
    drift_detector.show_drift_report(drift_data)
    
    ui.wait_for_enter()


def handle_state(ui: InfraGuideUI, state_explorer: StateExplorer):
    """Handle state exploration."""
    while True:
        ui.clear_screen()
        ui.show_banner()
        
        from rich.prompt import Prompt
        
        ui.console.print("\n[bold cyan]State Explorer Menu[/bold cyan]\n")
        ui.console.print("1. Show state overview")
        ui.console.print("2. List all resources")
        ui.console.print("3. Show resource tree")
        ui.console.print("4. Back to main menu\n")
        
        choice = Prompt.ask(
            "[cyan]Select option[/cyan]",
            choices=["1", "2", "3", "4"],
            default="4"
        )
        
        if choice == "1":
            state_explorer.show_state_overview()
            ui.wait_for_enter()
        elif choice == "2":
            state_explorer.show_resources_list()
            ui.wait_for_enter()
        elif choice == "3":
            state_explorer.show_resource_tree()
            ui.wait_for_enter()
        elif choice == "4":
            break


def handle_cicd(ui: InfraGuideUI, cicd_runner: CICDRunner):
    """Handle CI/CD pipeline mode."""
    ui.clear_screen()
    ui.show_banner()
    
    from rich.prompt import Confirm
    
    ui.console.print("\n[bold yellow]⚠️  CI/CD Pipeline Mode[/bold yellow]\n")
    ui.console.print("[white]This mode runs a complete validation and planning pipeline.")
    ui.console.print("Suitable for continuous integration environments.[/white]\n")
    
    if Confirm.ask("[cyan]Run CI/CD pipeline?[/cyan]", default=False):
        ui.console.print()
        success = cicd_runner.run_full_pipeline()
        
        if success:
            ui.show_success("CI/CD pipeline completed successfully!")
        else:
            ui.show_error("CI/CD pipeline failed. Check output above.")
    else:
        ui.show_info("Pipeline cancelled.")
    
    ui.wait_for_enter()


if __name__ == "__main__":
    main()
