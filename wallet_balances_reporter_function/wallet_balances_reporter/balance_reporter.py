import json
import asyncio

from coinbase_pro import CoinbaseProApi
from newrelic import NewRelicInsightsApi
from celsius_network import CelsiusNetworkApi

from .configuration import Configuration
from .wallet_balance import WalletBalance, Wallet


class BalanceReporter:

    def __init__(
        self,
        config: Configuration,
        event_loop: asyncio.AbstractEventLoop,
        dry_run: bool
    ):
        self._newrelic = NewRelicInsightsApi(
            config.newrelic.account_id,
            config.newrelic.insights.insert_api_key,
            config.newrelic.insights.query_api_url,
            config.newrelic.insights.insert_api_url,
            verbose=True
        )
        self._coinbase_pro = CoinbaseProApi(
            config.coinbase_pro.api_key,
            config.coinbase_pro.api_key_secret,
            config.coinbase_pro.api_key_passphrase
        )
        self._celsius = CelsiusNetworkApi(
            celsius_partner_token=config.celsius.partner_token,
            user_api_key=config.celsius.api_key
        )
        self._currency_cache = {}
        self._event_loop = event_loop
        self.dry_run = dry_run

    async def _get_currency_price(self, cryptocurrency: str, pair: str):
        product_id = f'{cryptocurrency}-{pair}'
        try:
            stats = await self._event_loop.run_in_executor(
                None,
                self._coinbase_pro.get_24_hr_stats,
                product_id
            )
            last = stats.get('last')
            return float(last)
        except Exception as e:
            print(f'ERROR: Failed to get latest price for the {product_id} pair from Coinbase Pro - {str(e)}')

        return 0.0

    async def _get_currency_price_usd(self, currency: str):
        cryptocurrency = currency.upper()

        if cryptocurrency not in self._currency_cache:
            crypto_btc = await self._get_currency_price(cryptocurrency, 'BTC')
            btc_usd = self._currency_cache['BTC']
            self._currency_cache[cryptocurrency] = crypto_btc * btc_usd

        return self._currency_cache[cryptocurrency]

    async def _report_wallet_balance(self, wallet_balance: WalletBalance):
        event_type = 'WalletBalanceSnapshot'

        if self.dry_run:
            event_type = f'Test{event_type}'
        event = {
            'cryptocurrency': wallet_balance.crypto,
            'crypto_amount': wallet_balance.amount,
            'usd_equivalent': wallet_balance.usd_equivalent,
            'usd_price': wallet_balance.usd_price,
            'source': wallet_balance.source.name,
        }

        insert_result = await self._event_loop.run_in_executor(
            None,
            self._newrelic.insert_event,
            event_type,
            event
        )
        if insert_result:
            print(f'Successfully sent {event_type} event with data: {json.dumps(event, indent=2)}')
        else:
            print(f'Failed to send {event_type} event with data: {json.dumps(event, indent=2)}')

    async def _get_and_report(self, crypto: str, amount: float, wallet: Wallet):
        crypto_value = await self._get_currency_price_usd(crypto)
        if crypto_value == 0.0:
            return

        await self._report_wallet_balance(
            WalletBalance(
                crypto,
                amount,
                crypto_value,
                wallet
            )
        )

    async def report_coinbase_wallet_balances(self):
        accounts = await self._event_loop.run_in_executor(
            None,
            self._coinbase_pro.get_coinbase_accounts
        )

        reporting_tasks = []
        for account in accounts:
            balance = float(account['balance'])
            if balance == 0.0:
                continue

            crypto = account['currency']
            # Ignore 'fiat' accounts
            is_wallet = account['type'] == 'wallet'
            if not is_wallet:
                continue

            reporting_tasks.append(self._get_and_report(crypto, balance, Wallet.COINBASE))

        await asyncio.gather(*reporting_tasks)

    async def report_coinbase_pro_wallet_balances(self):
        accounts = await self._event_loop.run_in_executor(
            None,
            self._coinbase_pro.get_accounts
        )

        reporting_tasks = []
        for account in accounts:
            balance = float(account['balance'])
            if balance == 0.0:
                continue

            crypto = account['currency']
            # Ignore 'USD' account
            if crypto == 'USD':
                continue

            reporting_tasks.append(self._get_and_report(crypto, balance, Wallet.COINBASE_PRO))

        await asyncio.gather(*reporting_tasks)

    async def report_celsius_wallet_balances(self):
        balance_summary = await self._event_loop.run_in_executor(
            None,
            self._celsius.get_balance_summary
        )

        reporting_tasks = []
        if 'balance' in balance_summary:
            for crypto, str_amount in balance_summary['balance'].items():
                amount = float(str_amount)
                if amount == 0.0:
                    continue

                reporting_tasks.append(self._get_and_report(crypto, amount, Wallet.CELSIUS_NETWORK))

        await asyncio.gather(*reporting_tasks)

    async def process_reports_async(self):
        # Warm up the currency cache
        # Before the first time we get prices, get BTC-USD to populate the cache
        btc_usd = await self._get_currency_price('BTC', 'USD')
        self._currency_cache['BTC'] = btc_usd

        await asyncio.gather(
            self.report_coinbase_wallet_balances(),
            self.report_coinbase_pro_wallet_balances(),
            self.report_celsius_wallet_balances()
        )
