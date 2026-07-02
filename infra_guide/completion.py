"""
Shell completion scripts for infra-guide.

Outputs a completion script for the requested shell.  Users add one line
to their shell rc file to enable tab completion for all infra-guide
subcommands, flags, and theme names.
"""

from infra_guide.preferences import THEMES

_SUBCOMMANDS = [
    "interactive",
    "status",
    "doctor",
    "guide",
    "history",
    "theme",
    "web",
    "validate",
    "drift",
    "state",
    "workspace",
    "fmt",
    "cicd",
    "output",
    "policy",
    "init",
    "plan",
    "apply",
    "destroy",
    "completion",
]

_THEME_NAMES = sorted(THEMES.keys())
_GUIDE_COMMANDS = ["init", "plan", "apply", "destroy"]


def _bash_script() -> str:
    subcommands = " ".join(_SUBCOMMANDS)
    themes = " ".join(_THEME_NAMES)
    guides = " ".join(_GUIDE_COMMANDS)
    return f"""\
# infra-guide bash completion
# Add this line to ~/.bashrc or ~/.bash_profile:
#   eval "$(infra-guide completion bash)"

_infra_guide_completion() {{
    local cur prev words cword
    _init_completion 2>/dev/null || {{
        COMPREPLY=()
        cur="${{COMP_WORDS[COMP_CWORD]}}"
        prev="${{COMP_WORDS[COMP_CWORD-1]}}"
    }}

    local subcommands="{subcommands}"
    local themes="{themes}"
    local guides="{guides}"

    if [[ ${{COMP_CWORD}} -eq 1 ]]; then
        COMPREPLY=( $(compgen -W "$subcommands" -- "$cur") )
        return 0
    fi

    case "${{COMP_WORDS[1]}}" in
        theme)
            case "$prev" in
                --set) COMPREPLY=( $(compgen -W "$themes" -- "$cur") ) ;;
                *) COMPREPLY=( $(compgen -W "--list --set" -- "$cur") ) ;;
            esac
            ;;
        guide)
            COMPREPLY=( $(compgen -W "$guides" -- "$cur") ) ;;
        doctor)
            COMPREPLY=( $(compgen -W "--with-drift" -- "$cur") ) ;;
        plan)
            COMPREPLY=( $(compgen -W "--out --detailed-exitcode --destroy-mode --refresh-only --no-refresh --var --var-file --target --parallelism" -- "$cur") ) ;;
        apply)
            COMPREPLY=( $(compgen -W "--plan-file --yes --no-refresh --var --var-file --target --parallelism" -- "$cur") ) ;;
        destroy)
            COMPREPLY=( $(compgen -W "--yes --no-refresh --var --var-file --target --parallelism" -- "$cur") ) ;;
        init)
            COMPREPLY=( $(compgen -W "--upgrade --reconfigure --migrate-state --backend-config --no-get" -- "$cur") ) ;;
        web)
            COMPREPLY=( $(compgen -W "--host --port --no-browser" -- "$cur") ) ;;
        state)
            COMPREPLY=( $(compgen -W "--list --tree --detail" -- "$cur") ) ;;
        workspace)
            COMPREPLY=( $(compgen -W "--list --select --create --delete" -- "$cur") ) ;;
        fmt)
            COMPREPLY=( $(compgen -W "--check --diff --no-recursive" -- "$cur") ) ;;
        completion)
            COMPREPLY=( $(compgen -W "bash zsh fish" -- "$cur") ) ;;
        history)
            COMPREPLY=( $(compgen -W "--favorites --clear" -- "$cur") ) ;;
        policy)
            COMPREPLY=( $(compgen -W "--plan-file" -- "$cur") ) ;;
        output)
            COMPREPLY=( $(compgen -W "--json --raw" -- "$cur") ) ;;
    esac
    return 0
}}

complete -F _infra_guide_completion infra-guide
"""


