
from loguru import logger
from web3 import Web3
from .account import Account
from config import ORBITER_CONTRACT


class Orbiter(Account):
    def __init__(self, account_id: int, private_key: str, chain: str) -> None:
        super().__init__(account_id=account_id, private_key=private_key, chain=chain)

        self.bridge_codes = {
            "ethereum": 9001,
            "arbitrum": 9002,
            "polygon": 9006,
            "optimism": 9007,
            "zksync": 9014,
            "bsc": 9015,
            "nova": 9016,
            "zkevm": 9017,
            "base": 9021,
        }

    def get_tx_data(self, value: float, destination_chain: str):
        amount = int(Web3.to_wei(value, "ether") + self.bridge_codes[destination_chain])

        tx = {
            "chainId": self.w3.eth.chain_id,
            "nonce": self.w3.eth.get_transaction_count(self.address),
            "to": Web3.to_checksum_address(ORBITER_CONTRACT),
            "value": amount,
            "gasPrice": self.w3.eth.gas_price,
            "from": self.address
        }
        return tx

    def bridge(
        self,
        destination_chain: str,
        min_amount: float,
        max_amount: float,
        decimal: int,
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

        if amount < 0.005 or amount > 5:
            logger.error(
                f"[{self.account_id}][{self.address}] Limit range amount for bridge 0.005 – 5 ETH | {amount} ETH"
            )
        else:
            logger.info(f"[{self.account_id}][{self.address}] Bridge {self.chain} –> {destination_chain} | {amount} ETH")

            tx_data = self.get_tx_data(amount, destination_chain)
            balance = self.w3.eth.get_balance(self.address)

            if tx_data["value"] >= balance:
                logger.error(f"[{self.account_id}][{self.address}] Insufficient funds!")
            else:
                gas_limit = self.w3.eth.estimate_gas(tx_data)
                tx_data.update({'gas': gas_limit})

                signed_txn = self.sign(tx_data)

                txn_hash = self.send_raw_transaction(signed_txn)

                self.wait_until_tx_finished(txn_hash.hex())
