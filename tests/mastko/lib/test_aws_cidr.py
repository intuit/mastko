from mastko.lib.aws_cidr import AwsCidr
from mastko.config.configs import Configs
import os
import json

def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code
            self.text = json_data

        def raise_for_status(self):
            return True
        
        def __enter__(*args):
            return MockResponse(
                json.dumps({"prefixes": [
                    {
                    "ip_prefix": "1.2.3.4/32",
                    "region": "us-east-2",
                    "service": "EC2",
                    "network_border_group": "us-east-2"
                    }
                ]}),
                200
            )

        def __exit__(*args):
            pass

    return MockResponse(
        json.dumps({"prefixes": [
                    {
                    "ip_prefix": "1.2.3.4/32",
                    "region": "us-east-2",
                    "service": "EC2",
                    "network_border_group": "us-east-2"
                    }
                ]}),
        200
    )



def test_get_region_for_aws_ip(mocker):
    try:
        mocker.patch.object(Configs, "mastko_cache_location", "/tmp")
        mocker.patch('requests.get', mocked_requests_get)
        aws_cidr = AwsCidr()
        aws_cidr.get_file()

        associated_region = aws_cidr.find_alloc_group("1.2.3.4")

        assert associated_region == "us-east-2"
    finally:
        os.remove("/tmp/aws-ip-ranges.json")


def test_get_region_for_non_aws_ip(mocker):
    try:
        mocker.patch.object(Configs, "mastko_cache_location", "/tmp")
        mocker.patch('requests.get', mocked_requests_get)
        aws_cidr = AwsCidr()
        aws_cidr.get_file()
        print(aws_cidr.aws_ranges)

        associated_region = aws_cidr.find_alloc_group("4.3.2.1")

        assert associated_region is None
    finally:
        os.remove("/tmp/aws-ip-ranges.json")