"""
Support shell functions
"""

import os
import re
import sys
from enum import Enum

from psutil import Process


class Shell(Enum):
    Linux = 1
    WindowsCommandPrompt = 2
    PowerShell = 3


def get_shell_type():
    """
    Check if running on Windows and what shell type were we launched from
    """
    if sys.platform.startswith("win"):
        parent_proc = os.getppid()
        parent_name = Process(parent_proc).name()

        if bool(re.match("pwsh*|pwsh.exe|powershell.exe", parent_name)):
            return Shell.PowerShell

        return Shell.WindowsCommandPrompt

    return Shell.Linux


def print_set_env_command(name, value):
    """
    Print command to set environment variable,
    format it correctly for the current platform
    """
    shell_type = get_shell_type()
    if shell_type == Shell.Linux:
        print(f'export {name!s}="{value!s}";')
    elif shell_type == Shell.PowerShell:
        print(f'$Env:{name!s}="{value!s}";')
    else:
        print(f"set {name!s}={value!s}")


def print_comment(comment):
    """
    Print comment command,
    format it correctly for the current platform
    """
    shell_type = get_shell_type()
    if shell_type == Shell.Linux:
        print(f"# {comment!s}")
    elif shell_type == Shell.PowerShell:
        print(f"# {comment!s}")
    else:
        print(f"rem {comment!s}")
