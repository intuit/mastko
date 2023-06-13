from mastko.config.configs import Configs
from mastko.data.target import Target
from mastko.lib.bruteforcer import Bruteforcer, BruteforcerException

import pytest


@pytest.fixture
def mock_ec2_client(mocker):
    return mocker.patch("mastko.lib.bruteforcer.Ec2Client")


@pytest.fixture
def brute_forcer(mock_ec2_client):
    return Bruteforcer(
        targets=[Target(domain="example.com", ip_address="1.2.3.4", region="us-west-2")],
        region="us-west-2",
        instance_id="i-1234567890abcdef0",
        eip_ip="1.2.3.4",
    )


def test_BruteForcer_init(mock_ec2_client):
    targets = [Target(domain="example.com", ip_address="1.2.3.4", region="us-west-2")]
    region = "us-west-2"
    instance_id = "i-1234567890abcdef0"
    eip_ip = "1.2.3.4"
    get_eip_return_value = "eip-1234567890abcdef0"

    mock_ec2_client().get_eip.return_value = get_eip_return_value

    bf = Bruteforcer(targets=targets, region=region, instance_id=instance_id, eip_ip=eip_ip)

    assert bf.targets == targets
    assert bf.region == region
    assert bf.eip == get_eip_return_value
    assert bf.ec2.instance_id == instance_id
    assert bf.target_hash == {
        "1.2.3.4": [Target(domain="example.com", ip_address="1.2.3.4", region="us-west-2")]
    }


def test_get_targets_grouped_by_ip(brute_forcer):
    targets = [
        Target(ip_address="2.3.4.5", domain="get_targets_1.com", region="us-west-2"),
        Target(ip_address="3.3.4.5", domain="get_targets_2.com", region="us-west-2"),
        Target(ip_address="4.3.4.5", domain="sub.get_targets_3.com", region="us-west-2"),
        Target(ip_address="4.3.4.5", domain="sub.get_targets_3.com", region="us-west-2"),
    ]

    results = brute_forcer._get_targets_grouped_by_ip(targets)

    assert list(results.keys()) == ["2.3.4.5", "3.3.4.5", "4.3.4.5"]
    assert results["2.3.4.5"] == [targets[0]]
    assert results["3.3.4.5"] == [targets[1]]
    assert results["4.3.4.5"] == [targets[2], targets[3]]


def test_rotate_ip(brute_forcer):
    brute_forcer.ec2_client.associate_eip.return_value = "fake-eip-allocation-id-return"
    brute_forcer.rotate_ip(ec2_instance_id="fake-instance-id", eip_allocation_id="fake-eip-id")

    brute_forcer.ec2_client.associate_eip.assert_called_once_with(
        ec2_instance_id="fake-instance-id", eip_id="fake-eip-id"
    )
    brute_forcer.ec2_client.disassociate_eip.assert_called_once_with(
        eip_association_id="fake-eip-allocation-id-return"
    )


def test_rotate_ip_raise_exception(brute_forcer):
    brute_forcer.ec2_client.associate_eip.side_effect = Exception("fake-exception")
    with pytest.raises(Exception) as ex:
        brute_forcer.rotate_ip(ec2_instance_id="fake-instance-id", eip_allocation_id="fake-eip-id")
    assert ex.type is BruteforcerException


def test_is_takeover_true(brute_forcer):
    assert brute_forcer._is_takeover(ec2_public_ip="1.2.3.4") is True


def test_is_takeover_false(brute_forcer):
    assert brute_forcer._is_takeover(ec2_public_ip="8.8.8.8") is False


def test_attempt_takeover(brute_forcer, mocker):
    brute_forcer.ec2_client.get_ec2_public_ip.return_value = "fake-public-ip"
    brute_forcer.ec2_client.get_eip.return_value = mocker.Mock(allocation_id="fake-allocation-id")

    ip_str = brute_forcer._attempt_takeover(ec2=brute_forcer.ec2, eip=brute_forcer.eip)

    brute_forcer.ec2_client.get_ec2_public_ip.assert_called_once_with("i-1234567890abcdef0")
    assert ip_str == "fake-public-ip"


def test_process_successful_takeover(brute_forcer):
    expected_tags = [{"Key": "domain_0", "Value": "example.com"}]
    brute_forcer._process_successful_takeover(ec2=brute_forcer.ec2, takeover_ip="1.2.3.4")

    brute_forcer.ec2_client.rename_ec2_instance.assert_called_once_with(
        "i-1234567890abcdef0", Configs.successful_takeover_ec2_name
    )
    brute_forcer.ec2_client.tag_instance.assert_called_once_with(
        instance_id="i-1234567890abcdef0", tags=expected_tags
    )


def test_run_takeover_exists(brute_forcer, mocker):
    brute_forcer._attempt_takeover = mocker.Mock(return_value="fake-new-ip")
    brute_forcer._is_takeover = mocker.Mock(return_value=True)
    brute_forcer._process_successful_takeover = mocker.Mock()

    brute_forcer.run(iterations=1)

    brute_forcer._attempt_takeover.assert_called_once_with(brute_forcer.ec2, brute_forcer.eip)
    brute_forcer._is_takeover.assert_called_once_with("fake-new-ip")
    brute_forcer._process_successful_takeover.assert_called_once_with(brute_forcer.ec2, "fake-new-ip")


def test_run_takeover_does_not_exist(brute_forcer, mocker):
    brute_forcer._attempt_takeover = mocker.Mock(return_value="fake-new-ip")
    brute_forcer._is_takeover = mocker.Mock(return_value=False)
    brute_forcer._process_successful_takeover = mocker.Mock()

    brute_forcer.run(iterations=1)

    brute_forcer._attempt_takeover.assert_called_once_with(brute_forcer.ec2, brute_forcer.eip)
    brute_forcer._is_takeover.assert_called_once_with("fake-new-ip")
    brute_forcer._process_successful_takeover.assert_not_called()


def test_run_raises_exception(brute_forcer, mocker):
    brute_forcer._attempt_takeover = mocker.Mock(side_effect=Exception("fake-exception"))
    with pytest.raises(Exception) as ex:
        brute_forcer.run(iterations=1)
    assert ex.type is BruteforcerException
