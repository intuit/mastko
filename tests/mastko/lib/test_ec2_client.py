from contextlib import contextmanager

import pytest
from moto import mock_ec2  # type: ignore

from mastko.lib.ec2_client import Ec2Client
from mastko.lib.exceptions import Ec2ClientException


@mock_ec2
def test_non_existant_get_eip(aws_credentials):
    ec2_client = Ec2Client(pytest.aws_region)
    try:
        ec2_client.get_eip(ip="1.2.3.4")
        assert False
    except Ec2ClientException:
        assert True


@contextmanager
def create_eip(ec2, ip):
    ec2.allocate_address(Address=ip)
    yield


def test_existing_get_eip(ec2, ip_address="1.2.3.4"):
    with create_eip(ec2, ip_address):
        ec2_client = Ec2Client(aws_region=pytest.aws_region)
        eip = ec2_client.get_eip(ip_address)

        assert eip.ip_address == ip_address


def test_get_eip_addresses_greater_than_one_raise_exception(ec2, ip_address="1.2.3.4"):
    with create_eip(ec2, ip_address):
        ec2.allocate_address(Address="1.2.3.4")  # allocating second address
        ec2_client = Ec2Client(aws_region=pytest.aws_region)

        with pytest.raises(Ec2ClientException) as ex:
            ec2_client.get_eip(ip_address)

        assert "Ambiguous result returned by AWS, got more than one results for public-ip: 1.2.3.4" in str(
            ex.value
        )


def test_get_eip_zero_addresses_raise_exception(ec2, ip_address="1.2.3.4"):
    ec2_client = Ec2Client(aws_region=pytest.aws_region)

    with pytest.raises(Ec2ClientException) as ex:
        ec2_client.get_eip(ip_address)

    assert "No EIP found for public-ip: 1.2.3.4" in str(ex.value)


def test_associate_eip(ec2, ip_address="1.2.3.4"):
    with create_eip(ec2, ip_address):
        ec2_client = Ec2Client(pytest.aws_region)
        eip = ec2_client.get_eip(ip_address)
        ami_id = ec2.describe_images()["Images"][0]["ImageId"]
        instance_id = ec2.run_instances(ImageId=ami_id, MinCount=1, MaxCount=1)["Instances"][0]["InstanceId"]
        ec2_client.associate_eip(ec2_instance_id=instance_id, eip_id=eip.allocation_id)
        associated_eip = ec2.describe_instances()["Reservations"][0]["Instances"][0]["PublicIpAddress"]

        assert eip.ip_address == associated_eip


def test_associate_eip_raise_exception(ec2, mocker):
    ec2_client = Ec2Client(aws_region=pytest.aws_region)
    ec2_client.ec2_client.associate_address = mocker.MagicMock(side_effect=Exception("Association Error"))

    with pytest.raises(
        Ec2ClientException,
        match=(
            "Failed to associate eip for ec2_instance_id: i-1234567890, eip_id: eipalloc-1234567890. ERROR:"
            " Association Error"
        ),
    ):
        ec2_client.associate_eip("i-1234567890", "eipalloc-1234567890")


def test_disassociate_eip(ec2, ip_address="1.2.3.4"):
    with create_eip(ec2, ip_address):
        ec2_client = Ec2Client(pytest.aws_region)
        eip = ec2_client.get_eip(ip_address)
        ami_id = ec2.describe_images()["Images"][0]["ImageId"]
        instance_id = ec2.run_instances(ImageId=ami_id, MinCount=1, MaxCount=1)["Instances"][0]["InstanceId"]
        association_id = ec2_client.associate_eip(ec2_instance_id=instance_id, eip_id=eip.allocation_id)
        ec2_client.disassociate_eip(association_id)
        associated_ip = ec2.describe_instances()["Reservations"][0]["Instances"][0]["PublicIpAddress"]

        assert eip.ip_address != associated_ip


def test_disassociate_eip_raise_exception(ec2, mocker):
    ec2_client = Ec2Client(aws_region=pytest.aws_region)
    ec2_client.ec2_client.disassociate_address = mocker.MagicMock(
        side_effect=Exception("Disassociation Error")
    )

    with pytest.raises(
        Ec2ClientException,
        match="Failed to disassociate eip_association_id: eipassoc-1234567890. ERROR: Disassociation Error",
    ):
        ec2_client.disassociate_eip("eipassoc-1234567890")


