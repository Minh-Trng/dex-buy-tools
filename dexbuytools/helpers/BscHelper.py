from web3 import Web3
from web3.middleware import geth_poa_middleware
from dexbuytools.helpers.BaseHelper import BaseHelper
from data.bsc import chain_data


class BscHelper(BaseHelper):

    DEFAULT_DEX = "PCS" #PancakeSwap

    def __init__(self, dex_name=None):
        self.w3 = Web3(Web3.HTTPProvider('https://bsc-dataseed1.ninicoin.io/'))
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)

        self.dex = BaseHelper.get_dex_contract(
            self.w3,
            chain_data,
            BscHelper.DEFAULT_DEX if dex_name is None else dex_name
        )

    def buy_instantly(self, address, buy_params):
        raise NotImplementedError()

    def buy_on_liquidity(self, buy_params, address=None, search_name=None, search_symbol=None):
        raise NotImplementedError()


