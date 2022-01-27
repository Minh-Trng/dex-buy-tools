import abc
import time

import dexbuytools.config as config
from dexbuytools import log_utils


class EvmBaseHelper(abc.ABC):

    DEADLINE_OFFSET = 60*5 #5 minutes
    @abc.abstractmethod
    def buy_instantly(self, address):
        pass

    def perform_uniswapv2_style_buy(self, w3, dex, token_address, main_token_address):
        token_address = w3.toChecksumAddress(token_address)
        wallet_address = self._get_wallet_address_from_key(w3)
        amount_out_min = 1
        path = [main_token_address, token_address]
        to = wallet_address
        deadline = round(time.time()) + EvmBaseHelper.DEADLINE_OFFSET

        tx = dex.functions.swapExactETHForTokensSupportingFeeOnTransferTokens(
            amount_out_min,
            path,
            to,
            deadline
        ).buildTransaction({
            'value': int(config.buy_params['AMOUNT']*10**18),
            'nonce': w3.eth.getTransactionCount(wallet_address),
            'gasPrice': w3.eth.gas_price + config.buy_params['GAS_PRICE_BONUS']
        })
        gas_estimate = w3.eth.estimateGas(tx)

        if gas_estimate*tx['gasPrice'] > config.buy_params["MAX_GAS_ESTIMATE"] * 10**18:
            log_utils.log_error("Transaction not executed, because the gas estimate is greater than the limit "
                                f"configured in the buy_params-file. Gas estimate in wei : {tx['gas']*tx['gasPrice']}")
            raise NotImplementedError

        tx['gas'] = gas_estimate + config.buy_params['GAS_LIMIT_BONUS']
        signed_tx = w3.eth.account.signTransaction(tx, private_key=config.wallet_data['PRIVATE_KEY'])
        tx_hash = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
        return w3.eth.waitForTransactionReceipt(tx_hash)

    @abc.abstractmethod
    def buy_on_liquidity(self, buy_params, address=None, search_name=None, search_symbol=None):
        pass

    def _get_wallet_address_from_key(self, w3):
        return w3.eth.account.from_key(config.wallet_data['PRIVATE_KEY']).address

    @staticmethod
    def get_dex_contract(w3, chain_data, dex_name):
        return w3.eth.contract(
            abi=chain_data[f"ROUTER_ABI_{dex_name}"],
            address=chain_data[f"ROUTER_ADDRESS_{dex_name}"]
        )