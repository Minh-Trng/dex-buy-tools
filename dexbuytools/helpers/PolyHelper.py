from web3 import Web3
from web3.middleware import geth_poa_middleware

from dexbuytools import log_utils
from dexbuytools.helpers.EvmBaseHelper import EvmBaseHelper
from dexbuytools.helpers.data.poly import chain_data


class PolyHelper(EvmBaseHelper):

    DEFAULT_DEX = "QS"

    def __init__(self, config, dex_name=None, custom_rpc=None):
        w3 = Web3(Web3.HTTPProvider(config.general_params['POLY_RPC_URL'] if custom_rpc is None else custom_rpc))
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)

        dex_name = PolyHelper.DEFAULT_DEX if dex_name is None else dex_name
        super().__init__(w3, chain_data, dex_name, config)

    def buy_instantly(self, token_address):
        super().perform_uniswapv2_style_buy(token_address)


    def buy_on_liquidity(self, buy_params, address=None, search_name=None, search_symbol=None):
        raise NotImplementedError()


