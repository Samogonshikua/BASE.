import requests

from loguru import logger
from web3 import Web3

from config import ZERO_ADDRESS, BASE_TOKENS, ODOS_CONTRACT
from .account import Account


class Odos(Account):
    def __init__(self, account_id: int, private_key: str) -> None:
        super().__init__(account_id=account_id, private_key=private_key, chain="base")

    def quote(self, from_token: str, to_token: str, amount: int, slippage: float):
        url = "https://api.odos.xyz/sor/quote/v2"

        data = {
            "chainId": self.w3.eth.chain_id,
            "inputTokens": [
                {
                    "tokenAddress": Web3.to_checksum_address(from_token),
                    "amount": f"{amount}"
                }
            ],
            "outputTokens": [
                {
                    "tokenAddress": Web3.to_checksum_address(to_token),
                    "proportion": 1
                }
            ],
            "slippageLimitPercent": slippage,
            "userAddr": self.address,
            "referralCode": 4209167245 if ODOS_CONTRACT["use_ref"] is True else 0,
            "compact": True
        }

        response = requests.post(
            url=url,
            headers={"Content-Type": "application/json"},
            json=data
        )

        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"[{self.account_id}][{self.address}] Bad Odos request")

    def assemble(self, path_id):
        url = "https://api.odos.xyz/sor/assemble"

        data = {
            "userAddr": self.address,
            "pathId": path_id,
            "simulate": False,
        }

        response = requests.post(
            url=url,
            headers={"Content-Type": "application/json"},
            json=data
        )

        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"[{self.account_id}][{self.address}] Bad Odos request")

    def swap(
            self,
            from_token: str,
            to_token: str,
            min_amount: float,
            max_amount: float,
            decimal: int,
            slippage: float,
            all_amount: bool,
            min_percent: int,
            max_percent: int
    ):
        amount_wei, amount, balance = self.get_amount(
            from_token,
            min_amount,
            max_amount,
            decimal,
            all_amount,
            min_percent,
            max_percent
        )

        logger.info(
            f"[{self.account_id}][{self.address}] Swap on Odos – {from_token} -> {to_token} | {amount} {from_token}"
        )

        from_token = ZERO_ADDRESS if from_token == "ETH" else BASE_TOKENS[from_token]
        to_token = ZERO_ADDRESS if to_token == "ETH" else BASE_TOKENS[to_token]

        if from_token != ZERO_ADDRESS:
            self.approve(amount_wei, from_token, Web3.to_checksum_address(ODOS_CONTRACT["router"]))

        try:
            quote_data = self.quote(from_token, to_token, amount_wei, slippage)

            transaction_data = self.assemble(quote_data["pathId"])

            transaction = transaction_data["transaction"]

            transaction["chainId"] = self.w3.eth.chain_id

            transaction["value"] = int(transaction["value"])

            signed_txn = self.sign(transaction)

            txn_hash = self.send_raw_transaction(signed_txn)

            self.wait_until_tx_finished(txn_hash.hex())
        except Exception as e:
            logger.error(f"[{self.account_id}][{self.address}] Error | {e}")
