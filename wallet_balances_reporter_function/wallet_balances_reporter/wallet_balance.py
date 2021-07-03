from .wallet import Wallet


class WalletBalance:

    def __init__(
        self,
        crypto: str,
        amount: float,
        usd_price: float,
        source: Wallet
    ):
        self.crypto = crypto.upper() if crypto else crypto
        self.amount = amount
        self.usd_price = usd_price
        self.usd_equivalent = amount * usd_price
        self.source = source
