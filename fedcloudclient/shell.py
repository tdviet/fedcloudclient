import os
import re
import sys
from enum import Enum

from psutil import Process


class Shell(Enum):
    Linux = 1
    WindowsCommandPrompt = 2
    PowerShell = 3


def getShellType():
    """
    Check if running on Windows and what shell type were we launched from
    """
    if sys.platform.startswith("win"):
        parentProc = os.getppid()
        parentName = Process(parentProc).name()

        if bool(re.match("pwsh*|pwsh.exe|powershell.exe", parentName)):
            return Shell.PowerShell

        return Shell.WindowsCommandPrompt

    return Shell.Linux


def printSetEnvCommand(name, value):
    """
    Print command to set environment variable,
    format it correctly for the current platform
    """
    shellType = getShellType()
    if shellType == Shell.Linux:
        print(f'export {name!s}="{value!s}";')
    elif shellType == Shell.PowerShell:
        print(f'$Env:{name!s}="{value!s}";')
    else:
        print(f"set {name!s}={value!s}")


def printComment(comment):
    """
    Print comment command,
    format it correctly for the current platform
    """
    shellType = getShellType()
    if shellType == Shell.Linux:
        print(f"# {comment!s}")
    elif shellType == Shell.PowerShell:
        print(f"# {comment!s}")
    else:
        print(f"rem {comment!s}")
