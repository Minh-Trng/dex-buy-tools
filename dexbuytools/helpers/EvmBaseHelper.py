import abc
import time

import dexbuytools.config as config
from dexbuytools import log_utils
from dexbuytools.helpers.data.general import ERC20_ABI


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

            # for some reason estimating gas does not work for method 'swapExactTokensForTokensSupportingFeeOnTransferTokens'
            gas_estimate = w3.eth.estimate_gas(tx)
            if gas_estimate*tx['gasPrice'] > config.buy_params["MAX_GAS_ESTIMATE"] * 10**18:
                log_utils.log_error("Transaction not executed, because the gas estimate is greater than the limit "
                                    f"configured in the buy_params-file. Gas estimate in wei : {tx['gas']*tx['gasPrice']}")
                raise NotImplementedError

            tx['gas'] = gas_estimate + config.buy_params['GAS_LIMIT_BONUS']

        signed_tx = w3.eth.account.signTransaction(tx, private_key=config.wallet_data['PRIVATE_KEY'])
        tx_hash = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
        receipt = w3.eth.waitForTransactionReceipt(tx_hash)

        log_utils.log_info(f"buy of {token_address} performed on DEX {dex_router.address}. receipt: {receipt}")

        if config.buy_params['APPROVE_AFTER_BUY']:
            self._approve(w3, dex_router.address, token_address, wallet_address)

        return receipt

    def _approve(self, w3, dex_address, token_address, wallet_address):
        erc20_token = w3.eth.contract(
            abi=ERC20_ABI,
            address=token_address
        )

        amount_to_approve = erc20_token.functions.balanceOf(wallet_address).call()

        tx = erc20_token.functions.approve(dex_address, amount_to_approve).buildTransaction({
                'nonce': w3.eth.getTransactionCount(wallet_address),
                'gas': 300000, #arbitrary
                'gasPrice': w3.eth.gas_price + config.buy_params['GAS_PRICE_BONUS']
        })

        signed_tx = w3.eth.account.signTransaction(tx, private_key=config.wallet_data['PRIVATE_KEY'])
        tx_hash = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
        receipt = w3.eth.waitForTransactionReceipt(tx_hash)

        log_utils.log_info(f"approval given for dex {dex_address} to spend {amount_to_approve} of {token_address}. "
                           f"receipt: {receipt}")


    def _get_wallet_address_from_key(self, w3, value=None):
        return w3.eth.account.from_key(config.wallet_data['PRIVATE_KEY']).address

    def _get_overrides(self, w3, wallet_address):
        if w3.provider.endpoint_uri == config.general_params['ETH_RPC_URL']:
            w3.eth.fee_history(5, newest_block='latest', reward_percentiles=[10,90])
            priority_fee = w3.eth.max_priority_fee + config.buy_params['GAS_PRICE_BONUS']
            base_fee = 'TODO'
            return {
                'nonce': w3.eth.getTransactionCount(wallet_address),
                'type': 2, # EIP-1559
                'gas': 300000, # =gasLimit
                'maxPriorityFeePerGas': priority_fee,
                'maxFeePerGas': base_fee*2+priority_fee,
            }

        raise NotImplementedError

    @abc.abstractmethod
    def buy_on_liquidity(self, buy_params, address=None, search_name=None, search_symbol=None):
        pass

    @staticmethod
    def get_dex_router_contract(w3, chain_data, dex_name):
        return w3.eth.contract(
            abi=chain_data[f"ROUTER_ABI_{dex_name}"],
            address=chain_data[f"ROUTER_ADDRESS_{dex_name}"]
        )