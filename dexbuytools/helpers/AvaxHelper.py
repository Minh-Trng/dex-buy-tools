from web3 import Web3
from web3.middleware import geth_poa_middleware
from dexbuytools.helpers.BaseHelper import BaseHelper
from dexbuytools.helpers.data.avax import chain_data


class AvaxHelper(BaseHelper):

    DEFAULT_DEX = "TJ"

    def __init__(self, dex_name=None):
        self.w3 = Web3(Web3.HTTPProvider('https://api.avax.network/ext/bc/C/rpc'))
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)

        self.dex = BaseHelper.get_dex_contract(
            self.w3,
            chain_data,
            AvaxHelper.DEFAULT_DEX if dex_name is None else dex_name
        )

    def buy_instantly(self, address, buy_params):
        raise NotImplementedError()

    def buy_on_liquidity(self, buy_params, address=None, search_name=None, search_symbol=None):
        raise NotImplementedError()


