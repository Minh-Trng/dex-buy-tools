from web3 import Web3
from web3.middleware import geth_poa_middleware
from dexbuytools.helpers.BaseHelper import BaseHelper
import dexbuytools.config.general_params as general_params
from dexbuytools.helpers.data.eth import chain_data


class EthHelper(BaseHelper):

    DEFAULT_DEX = "UNI"

    def __init__(self, dex_name=None):
        self.w3 = Web3(Web3.HTTPProvider(general_params.ETH_RPC_URL))

        self.dex = BaseHelper.get_dex_contract(
            self.w3,
            chain_data,
            EthHelper.DEFAULT_DEX if dex_name is None else dex_name
        )

    def buy_instantly(self, address, buy_params):
        raise NotImplementedError()

    def buy_on_liquidity(self, buy_params, address=None, search_name=None, search_symbol=None):
        raise NotImplementedError()


