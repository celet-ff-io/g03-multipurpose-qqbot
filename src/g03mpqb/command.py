# Copyright 2025 IO Club
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Commands."""

import logging
import subprocess
from typing import TypedDict, NotRequired

logger = logging.getLogger(__name__)

type Executable = list[str]


class Command(TypedDict):
    """Command details."""

    execute: Executable
    response: NotRequired[str]
    shell: NotRequired[bool]


class Commander:
    """Command runner."""

    _commands: dict[str, Command]

    def __init__(self, commands: dict[str, Command]) -> None:
        self._commands = commands

    def run_command_noblock(self, name: str) -> str | None:
        """Run a command if it exists."""
        command = self._commands.get(name)
        if command is None:
            return None

        try:
            execute = command["execute"]
            shell = command.get("shell", False)

            subprocess.Popen(execute, shell=shell)

        except KeyError:
            print(
                f"Loaded command '{name}' is missing 'execute' field.",
            )
            logger.error("Loaded command '%s' is missing 'execute' field.", name)
            return None

        except Exception as err:
            return f"Failed to execute command '{name}': {err}"

        else:
            return command.get("response", "")
