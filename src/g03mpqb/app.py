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

"""Main application."""

import argparse
from io import TextIOWrapper
import json
import logging
import sys
from typing import Any

import botpy
from botpy.message import DirectMessage

from g03mpqb.command import Command, Commander

if __name__ == "__main__":
    import os.path

    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


logger = logging.getLogger(__name__)


class BotClient(botpy.Client):
    """Bot client."""

    class OnMessageListener:
        """Message listener."""

        __slots__ = ()

        def on_direct_message_create(self, message: DirectMessage) -> str:
            """Handle direct messages."""
            return ""

    __on_message_listener: OnMessageListener | None

    @property
    def on_message_listener(self) -> OnMessageListener:
        """Get the on-message listener associated with this client."""
        if self.__on_message_listener is None:
            raise RuntimeError("Client's on-message listener is not initialized")
        return self.__on_message_listener

    @on_message_listener.setter
    def on_message_listener(self, on_message_listener: OnMessageListener) -> None:
        """Set the on-message listener associated with this client."""
        self.__on_message_listener = on_message_listener

    async def on_direct_message_create(self, message: DirectMessage) -> None:
        """Handle direct messages."""
        logger.info(f"Received direct message from {message.author}: {message.content}")
        reply_content = self.on_message_listener.on_direct_message_create(message)
        await message.reply(content=reply_content)


class ConfigError(KeyError):
    """Missing entry in config."""

    _missing: str

    def __init__(self, missing_key: str):
        self._missing = missing_key

    def __repr__(self) -> str:
        return f"Missing entry with key {self._missing}"


type ConfigDict = dict[str, Any]


class App:
    """Main application class."""

    class Config:
        """Application config."""

        _conf_dict: dict

        def __init__(self, config_dict: dict) -> None:
            self._conf_dict = config_dict

        @property
        def appid(self) -> str:
            """Bot app ID."""
            return self._config_entry()

        @property
        def secret(self) -> str:
            """Bot app secret."""
            return self._config_entry()

        @property
        def commands(self) -> dict[str, Command]:
            """Commands."""
            return self._config_entry(required=False, default={})

        def _config_entry(
            self,
            key: str | None = None,
            *,
            required: bool = True,
            default: Any = None,
        ) -> Any:
            """Require a config entry by key.

            If `key` is omitted, attempt to infer the key from the caller's
            function name (useful for simple property wrappers like
            `def appid(self): return self._config_entry()`). If
            inference fails, raise a ValueError to require the caller to pass
            the key explicitly.
            """
            if key is None:
                # Import here to keep module imports minimal at top-level.
                import inspect

                frame = inspect.currentframe()
                try:
                    caller_name = None
                    if frame is not None and frame.f_back is not None:
                        caller_name = frame.f_back.f_code.co_name
                    if not caller_name or caller_name == "<module>":
                        raise ValueError(
                            "Unable to infer config key from caller; please provide the key explicitly"
                        )
                    key = caller_name
                finally:
                    # Break reference cycles created by frame objects
                    del frame

            conf_dict = self._conf_dict
            return (
                App.Config.require_config_entry(conf_dict, key)
                if required
                else conf_dict.get(key, default)
            )

        @classmethod
        def load_json(cls, fp: TextIOWrapper) -> "App.Config":
            """Load config from json file."""
            conf_dict = json.load(fp)
            return App.Config(conf_dict)

        @staticmethod
        def require_config_entry(config_dict: ConfigDict, key: str) -> Any:
            """Get config entry by key."""
            try:
                return config_dict[key]
            except KeyError:
                raise ConfigError(key)

    _config: Config
    _commander: Commander

    def __init__(self, config_path: str) -> None:
        """Initialize and run the application."""

        print("Loading config...")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                self._config = config = App.Config.load_json(f)
        except IOError as err:
            print("Failed to read config file.")
            raise err
        except json.JSONDecodeError as err:
            print("Failed to parse JSON config file.")
            raise err
        print("Config loaded.")

        self._commander = commander = Commander(config.commands)

        print("Start client.")
        print("------------------------")
        intents = botpy.Intents.all()
        client = BotClient(intents=intents)

        class AppOnMessageListener(BotClient.OnMessageListener):
            """Message listener."""

            def on_direct_message_create(self, message: DirectMessage) -> str:
                """Handle direct messages."""
                cmd_name = message.content.strip()
                resp = commander.run_command_noblock(cmd_name)
                if resp is None:
                    reply_content = f"Failed to execute command."
                    logger.info(
                        "Failed command from %s: %s", message.author, cmd_name
                    )
                else:
                    reply_content = (
                        resp if resp else "Executed command successfully."
                    )
                    logger.info(
                        "Executed command from %s: %s -> %s",
                        message.author,
                        cmd_name,
                        reply_content,
                    )
                return reply_content

        client.on_message_listener = AppOnMessageListener()
        client.run(appid=config.appid, secret=config.secret)


def main() -> int:
    """Run the bot application."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        help="Path to the secret JSON config file.",
    )
    args = parser.parse_args()
    try:
        arg_config = args.config
        if arg_config is None:
            print("Config file path required (-c/--config).")
            raise ValueError("Config file path is required")
        App(arg_config)
    except Exception as err:
        print(f"Error:\n{type(err).__name__}: {err}")
        return 1
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())
