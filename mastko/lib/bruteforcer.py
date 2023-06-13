import time
from datetime import datetime
from typing import Dict, List, Mapping, Sequence

from mastko.config.configs import Configs
from mastko.data.ec2 import Ec2
from mastko.data.eip import EIP
from mastko.data.target import Target
from mastko.lib.ec2_client import Ec2Client
from mastko.lib.exceptions import BruteforcerException
from mastko.lib.logger import get_logger

log = get_logger("mastko.lib.bruteforcer")


class Bruteforcer:
    """
    The Bruteforcer is capable of rotating the public IP on AWS EC2 and comparing against target list to
    check for takeovers.
    """

    def __init__(self, targets: Sequence[Target], region: str, instance_id: str, eip_ip: str):
        self.targets = targets
        self.target_hash = self._get_targets_grouped_by_ip(self.targets)
        self.region = region
        self.ec2_client = Ec2Client(aws_region=self.region)
        self.ec2 = Ec2(instance_id=instance_id)
        self.eip = self.ec2_client.get_eip(eip_ip)

    def _get_targets_grouped_by_ip(self, targets: Sequence[Target]) -> Mapping[str, Sequence[Target]]:
        target_hash: Dict[str, List[Target]] = {}
        for target in targets:
            if target.ip_address not in target_hash:
                target_hash[target.ip_address] = []

            target_hash[target.ip_address].append(target)

        return target_hash

    def rotate_ip(self, ec2_instance_id: str, eip_allocation_id: str) -> None:
        try:
            eip_association_id = self.ec2_client.associate_eip(
                ec2_instance_id=ec2_instance_id, eip_id=eip_allocation_id
            )
            self.ec2_client.disassociate_eip(eip_association_id=eip_association_id)
        except Exception:
            for attempt in range(Configs.aws_api_retry_count):
                try:
                    log.warning("Failed to rotate IP, trying again.")
                    log.info(f"sleeping for {attempt * 2} seconds")
                    time.sleep(attempt * 2)
                    eip_association_id = self.ec2_client.associate_eip(
                        ec2_instance_id=ec2_instance_id, eip_id=eip_allocation_id
                    )
                    self.ec2_client.disassociate_eip(eip_association_id=eip_association_id)
                except Exception as err:
                    if attempt == Configs.aws_api_retry_count - 1:
                        message = (
                            f"Failed to rotate IP for ec2_instance_id: {ec2_instance_id}, "
                            f"eip_allocation_id: {eip_allocation_id}. ERROR: {err}"
                        )
                        log.error(message)
                        log.exception(err)
                        raise BruteforcerException(message)
                else:
                    break

    def _is_takeover(self, ec2_public_ip: str) -> bool:
        return ec2_public_ip in self.target_hash

    def _attempt_takeover(self, ec2: Ec2, eip: EIP) -> str:
        self.rotate_ip(ec2.instance_id, eip.allocation_id)
        return self.ec2_client.get_ec2_public_ip(ec2.instance_id)

    def _process_successful_takeover(self, ec2: Ec2, takeover_ip: str) -> None:
        self.ec2_client.rename_ec2_instance(ec2.instance_id, Configs.successful_takeover_ec2_name)
        successful_takeover_targets = self.target_hash[takeover_ip]
        associated_dns_names = [target.domain for target in successful_takeover_targets]
        tags = []
        for index in range(len(associated_dns_names)):
            log.info(
                f"SUCCESSFUL TAKEOVER. takeover_ip: {takeover_ip}, "
                f"target: {associated_dns_names[index]}, ec2 used: {ec2}"
            )
            tags.append({"Key": f"domain_{index}", "Value": associated_dns_names[index]})
        self.ec2_client.tag_instance(instance_id=ec2.instance_id, tags=tags)

    def run(self, iterations: int) -> None:
        try:
            iteration_counter: int = 0
            start_time: datetime = datetime.now().replace(microsecond=0)
            while iteration_counter < iterations:
                new_ip = self._attempt_takeover(self.ec2, self.eip)

                if self._is_takeover(new_ip):
                    log.info(
                        f"SUCESSFULL ATTEMPT, takeover match found. ec2_used: {self.ec2}, public_ip: {new_ip}"
                    )
                    self._process_successful_takeover(self.ec2, new_ip)
                    return  # exit on success
                else:
                    log.info(f"Unsuccessful attempt, ec2_used: {self.ec2}, public_ip_used: {new_ip}")

                iteration_counter += 1
            end_time: datetime = datetime.now().replace(microsecond=0)
            log.info(
                f"MasTKO finished executing {iterations} iterations in {end_time - start_time} (HH:MM:SS)"
                " time."
            )
        except Exception as ex:
            message = f"Exception caught in bruteforce handler, error: {ex}"
            log.error(message)
            log.exception(ex)
            raise BruteforcerException(message)
