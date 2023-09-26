import random

from loguru import logger
from utils.sleeping import sleep
from .account import Account


class Routes(Account):
    def __init__(self, account_id: int, private_key: str) -> None:
        super().__init__(account_id=account_id, private_key=private_key, chain="base")

    def start(self, use_modules: list, sleep_from: int, sleep_to: int, random_module: bool):
        logger.info(f"[{self.account_id}][{self.address}] Start using routes")

        for _ in range(0, len(use_modules)):
            if random_module:
                module = random.choice(use_modules)

                use_modules.remove(module)
            else:
                module = use_modules[_]

            module = random.choice(module) if type(module) is list else module

            module(self.account_id, self.private_key)

            sleep(sleep_from, sleep_to)
