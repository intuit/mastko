from pathlib import Path

from mastko.config.configs import Configs

# create cache folder
Path.mkdir(Configs.mastko_cache_location, exist_ok=True)
