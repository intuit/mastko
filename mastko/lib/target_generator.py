import os
import re
import socket
import subprocess
import sys
from concurrent import futures
from pathlib import Path
from typing import Dict, List, Optional

from tqdm import tqdm

from mastko.config.configs import Configs
from mastko.data.host import Host
from mastko.data.target import Target
from mastko.lib.aws_cidr import AwsCidr
from mastko.lib.exceptions import (
    FileImportException,
    NoTargetsFound,
    TargetGeneratorException,
)
from mastko.lib.logger import get_logger

log = get_logger("mastko.lib.target_generator")


class TargetGenerator:
    """Produces a list of EC2 IP subdomain takeover opportunities."""

    def __init__(self, hosts_file: str, region: Optional[str] = None):
        self.hosts = self.import_hosts_from_file(hosts_file)
        self.region = self.validate_region(region)
        self.threads = 20
        self.aws_cidr = AwsCidr()

    def import_hosts_from_file(self, file_name: str) -> List[str]:
        try:
            file = Path(file_name)

            if not file.is_file():
                raise FileImportException(
                    f"The file_name: {file_name} does not exists. Please verify the file path."
                )

            hosts: List[str] = []

            with open(file_name, encoding="utf-8") as host_file:
                hosts = host_file.read().splitlines()

            return hosts
        except Exception as ex:
            if ex.__class__ == "FileImportException":
                raise ex

            raise FileImportException(f"Failed to import hosts from file_name: {file_name}, ERROR: {ex}")

    def validate_region(self, region: Optional[str]) -> Optional[str]:
        if not region:
            log.info("Region not specified, will produce targets for all AWS Regions.")
            return None
        elif region and not bool(re.match(r"^[a-zA-Z]{2}-[a-zA-Z]+-[0-9]$", region)):
            log.error("Invalid AWS Region specified: %s", region)
            sys.exit(1)
        else:
            log.info("Producing ec2 takeover targets in '%s'.", region.lower())
            return region.lower()

    def valid_domain(self, domain: str) -> bool:
        """Determines a string is of valid domain format."""
        try:
            domain_re = r"^((?!-)[A-Za-z0-9-]{1,63}(?<!-)\.)+[A-Za-z]{2,63}\.?$"
            return bool(re.match(domain_re, domain))
        except TypeError:
            return False

    def get_ips(self, domain: str, ip_list: Optional[List[str]] = None) -> Optional[List[str]]:
        """Takes a domain and outputs any A records in the chain."""
        try:
            if ip_list is None:
                # https://docs.python-guide.org/writing/gotchas/#mutable-default-arguments
                ip_list = []
            socket.setdefaulttimeout(0.01)
            _, cnames, ips = socket.gethostbyname_ex(domain)
            if ips:
                ip_list.extend(ips)
            elif cnames:
                for dom in cnames:
                    self.get_ips(dom, ip_list)
            return ip_list
        except (socket.gaierror, socket.herror):
            return ip_list

    def clean_host(self, domain: str) -> Optional[List[Host]]:
        """Returns a domains and the IPs they map to as separate candidates."""
        if not self.valid_domain(domain):
            return None

        ip_list = self.get_ips(domain)

        if not ip_list:
            return None

        candidates = [Host(domain=domain, ip_address=ip) for ip in ip_list]
        return candidates

    def clean_hosts(self) -> List[Host]:
        """For all domains, return a list of distinct domain to IP mappings."""
        results: tqdm[Optional[List[Host]]]
        with futures.ThreadPoolExecutor(self.threads) as executor:
            results = tqdm(
                executor.map(self.clean_host, self.hosts),
                desc="Cleaning Input Domains",
                total=len(self.hosts),
                ncols=100,
            )
        cleaned_hosts: List[Host] = []
        for result in results:
            if result:
                cleaned_hosts.extend(result)

        return cleaned_hosts

    def get_inactive_hosts(self, hosts: List[Host]) -> List[Host]:
        masscan_input_file_location = f"{Configs.mastko_cache_location}/masscan_input_ips_file"
        nmap_input_file_location = f"{Configs.mastko_cache_location}/nmap_input_ips_file"
        try:
            """Scan top 100 ports for signs of life, mark hosts inactive no response."""
            log.info(f"Scanning {len(hosts)} hosts to identify inactive ones.")
            ips = [host.ip_address for host in hosts]
            with open(masscan_input_file_location, "w", encoding="utf-8") as masscan_input:
                masscan_input.write("\n".join([ip for ip in ips]))
            r_active_ips_ms = r"Discovered open port [0-9]{2,5}\/tcp on ([0-9\.\:]+)"
            masscan_command = [
                "sudo",
                "masscan",
                "--top-ports",
                "100",
                "--max-rate",
                "100000",
                "-iL",
                masscan_input_file_location,
            ]
            log.info(f"Running masscan command, might require password for sudo: {' '.join(masscan_command)}")
            with subprocess.Popen(masscan_command, stdout=subprocess.PIPE) as ms_proc:
                lofi_scan = str(ms_proc.stdout.read()) if ms_proc.stdout else ""
            active_ips = set(re.findall(r_active_ips_ms, lofi_scan))
            inactive_hosts = [host for host in hosts if host.ip_address not in active_ips]
            inactive_ips = {host.ip_address for host in inactive_hosts}
            with open(nmap_input_file_location, "w", encoding="utf-8") as nmap_input:
                nmap_input.write("\n".join([ip for ip in inactive_ips]))
            nmap_command = [
                "sudo",
                "nmap",
                "--max-retries",
                "3",
                "--host-timeout",
                "5m",
                "-T4",
                "-sn",
                "-iL",
                nmap_input_file_location,
            ]
            log.info(f"Running nmap command, might require password for sudo: {' '.join(nmap_command)}")
            r_active_ips_nm = r"Nmap scan report for .+?\(([0-9\.\:]+)\)"
            with subprocess.Popen(nmap_command, stdout=subprocess.PIPE) as nm_proc:
                hifi_scan = str(nm_proc.stdout.read()) if nm_proc.stdout else ""
            active_ips2 = set(re.findall(r_active_ips_nm, hifi_scan))
            inactive_hosts2 = [host for host in inactive_hosts if host.ip_address not in active_ips2]
            log.info(f"Detected {len(inactive_hosts2)} inactive hosts.")
            if not inactive_hosts2:
                raise NoTargetsFound("our scanner did not find any inactive hosts in the input file.")
            return inactive_hosts2
        except Exception as ex:
            if ex.__class__ != NoTargetsFound:
                err_msg = f"Error while scanning for inactive targets. Error: {ex}"
                log.exception(ex)
                raise TargetGeneratorException(err_msg)
            raise ex
        finally:
            os.remove(masscan_input_file_location)

    def create_target(self, inactive_host: Host) -> Optional[Target]:
        try:
            region = self.aws_cidr.find_alloc_group(inactive_host.ip_address)
            log.debug(f"{inactive_host.ip_address} is associated to {region}")
            if region:
                return Target(
                    domain=inactive_host.domain,
                    ip_address=inactive_host.ip_address,
                    region=region,
                )
            return None
        except Exception as ex:
            raise TargetGeneratorException(f"Error while creating a target, Error: {ex}")

    def load_targets(self, targets: List[Target]) -> None:
        try:
            if self.region is None:
                Target.insert_targets_to_db(list(targets))
            else:
                filtered_targets: List[Target] = []
                for target in targets:
                    if target.region == self.region:
                        filtered_targets.append(target)

                Target.insert_targets_to_db(filtered_targets)
        except Exception as ex:
            raise TargetGeneratorException(f"Error while loading targets to DB, Error: {ex}")

    def display_target_distribution(self, targets: List[Target]) -> None:
        """Prints a table with validated target count and thier repective AWS region."""
        target_map: Dict[str, int] = {}
        for target in targets:
            if target.region not in target_map:
                target_map[target.region] = 1
            else:
                target_map[target.region] += 1

        print("AWS REGION\t\tCOUNT OF Targets")
        for key, value in target_map.items():
            print(f"{key}\t\t{value}")

    def filter_targets_to_aws_region(self, targets: List[Target]) -> List[Target]:
        filtered_targets: List[Target] = []
        for target in targets:
            if target.region == self.region:
                filtered_targets.append(target)

        log.info(f"Filter: {len(filtered_targets)} found for {self.region} AWS Region")
        return filtered_targets

    def generate(self) -> List[Target]:
        try:
            cleaned_hosts = self.clean_hosts()
            inactive_hosts = self.get_inactive_hosts(cleaned_hosts)
            results: tqdm[Optional[Target]]
            with futures.ThreadPoolExecutor(self.threads) as executor:
                results = tqdm(
                    executor.map(self.create_target, inactive_hosts),
                    desc="Associating Domains to AWS Region",
                    total=len(inactive_hosts),
                    ncols=100,
                )

            list_of_targets: List[Target] = []
            for result in results:
                if result:
                    list_of_targets.append(result)

            if len(list_of_targets) > 0:
                self.display_target_distribution(list(list_of_targets))

            return list_of_targets
        except Exception as ex:
            log.error(ex)
            sys.exit(1)
