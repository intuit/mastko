from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Configs:
    mastko_cache_location: Path = Path.joinpath(Path.home(), ".mastko")
    successful_takeover_ec2_name: str = "dns_takeover_instance"
    db_name: str = "mastko.db"
    db_path_uri: str = str(Path.joinpath(mastko_cache_location, db_name))
    aws_api_retry_count: int = 5
