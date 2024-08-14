from pathlib import Path

from dynaconf import Dynaconf


class Config(Dynaconf):
    @classmethod
    def load(cls, config_path: Path) -> Dynaconf:
        return Dynaconf(environments=True, settings_files=[config_path])