def _zsh_script() -> str:
    subcommands = "\n    ".join(f"'{s}'" for s in _SUBCOMMANDS)
    themes = " ".join(_THEME_NAMES)
    return f"""\
#compdef infra-guide
# infra-guide zsh completion
# Add this line to ~/.zshrc:
#   eval "$(infra-guide completion zsh)"

_infra_guide() {{
    local -a subcommands
    subcommands=(
    {subcommands}
    )

    _arguments \\
        '(--tool)--tool[force IaC tool]:tool:(tofu terraform)' \\
        '(--theme)--theme[session theme]:theme:({themes})' \\
        '(--no-color)--no-color[disable colour output]' \\
        '(--version)--version[print version]' \\
        '1:command:->subcmd' \\
        '*::args:->args'

    case $state in
        subcmd)
            _describe 'subcommand' subcommands
            ;;
        args)
            case $words[1] in
                theme)
                    _arguments \\
                        '--list[list themes]' \\
                        '--set[save theme]:theme:({themes})'
                    ;;
                guide)
                    _arguments '1:command:(init plan apply destroy)'
                    ;;
                completion)
                    _arguments '1:shell:(bash zsh fish)'
                    ;;
                plan)
                    _arguments \\
                        '--out[plan file]:file:_files' \\
                        '--detailed-exitcode' \\
                        '--refresh-only' \\
                        '--no-refresh' \\
                        '--var[variable]:VAR:' \\
                        '--var-file[var file]:file:_files' \\
                        '--target[resource]:address:'
                    ;;
                apply)
                    _arguments \\
                        '--plan-file[plan file]:file:_files' \\
                        '--yes[auto-approve]' \\
                        '--var[variable]:VAR:' \\
                        '--var-file[var file]:file:_files' \\
                        '--target[resource]:address:'
                    ;;
                destroy)
                    _arguments '--yes[auto-approve]'
                    ;;
                web)
                    _arguments \\
                        '--port[port]:port:' \\
                        '--host[host]:host:' \\
                        '--no-browser'
                    ;;
                state)
                    _arguments '--list' '--tree' '--detail[address]:address:'
                    ;;
                workspace)
                    _arguments '--list' '--select[name]:name:' '--create[name]:name:' '--delete[name]:name:'
                    ;;
            esac
            ;;
    esac
}}

_infra_guide "$@"
"""


def _fish_script() -> str:
    subcommands = "\n".join(
        f"complete -c infra-guide -f -n '__fish_use_subcommand' -a '{s}'" for s in _SUBCOMMANDS
    )
    themes = " ".join(_THEME_NAMES)
    return f"""\
# infra-guide fish completion
# Add this line to ~/.config/fish/config.fish:
#   infra-guide completion fish | source

function __fish_use_subcommand
    set cmd (commandline -opc)
    if test (count $cmd) -eq 1
        return 0
    end
    return 1
end

# Global flags
complete -c infra-guide -l tool -d 'Force IaC tool' -a 'tofu terraform'
complete -c infra-guide -l theme -d 'Session theme' -a '{themes}'
complete -c infra-guide -l no-color -d 'Disable colour output'
complete -c infra-guide -l version -d 'Print version'
complete -c infra-guide -l cwd -d 'Working directory' -r

# Subcommands
{subcommands}

# Theme args
complete -c infra-guide -f -n '__fish_seen_subcommand_from theme' -l list -d 'List themes'
complete -c infra-guide -f -n '__fish_seen_subcommand_from theme' -l set -d 'Save theme' -a '{themes}'

# Plan args
complete -c infra-guide -f -n '__fish_seen_subcommand_from plan' -l out -d 'Save plan file' -r
complete -c infra-guide -f -n '__fish_seen_subcommand_from plan' -l detailed-exitcode
complete -c infra-guide -f -n '__fish_seen_subcommand_from plan' -l refresh-only
complete -c infra-guide -f -n '__fish_seen_subcommand_from plan' -l no-refresh
complete -c infra-guide -f -n '__fish_seen_subcommand_from plan apply destroy' -l var -d 'Variable KEY=VALUE'
complete -c infra-guide -f -n '__fish_seen_subcommand_from plan apply destroy' -l var-file -d 'Variable file' -r
complete -c infra-guide -f -n '__fish_seen_subcommand_from plan apply destroy' -l target -d 'Resource address'

# Apply args
complete -c infra-guide -f -n '__fish_seen_subcommand_from apply' -l plan-file -d 'Apply saved plan' -r
complete -c infra-guide -f -n '__fish_seen_subcommand_from apply destroy' -l yes -d 'Auto-approve'

# Web args
complete -c infra-guide -f -n '__fish_seen_subcommand_from web' -l port -d 'HTTP port'
complete -c infra-guide -f -n '__fish_seen_subcommand_from web' -l host -d 'Bind host'
complete -c infra-guide -f -n '__fish_seen_subcommand_from web' -l no-browser

# Completion args
complete -c infra-guide -f -n '__fish_seen_subcommand_from completion' -a 'bash zsh fish'
"""


_SCRIPTS = {
    "bash": _bash_script,
    "zsh": _zsh_script,
    "fish": _fish_script,
}


def get_completion_script(shell: str) -> str:
    """Return the completion script for the requested shell."""
    fn = _SCRIPTS.get(shell)
    if fn is None:
        raise ValueError(f"Unsupported shell: {shell!r}. Choose from: bash, zsh, fish")
    return fn()
