import logging
import os
from typing import Tuple

import paramiko
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient
from dynaconf import Dynaconf
from src.config import Config
from src.paths import SETTINGS_PATH

logger = logging.getLogger(__name__)


def infrastructure_setup():
    config = Config.load(SETTINGS_PATH)

    private_key_path, public_key_path = generate_ssh_keys(config)

    logger.info("SSH keys have been generated")
    logger.info(f"Private key: {private_key_path}")
    logger.info(f"Public key: {public_key_path}")

    resource_client = ResourceManagementClient(
        credential=DefaultAzureCredential(),
        subscription_id=config.azure.subscription_id,
    )

    resource_client = provide_resource_group(config, resource_client)
    logger.info(
        f"Provisioned resource group {resource_client.name} in the {resource_client.location} region"
    )

    network_client = NetworkManagementClient(
        credential=DefaultAzureCredential(),
        subscription_id=config.azure.subscription_id,
    )

    vn_name, vn_address_prefixes = provide_virtual_network(config, network_client)
    logger.info(
        f"Provisioned virtual network {vn_name} with address prefixes {vn_address_prefixes}"
    )

    subnet_name, subnet_address_prefix, subnet_id = provide_subnet(
        config, network_client
    )
    logger.info(
        f"Provisioned virtual subnet {subnet_name} with address prefix {subnet_address_prefix}"
    )

    ip_address_name, ip_address, ip_address_id = provide_public_ip_address(
        config, network_client
    )
    logger.info(
        f"Provisioned public IP address {ip_address_name} with address {ip_address}"
    )

    nsg_name, nsg_id = provide_security_group(config, network_client)
    logger.info(f"Provisioned Network Security Group {nsg_name}")

    nic_client_name, nic_id = provide_nic_client(
        config, network_client, subnet_id, ip_address_id, nsg_id
    )
    logger.info(f"Provisioned network interface client {nic_client_name}")

    compute_client = ComputeManagementClient(
        credential=DefaultAzureCredential(),
        subscription_id=config.azure.subscription_id,
    )
    vm_name = provide_virtual_machine(config, compute_client, nic_id)
    logger.info(f"Provisioned virtual machine {vm_name}")


def generate_ssh_keys(config: Dynaconf) -> Tuple[str, str]:
    # Define paths for the keys
    private_key_path = os.path.expanduser(path=config.ssh.key.path.private)
    public_key_path = private_key_path + ".pub"

    # Ensure the .ssh directory exists
    os.makedirs(os.path.dirname(private_key_path), exist_ok=True)

    # Generate a new RSA key pair
    key = paramiko.RSAKey.generate(2048)

    # Save the private key
    with open(private_key_path, "w") as private_key_file:
        key.write_private_key(private_key_file)
        os.chmod(private_key_path, 0o600)

    # Save the public key
    with open(public_key_path, "w") as public_key_file:
        public_key_file.write(f"{key.get_name()} {key.get_base64()}\n")

    return private_key_path, public_key_path


def provide_resource_group(
    config: Dynaconf, resource_client: ResourceManagementClient
) -> ResourceManagementClient:
    rg_result = resource_client.resource_groups.create_or_update(
        resource_group_name=config.azure.resource_group_name,
        parameters={"location": config.azure.location},
    )
    return rg_result


def provide_virtual_network(
    config: Dynaconf, network_client: NetworkManagementClient
) -> Tuple[str, str]:
    poller = network_client.virtual_networks.begin_create_or_update(
        resource_group_name=config.azure.resource_group_name,
        virtual_network_name=config.azure.vnet.name,
        parameters={
            "location": config.azure.location,
            "address_space": {"address_prefixes": [config.azure.vnet.address_prefixes]},
        },
    )
    vnet_result = poller.result()

    return vnet_result.name, vnet_result.address_space.address_prefixes


def provide_subnet(
    config: Dynaconf, network_client: NetworkManagementClient
) -> Tuple[str, str, str]:
    poller = network_client.subnets.begin_create_or_update(
        resource_group_name=config.azure.resource_group_name,
        virtual_network_name=config.azure.vnet.name,
        subnet_name=config.azure.subnet.name,
        subnet_parameters={"address_prefix": config.azure.subnet.address_prefix},
    )
    subnet_result = poller.result()
    return subnet_result.name, subnet_result.address_prefix, subnet_result.id


