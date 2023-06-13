from __future__ import annotations

import csv
import json
import sqlite3
from dataclasses import dataclass
from typing import Dict, List, Set

from tqdm import tqdm  # type: ignore

from mastko.config.configs import Configs
from mastko.lib.exceptions import DatabaseException
from mastko.lib.logger import get_logger

log = get_logger("mastko.data.target")

__domain__ = "domain"
__ip_address__ = "ip_address"
__region__ = "region"


@dataclass
class Target:
    domain: str
    ip_address: str
    region: str

    @staticmethod
    def from_dict(dct: Dict) -> Target:
        if not (
            type(dct.get(__domain__)) is str
            and type(dct.get(__ip_address__)) is str
            and type(dct.get(__region__)) is str
        ):
            raise TypeError(f"{dct} is not a valid MasTKO Target")

        return Target(domain=dct[__domain__], ip_address=dct[__ip_address__], region=dct[__region__])

    @staticmethod
    def from_json(js: str) -> Target:
        return Target.from_dict(dct=json.loads(js))

    def to_dict(self) -> Dict[str, str]:
        return {
            __domain__: self.domain,
            __ip_address__: self.ip_address,
            __region__: self.region,
        }

    @staticmethod
    def to_csv(targets: List[Target], output_file_name: str) -> str:
        with open(f"{output_file_name}", "w+", newline="") as output_csv:
            headers = [__domain__, __ip_address__, __region__]
            writer = csv.DictWriter(output_csv, fieldnames=headers)
            writer.writeheader()
            for target in targets:
                writer.writerow(target.to_dict())

        return output_file_name

    @staticmethod
    def init_db_table() -> None:
        try:
            db = sqlite3.connect(Configs.db_path_uri)
            cursor = db.cursor()
            res = cursor.execute("SELECT name FROM sqlite_master WHERE name='targets'")
            if res.fetchone() is None:
                log.debug("targets table does not exist, creating one now.")
                sql = f"""CREATE TABLE targets ({__domain__} CHAR(500),
                                                {__ip_address__} CHAR(250) NOT NULL,
                                                {__region__} CHAR(250))"""
                cursor.execute(sql)
                db.commit()
            db.close()
        except sqlite3.Error as ex:
            raise DatabaseException(f"Failed to create targets table in database, error: {ex}")

    @staticmethod
    def target_available() -> bool:
        try:
            db = sqlite3.connect(Configs.db_path_uri)
            cursor = db.cursor()
            sql = "SELECT COUNT(*) > 0 FROM targets"
            results = cursor.execute(sql)
            return bool(results.fetchone()[0])
        except sqlite3.Error as ex:
            raise DatabaseException(f"Failed to check for targets in database, error: {ex}")

    @staticmethod
    def get_all_targets_from_db() -> List[Target]:
        try:
            db = sqlite3.connect(Configs.db_path_uri)
            cursor = db.cursor()
            sql = "SELECT * FROM targets"
            results = cursor.execute(sql)
            db_rows = results.fetchall()
            targets: List[Target] = []
            for row in db_rows:
                targets.append(Target(domain=row[0], ip_address=row[1], region=row[2]))
            db.commit()
            db.close()
            return targets
        except sqlite3.Error as ex:
            raise DatabaseException(f"Failed to get targets from database, error: {ex}")

    @staticmethod
    def insert_targets_to_db(targets: List[Target]) -> None:
        # perform cleanup
        distinct_domains: Set[str] = set()
        for target in targets:
            distinct_domains.add(target.domain)
        Target.delete_records_with_domains(domains=list(distinct_domains))

        # Load new targets
        for target in tqdm(targets, desc="loading targets to DB"):
            Target.__insert_target_to_db(target)

    # Private method, should not be used outside the class.
    @staticmethod
    def __insert_target_to_db(target: Target) -> None:
        try:
            db = sqlite3.connect(Configs.db_path_uri)
            cursor = db.cursor()
            sql = "INSERT INTO targets (domain, ip_address, region) VALUES (?,?,?)"
            args = (target.domain, target.ip_address, target.region)
            cursor.execute(sql, args)
        except sqlite3.Error as ex:
            raise DatabaseException(f"Failed to insert target: {target} into database, error: {ex}")
        finally:
            db.commit()
            cursor.close()
            db.close()

    @staticmethod
    def delete_records_with_domains(domains: List[str]) -> None:
        for domain in domains:
            Target.delete_record_with_domain(domain)

    @staticmethod
    def delete_record_with_domain(domain: str) -> None:
        try:
            db = sqlite3.connect(Configs.db_path_uri)
            cursor = db.cursor()
            sql = "DELETE FROM targets WHERE domain = ?"
            args = (domain,)
            cursor.execute(sql, args)
        except sqlite3.Error as ex:
            raise DatabaseException(
                f"Failed to delete record with domain: {domain} from database, error: {ex}"
            )
        finally:
            db.commit()
            cursor.close()
            db.close()
