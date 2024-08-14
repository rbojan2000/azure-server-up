import logging

from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from src.config import Config
from src.paths import SETTINGS_PATH

logger = logging.getLogger(__name__)


def vm_start_task():
    config = Config.load(SETTINGS_PATH)

    compute_client = ComputeManagementClient(
        credential=DefaultAzureCredential(),
        subscription_id=config.azure.subscription_id,
    )

    script = [
        f"""
              sudo apt-get update
              sudo apt install docker.io --yes
              sudo groupadd docker
              sudo usermod -aG docker $USER
              newgrp docker
              docker login {config.container.registry.server} -p {config.container.registry.password} -u {config.container.registry.username}
              docker run -p 80:5000  {config.container.registry.image}
             """
    ]

    poller = compute_client.virtual_machines.begin_run_command(
        resource_group_name=config.azure.resource_group_name,
        vm_name=config.azure.vm.name,
        parameters={"command_id": "script", "script": script},
    )

    result = poller.result()

    print(result.value[0].message)


if __name__ == "__main__":
    vm_start_task()
