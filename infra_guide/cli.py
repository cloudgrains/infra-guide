"""
Main CLI entry point for infra-guide.
"""

import sys
from infra_guide.detector import ToolDetector
from infra_guide.ui import InfraGuideUI
from infra_guide.runner import CommandRunner
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


if __name__ == "__main__":
    main()