def test_tag_instance(ec2, tag_value="test_instance"):
    ami_id = ec2.describe_images()["Images"][0]["ImageId"]
    instance_id = ec2.run_instances(ImageId=ami_id, MinCount=1, MaxCount=1)["Instances"][0]["InstanceId"]
    ec2_client = Ec2Client(pytest.aws_region)
    ec2_client.tag_instance(instance_id, [{"Key": "Name", "Value": tag_value}])
    ec2_name_from_boto3 = ec2.describe_instances()["Reservations"][0]["Instances"][0]["Tags"][0]["Value"]

    assert ec2_name_from_boto3 == tag_value


def test_tag_instance_raise_exception(ec2, mocker):
    ec2_client = Ec2Client(aws_region=pytest.aws_region)
    ec2_client.ec2_client.create_tags = mocker.MagicMock(side_effect=Exception("Fake create tags error"))

    with pytest.raises(
        Ec2ClientException, match="Failed to tag an instance: i-1234567890. ERROR: Fake create tags error"
    ):
        ec2_client.tag_instance("i-1234567890", [{"Key": "Name", "Value": "test_instance"}])


def test_rename_instance(ec2, ec2_name="test_instance"):
    ami_id = ec2.describe_images()["Images"][0]["ImageId"]
    instance_id = ec2.run_instances(ImageId=ami_id, MinCount=1, MaxCount=1)["Instances"][0]["InstanceId"]
    ec2_client = Ec2Client(pytest.aws_region)
    ec2_client.rename_ec2_instance(instance_id, ec2_name)
    ec2_name_from_boto3 = ec2.describe_instances()["Reservations"][0]["Instances"][0]["Tags"][0]["Value"]

    assert ec2_name_from_boto3 == ec2_name


def test_rename_ec2_instance_raise_exception(ec2, mocker):
    ec2_client = Ec2Client(aws_region=pytest.aws_region)
    ec2_client.ec2_client.create_tags = mocker.MagicMock(side_effect=Exception("Fake rename tags error"))

    with pytest.raises(
        Ec2ClientException,
        match=(
            "Failed to rename instance: i-1234567890, new_name: test_instance. ERROR: Fake rename tags error"
        ),
    ):
        ec2_client.rename_ec2_instance("i-1234567890", "test_instance")


def test_get_ec2_public_ip(ec2, ip="1.2.3.4"):
    with create_eip(ec2, ip):
        ami_id = ec2.describe_images()["Images"][0]["ImageId"]
        instance_id = ec2.run_instances(ImageId=ami_id, MinCount=1, MaxCount=1)["Instances"][0]["InstanceId"]
        ec2_client = Ec2Client(pytest.aws_region)
        eip = ec2_client.get_eip(ip)
        ec2_client.associate_eip(ec2_instance_id=instance_id, eip_id=eip.allocation_id)
        associated_eip = ec2.describe_instances()["Reservations"][0]["Instances"][0]["PublicIpAddress"]
        ec2_public_ip = ec2_client.get_ec2_public_ip(instance_id)

        assert associated_eip == ec2_public_ip


def test_get_ec2_public_ip_ambiguous_response_raise_exception(ec2, mocker):
    ec2_client = Ec2Client(aws_region=pytest.aws_region)
    ec2_client.ec2_client.describe_instances = mocker.MagicMock(
        return_value={"Reservations": ["fake-1", "fake-2"]}
    )

    with pytest.raises(Ec2ClientException) as ex:
        ec2_client.get_ec2_public_ip("i-1234567890")

    assert "Describe instance with filter for instance_id: i-1234567890" in str(ex.value)


def test_get_ec2_public_ip_raise_exception(ec2, mocker):
    ec2_client = Ec2Client(aws_region=pytest.aws_region)
    ec2_client.ec2_client.describe_instances = mocker.MagicMock(
        side_effect=Exception("Describe Instances Error")
    )

    with pytest.raises(
        Ec2ClientException,
        match="Failed to get public ip_address of intance: i-1234567890. ERROR: Describe Instances Error",
    ):
        ec2_client.get_ec2_public_ip("i-1234567890")
