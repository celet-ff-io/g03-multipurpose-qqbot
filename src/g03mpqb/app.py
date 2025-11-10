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

import argparse
from io import TextIOWrapper
import json
import logging
import sys
from typing import Any

import botpy
from botpy.message import Message

if __name__ == "__main__":
    import os.path

    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


logger = logging.getLogger(__name__)


class BotClient(botpy.Client):
    """Bot client."""

    async def on_at_message_create(self, message: Message):
        """Handle @ mention messages."""
        robot = self._require_robot()
        content = message.content
        logger.info(f"Received @ mention message: {content}")
        await message.reply(content=f"{robot.name} received message: {content}")

    def _require_robot(self) -> botpy.Robot:
        """Require the robot associated with this client."""
        robot = self.robot
        if robot is None:
            raise RuntimeError("Robot is not initialized")
        return robot


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
            return self._require_config_entry()

        @property
        def secret(self) -> str:
            """Bot app secret."""
            return self._require_config_entry()

        def _require_config_entry(self, key: str | None = None) -> Any:
            """Require a config entry by key.

            If `key` is omitted, attempt to infer the key from the caller's
            function name (useful for simple property wrappers like
            `def appid(self): return self._require_config_entry()`). If
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

            return App.Config.require_config_entry(self._conf_dict, key)

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

        print("Start client.")
        print("------------------------")
        intents = botpy.Intents(guild_messages=True)
        client = BotClient(intents=intents)
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
