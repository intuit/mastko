import json
import pytest
import sqlite3
import os

from mastko.data.target import Target
from mastko.config.configs import Configs


def test_dumpingAndLoadingDict_shouldClonesClass():
    target = Target(domain="example.com", ip_address="1.2.3.4", region="us-west-2")

    dictionary = target.to_dict()
    cloned_target = Target.from_dict(dictionary)

    assert target == cloned_target
    assert target is not cloned_target


def test_jsonSerializeAndDeserialize_shouldClonesClass():
    target = Target(domain="example.com", ip_address="1.2.3.4", region="us-west-2")

    json_str = json.dumps(target.to_dict())
    cloned_target = Target.from_json(json_str)

    assert target == cloned_target
    assert target is not cloned_target


def test_target_from_dict_TypeError():
    with pytest.raises(TypeError) as ex:
        Target.from_dict({"domain": "fake-domain", "ip_address": 1234, "region": "us-west-2"})

    assert ex.type is TypeError
    assert "is not a valid MasTKO Target" in str(ex.value)


def test_target_table_creation(mocker):
    try:
        mocker.patch.object(Configs, "db_path_uri", "/tmp/mastko.db")
        Target.init_db_table()
        db = sqlite3.connect(Configs.db_path_uri)
        cursor = db.cursor()
        res = cursor.execute("SELECT name FROM sqlite_master WHERE name='targets'")

        assert res.fetchone is not None
    finally:
        os.remove("/tmp/mastko.db")


def test_get_all_target_from_db(mocker):
    try:
        targets = [Target(domain="example.com", ip_address="1.2.3.4", region="us-west-2")]
        mocker.patch.object(Configs, "db_path_uri", "/tmp/mastko.db")
        Target.init_db_table()
        Target.insert_targets_to_db(targets)

        assert Target.get_all_targets_from_db() == targets
    finally:
        os.remove("/tmp/mastko.db")


def test_target_available(mocker):
    try:
        mocker.patch.object(Configs, "db_path_uri", "/tmp/mastko.db")
        Target.init_db_table()

        assert Target.target_available() is False
    finally:
        os.remove("/tmp/mastko.db")
