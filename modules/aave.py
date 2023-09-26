from loguru import logger
from web3 import Web3
from config import AAVE_CONTRACT, AAVE_WETH_CONTRACT, AAVE_ABI
from utils.sleeping import sleep
from .account import Account


class Aave(Account):
    def __init__(self, account_id: int, private_key: str) -> None:
        super().__init__(account_id=account_id, private_key=private_key, chain="base")

        self.contract = self.get_contract(AAVE_CONTRACT, AAVE_ABI)
        self.tx = {
            "chainId": self.w3.eth.chain_id,
            "from": self.address,
            "gasPrice": self.w3.eth.gas_price,
            "nonce": self.w3.eth.get_transaction_count(self.address),
        }

    def get_deposit_amount(self):
        aave_weth_contract = self.get_contract(AAVE_WETH_CONTRACT)

        amount = aave_weth_contract.functions.balanceOf(self.address).call()

        return amount

    def deposit(
            self,
            min_amount: float,
            max_amount: float,
            decimal: int,
            sleep_from: int,
            sleep_to: int,
            make_withdraw: bool,
            all_amount: bool,
            min_percent: int,
            max_percent: int
    ):
        amount_wei, amount, balance = self.get_amount(
            "ETH",
            min_amount,
            max_amount,
            decimal,
            all_amount,
            min_percent,
            max_percent
        )

        try:
            logger.info(f"[{self.account_id}][{self.address}] Make deposit on Aave | {amount} ETH")

            self.tx.update({"value": amount_wei})

            transaction = self.contract.functions.depositETH(
                Web3.to_checksum_address("0xA238Dd80C259a72e81d7e4664a9801593F98d1c5"),
                self.address,
                0
            ).build_transaction(self.tx)

            signed_txn = self.sign(transaction)

            txn_hash = self.send_raw_transaction(signed_txn)

            self.wait_until_tx_finished(txn_hash.hex())

            if make_withdraw:
                sleep(sleep_from, sleep_to)

                self.withdraw()
        except Exception as e:
            logger.error(f"[{self.account_id}][{self.address}] Error | {e}")

    def withdraw(self):
        amount = self.get_deposit_amount()

        if amount > 0:
            try:
                logger.info(
                    f"[{self.account_id}][{self.address}] Make withdraw from Aave | " +
                    f"{Web3.from_wei(amount, 'ether')} ETH"
                )

                self.tx.update({"value": 0, "nonce": self.w3.eth.get_transaction_count(self.address)})

                transaction = self.contract.functions.withdrawETH(
                    Web3.to_checksum_address("0xA238Dd80C259a72e81d7e4664a9801593F98d1c5"),
                    amount,
                    self.address
                ).build_transaction(self.tx)

                signed_txn = self.sign(transaction)

                txn_hash = self.send_raw_transaction(signed_txn)

                self.wait_until_tx_finished(txn_hash.hex())
            except Exception as e:
                logger.error(f"[{self.account_id}][{self.address}] Error | {e}")
        else:
            logger.error(f"[{self.account_id}][{self.address}] Deposit not found")
