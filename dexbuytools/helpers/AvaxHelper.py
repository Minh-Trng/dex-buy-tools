from web3 import Web3
from web3.middleware import geth_poa_middleware

from dexbuytools import log_utils
import dexbuytools.config as config
from dexbuytools.helpers.EvmBaseHelper import EvmBaseHelper
from dexbuytools.helpers.data.avax import chain_data


class AvaxHelper(EvmBaseHelper):

    DEFAULT_DEX = "TJ"

    def __init__(self, dex_name=None, custom_rpc=None):
        w3 = Web3(Web3.HTTPProvider(config.general_params['AVAX_RPC_URL'] if custom_rpc is None else custom_rpc))
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)

        super().__init__(w3, chain_data)

        self.dex_router = EvmBaseHelper.get_dex_router_contract(
            self.w3,
            chain_data,
            AvaxHelper.DEFAULT_DEX if dex_name is None else dex_name
        )

    def buy_instantly(self, token_address):
        super().perform_uniswapv2_style_buy(self.w3, self.dex_router, token_address, chain_data["MAIN_TOKEN_ADDRESS"])

    def buy_on_liquidity(self, buy_params, address=None, search_name=None, search_symbol=None):
        raise NotImplementedError()


