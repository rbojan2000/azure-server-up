import logging
import sys

logging.basicConfig(
    format="[%(asctime)s] - [%(levelname)s] - [%(name)s] - %(message)s",
    level=logging.INFO,
    stream=sys.stdout,
)

logger_denylist = ["azure.core.pipeline.policies.http_logging_policy"]

for module in logger_denylist:
    logging.getLogger(module).setLevel(logging.ERROR)
