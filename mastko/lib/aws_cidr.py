import ipaddress
import json
import os
import sys
from typing import List, Optional, Tuple

import requests

from mastko.config.configs import Configs
from mastko.lib.logger import get_logger

log = get_logger("mastko.lib.aws_cidr")


class AwsCidr:
    """Helper class to retrieve AWS CIDR range"""

    def __init__(self) -> None:
        self.aws_ranges_url = "https://ip-ranges.amazonaws.com/ip-ranges.json"
        self.aws_ranges_file_location = f"{Configs.mastko_cache_location}/aws-ip-ranges.json"
        self.get_file()
        self.aws_ranges = self.get_aws_ec2_ipv4_ranges()

    def get_file(self) -> str:
        """Check if AWS Ranges file exists, if not download from AWS"""
        if os.path.isfile(self.aws_ranges_file_location):
            return self.aws_ranges_file_location
        with requests.get(self.aws_ranges_url, stream=True, timeout=10) as request:
            request.raise_for_status()
            with open(self.aws_ranges_file_location, "w", encoding="utf-8") as loc_fi:
                loc_fi.write(request.text)

        return self.aws_ranges_file_location

    def cidr_to_range(self, cidr: str) -> str:
        """Turns a CIDR notation into 'lower_bound,higher_bound' strings."""
        net = ipaddress.ip_network(cidr)
        return str(net[0]) + "," + str(net[-1])

    def get_range_tuple(self, dic: dict) -> Tuple:
        """Takes a host dict and returns host tuple."""
        ip_prefix = dic["ip_prefix"]
        cidr_range = self.cidr_to_range(ip_prefix)
        return (cidr_range, ip_prefix, dic["region"])

    def get_range_min(self, range_tuple: Tuple[str, ...]) -> Tuple:
        """Gets a CIDR range lower bound from a (lower_bound,higher_bound) tuple."""
        cidr_range, *_ = range_tuple
        return self.convert_ipv4(cidr_range.split(",")[0])

    def convert_ipv4(self, ip_address: str) -> Tuple:
        """Turns an IP string into a tuple of ints."""
        return tuple(int(n) for n in ip_address.split("."))

    def get_aws_ec2_ipv4_ranges(self) -> List[Tuple]:
        """Get AWS CIDR range to region allocation as an ordered list of tuples."""
        try:
            aws_ranges = []

            with open(self.aws_ranges_file_location, "r") as ips:
                data = ips.read().strip()
                # restrict the lookup to ipv4 ranges
                for range in json.loads(data)["prefixes"]:
                    if range["service"] == "EC2":
                        range_alloc = self.get_range_tuple(range)
                        aws_ranges.append(range_alloc)
            return sorted(aws_ranges, key=self.get_range_min)
        except Exception as err:
            log.error("%s: %s", err.__class__.__name__, err)
            log.error(err.args[0])
            sys.exit(1)

    def find_alloc_group(self, ip_address: str) -> Optional[str]:
        """Binary search to find an IPs allocation group."""
        low = 0
        mid = 0
        high = len(self.aws_ranges) - 1
        while high >= low:
            mid = (high + low) // 2
            cidr_range, *attrs = self.aws_ranges[mid]
            cidr_low, cidr_high = cidr_range.split(",")
            if self.convert_ipv4(cidr_high) < self.convert_ipv4(ip_address):
                low = mid + 1
            elif self.convert_ipv4(cidr_low) > self.convert_ipv4(ip_address):
                high = mid - 1
            else:
                return attrs[1]

        return None
