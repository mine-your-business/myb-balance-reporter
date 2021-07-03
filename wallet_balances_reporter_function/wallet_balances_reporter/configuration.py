import os


class Configuration:

    def __init__(self):
        self.coinbase_pro = CoinbasePro()
        self.celsius = CelsiusWallet()
        self.newrelic = NewRelic()


class CoinbasePro:

    def __init__(self):
        self.api_key = os.environ.get('CBP_API_KEY')
        self.api_key_passphrase = os.environ.get('CBP_API_KEY_PASSPHRASE')
        self.api_key_secret = os.environ.get('CBP_API_KEY_SECRET')


class CelsiusWallet:

    def __init__(self):
        self.api_key = os.environ.get('CELNET_API_KEY')
        self.partner_token = os.environ.get('CELNET_PARTNER_TOKEN')


class NewRelicInsights:

    def __init__(self):
        self.insert_api_key = os.environ.get('NEWRELIC_INSIGHTS_INSERT_API_KEY')
        self.query_api_url = os.environ.get('NEWRELIC_INSIGHTS_QUERY_API_URL')
        self.insert_api_url = os.environ.get('NEWRELIC_INSIGHTS_INSERT_API_URL')


class NewRelic:

    def __init__(self):
        self.account_id = os.environ.get('NEWRELIC_ACCOUNT_ID')
        self.insights = NewRelicInsights()
