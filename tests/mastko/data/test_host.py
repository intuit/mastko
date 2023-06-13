import json
import pytest

from mastko.data.host import Host


def test_dumpingAndLoadingDict_shouldClonesClass():
    host = Host(domain="example.com", ip_address="1.2.3.4")

    dictionary = host.to_dict()
    cloned_target = Host.from_dict(dictionary)

    assert host == cloned_target
    assert host is not cloned_target


def test_jsonSerializeAndDeserialize_shouldClonesClass():
    host = Host(domain="example.com", ip_address="1.2.3.4")

    json_str = json.dumps(host.to_dict())
    cloned_target = Host.from_json(json_str)

    assert host == cloned_target
    assert host is not cloned_target


def test_host_from_dict_TypeError():
    with pytest.raises(TypeError) as ex:
        Host.from_dict({"domain": "fake-domain", "ip_address": 1234})

    assert ex.type is TypeError
    assert "is not a valid MasTKO Host" in str(ex.value)
