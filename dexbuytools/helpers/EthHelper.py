from web3 import Web3
from web3.middleware import geth_poa_middleware

from dexbuytools import log_utils
from dexbuytools.helpers.EvmBaseHelper import EvmBaseHelper
import dexbuytools.config as config
from dexbuytools.helpers.data.eth import chain_data


class EthHelper(EvmBaseHelper):

    DEFAULT_DEX = "UNI"

    def __init__(self, dex_name=None, custom_rpc=None):
        w3 = Web3(Web3.HTTPProvider(config.general_params['ETH_RPC_URL'] if custom_rpc is None else custom_rpc))

        super().__init__(w3, chain_data)

        self.dex_router = EvmBaseHelper.get_dex_router_contract(
            w3,
            chain_data,
            EthHelper.DEFAULT_DEX if dex_name is None else dex_name
        )

    def buy_instantly(self, token_address):
        try:
            receipt = super().perform_uniswapv2_style_buy(self.dex_router, token_address)
            log_utils.log_info(f"buy performed. receipt: {receipt}")
        except Exception as e:
            self._perform_uniswapv3_style_buy(token_address)

    def _perform_uniswapv3_style_buy(self, token_address):
        uniswapv3 = self.w3.eth.contract(
            abi=chain_data['ROUTER_ABI_UNIV3'],
            address=chain_data['ROUTER_ADDRESS_UNIV3']
        )

        raise NotImplementedError


    def buy_on_liquidity(self, buy_params, address=None, search_name=None, search_symbol=None):
        raise NotImplementedError()


