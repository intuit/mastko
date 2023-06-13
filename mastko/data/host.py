from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict

from mastko.lib.logger import get_logger

log = get_logger("mastko.data.host")

__domain__ = "domain"
__ip_address__ = "ip_address"


@dataclass
class Host:
    domain: str
    ip_address: str

    @staticmethod
    def from_dict(dct: Dict) -> Host:
        if not (type(dct.get(__domain__)) is str and type(dct.get(__ip_address__)) is str):
            raise TypeError(f"{dct} is not a valid MasTKO Host")

        return Host(domain=dct[__domain__], ip_address=dct[__ip_address__])

    @staticmethod
    def from_json(js: str) -> Host:
        return Host.from_dict(dct=json.loads(js))

    def to_dict(self) -> Dict[str, str]:
        return {
            __domain__: self.domain,
            __ip_address__: self.ip_address,
        }
