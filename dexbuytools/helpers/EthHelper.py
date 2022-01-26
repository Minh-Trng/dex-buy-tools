from web3 import Web3
from web3.middleware import geth_poa_middleware

from dexbuytools import log_utils
from dexbuytools.helpers.EvmBaseHelper import EvmBaseHelper
import dexbuytools.config.general_params as general_params
from dexbuytools.helpers.data.eth import chain_data


class EthHelper(EvmBaseHelper):

    DEFAULT_DEX = "UNI"
    DEFAULT_RPC = general_params.ETH_RPC_URL

    def __init__(self, dex_name=None, custom_rpc=None):
        self.w3 = Web3(Web3.HTTPProvider(EthHelper.DEFAULT_RPC if custom_rpc is None else custom_rpc))

        self.dex = EvmBaseHelper.get_dex_contract(
            self.w3,
            chain_data,
            EthHelper.DEFAULT_DEX if dex_name is None else dex_name
        )

    def buy_instantly(self, token_address):
        receipt = super().perform_uniswap_style_buy(self.w3, self.dex, token_address)

        log_utils.log_info(f"buy performed. receipt: {receipt}")

    def buy_on_liquidity(self, buy_params, address=None, search_name=None, search_symbol=None):
        raise NotImplementedError()


