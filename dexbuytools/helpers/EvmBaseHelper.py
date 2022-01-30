import abc
import time

import dexbuytools.config as config
from dexbuytools import log_utils


class EvmBaseHelper(abc.ABC):

    DEADLINE_OFFSET = 60*5 #5 minutes
    @abc.abstractmethod
    def buy_instantly(self, address):
        pass

    def perform_uniswapv2_style_buy(
            self,
            w3,
            dex_router,
            token_address,
            main_token_address,
            swap_method='swapExactETHForTokensSupportingFeeOnTransferTokens'):
        token_address = w3.toChecksumAddress(token_address)
        main_token_address = w3.toChecksumAddress(main_token_address)
        wallet_address = w3.toChecksumAddress(self._get_wallet_address_from_key(w3))
        amount_out_min = config.buy_params['AMOUNT_OUT_MIN']
        path = [main_token_address, token_address]
        to = wallet_address
        deadline = round(time.time()) + EvmBaseHelper.DEADLINE_OFFSET

        if config.buy_params['USE_WRAPPED_MAIN_TOKEN']:
            swap_method = 'swapExactTokensForTokensSupportingFeeOnTransferTokens'
            amount_in = int(config.buy_params['AMOUNT'] * 10 ** 18)
            tx = dex_router.functions[swap_method](
                amount_in,
                amount_out_min,
                path,
                to,
                deadline
            ).buildTransaction({
                'nonce': w3.eth.getTransactionCount(wallet_address),
                'gas': 3000000,
                'gasPrice': w3.eth.gas_price + config.buy_params['GAS_PRICE_BONUS']
            })
        else:
            tx = dex_router.functions[swap_method](
                amount_out_min,
                path,
                to,
                deadline
            ).buildTransaction({
                'value': int(config.buy_params['AMOUNT']*10**18),
                'nonce': w3.eth.getTransactionCount(wallet_address),
                'gasPrice': w3.eth.gas_price + config.buy_params['GAS_PRICE_BONUS']
            })

        gas_estimate = w3.eth.estimate_gas(tx)

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
    def get_dex_router_contract(w3, chain_data, dex_name):
        return w3.eth.contract(
            abi=chain_data[f"ROUTER_ABI_{dex_name}"],
            address=chain_data[f"ROUTER_ADDRESS_{dex_name}"]
        )