def provide_public_ip_address(
    config: Dynaconf, network_client: NetworkManagementClient
) -> Tuple[str, str, str]:
    poller = network_client.public_ip_addresses.begin_create_or_update(
        resource_group_name=config.azure.resource_group_name,
        public_ip_address_name=config.azure.public.ip.name,
        parameters={
            "location": config.azure.location,
            "sku": {"name": config.azure.public.ip.sku},
            "public_ip_allocation_method": config.azure.public.ip.allocation_method,
            "public_ip_address_version": "IPV4",
        },
    )
    ip_address_result = poller.result()
    return ip_address_result.name, ip_address_result.ip_address, ip_address_result.id


def provide_security_group(
    config: Dynaconf, network_client: NetworkManagementClient
) -> Tuple[str, str]:
    poller = network_client.network_security_groups.begin_create_or_update(
        resource_group_name=config.azure.resource_group_name,
        network_security_group_name=config.azure.nsg.name,
        parameters={
            "location": config.azure.location,
            "security_rules": [
                {
                    "name": "Allow-SSH",
                    "properties": {
                        "protocol": "*",
                        "sourcePortRange": "*",
                        "destinationPortRange": "22",
                        "sourceAddressPrefix": "*",
                        "destinationAddressPrefix": "*",
                        "access": "Allow",
                        "priority": 4000,
                        "direction": "Inbound",
                    },
                },
                {
                    "name": "Allow-HTTP",
                    "properties": {
                        "protocol": "*",
                        "sourcePortRange": "*",
                        "destinationPortRange": "80",
                        "sourceAddressPrefix": "*",
                        "destinationAddressPrefix": "*",
                        "access": "Allow",
                        "priority": 4001,
                        "direction": "Inbound",
                    },
                },
            ],
        },
    )

    nsg_result = poller.result()
    return nsg_result.name, nsg_result.id


def provide_nic_client(
    config, network_client, subnet_id, ip_address_id, nsg_id
) -> Tuple[str, str]:
    poller = network_client.network_interfaces.begin_create_or_update(
        resource_group_name=config.azure.resource_group_name,
        network_interface_name=config.azure.public.nic.name,
        parameters={
            "location": config.azure.location,
            "ip_configurations": [
                {
                    "name": config.azure.public.ip.config_name,
                    "subnet": {"id": subnet_id},
                    "public_ip_address": {"id": ip_address_id},
                }
            ],
            "network_security_group": {"id": nsg_id},
        },
    )

    nic_result = poller.result()
    return nic_result.name, nic_result.id


def provide_virtual_machine(
    config: Dynaconf, compute_client: ComputeManagementClient, nic_id: str
) -> str:
    # Read the SSH public key
    with open(os.path.expanduser(config.ssh.key.path.public), "r") as f:
        ssh_key_data = f.read()

    poller = compute_client.virtual_machines.begin_create_or_update(
        resource_group_name=config.azure.resource_group_name,
        vm_name=config.azure.vm.name,
        parameters={
            "location": config.azure.location,
            "storage_profile": {
                "image_reference": {
                    "publisher": "Canonical",
                    "offer": "UbuntuServer",
                    "sku": config.azure.vm.image.sku,
                    "version": config.azure.vm.image.version,
                }
            },
            "hardware_profile": {"vm_size": config.azure.vm.size},
            "os_profile": {
                "computer_name": config.azure.vm.name,
                "admin_username": config.azure.vm.credentials.username,
                "admin_password": config.azure.vm.credentials.password,
                "linux_configuration": {
                    "disable_password_authentication": True,
                    "ssh": {
                        "public_keys": [
                            {
                                "path": f"/home/{config.azure.vm.credentials.username}/.ssh/authorized_keys",
                                "key_data": ssh_key_data,
                            }
                        ]
                    },
                },
            },
            "network_profile": {
                "network_interfaces": [
                    {
                        "id": nic_id,
                    }
                ]
            },
        },
    )
    vm_result = poller.result()
    return vm_result.name


if __name__ == "__main__":
    infrastructure_setup()
