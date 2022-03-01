import abc
import json
import time

from eth_account import messages
from web3 import Web3
from dexbuytools import log_utils
from dexbuytools.helpers.data.general import ERC20_ABI
from dexbuytools.helpers.data.eth import chain_data as eth_chain_data
from eth_account.account import Account
import requests


class EvmBaseHelper(abc.ABC):

    def __init__(self, w3, chain_data, dex_name, config):
        self.w3 = w3
        self.chain_data = chain_data
        self.config = config
        self.dex_router = self._get_dex_router_contract(dex_name)

    @abc.abstractmethod
    def buy_instantly(self, token_address):
        pass

    def build_uniswapv2_style_tx(self, token_address, wallet_address, swap_method='swapExactETHForTokensSupportingFeeOnTransferTokens'):
        token_address = self.w3.toChecksumAddress(token_address)
        main_token_address = self.w3.toChecksumAddress(self.chain_data['MAIN_TOKEN_ADDRESS'])
        amount_out_min = self.config.buy_params['AMOUNT_OUT_MIN']
        path = [main_token_address, token_address]
        to = wallet_address
        deadline = round(time.time()) + self.config.buy_params['DEADLINE_OFFSET']

        if self.config.buy_params['USE_WRAPPED_MAIN_TOKEN']:
            swap_method = 'swapExactTokensForTokensSupportingFeeOnTransferTokens'
            amount_in = int(self.config.buy_params['AMOUNT'] * 10 ** 18)
            tx = self.dex_router.functions[swap_method](
                amount_in,
                amount_out_min,
                path,
                to,
                deadline
            ).buildTransaction({
                'nonce': self.w3.eth.getTransactionCount(wallet_address),
                'gas': 3000000,
                'gasPrice': self.w3.eth.gas_price + self.config.buy_params['GAS_PRICE_BONUS']
            })
        else:
            tx = self.dex_router.functions[swap_method](
                amount_out_min,
                path,
                to,
                deadline
            ).buildTransaction({
                'value': int(self.config.buy_params['AMOUNT'] * 10 ** 18),
                'nonce': self.w3.eth.getTransactionCount(wallet_address),
                'gasPrice': self.w3.eth.gas_price + self.config.buy_params['GAS_PRICE_BONUS']
            })

            # for some reason estimating gas does not work for method 'swapExactTokensForTokensSupportingFeeOnTransferTokens'
            gas_estimate = self.w3.eth.estimate_gas(tx)
            if gas_estimate * tx['gasPrice'] > self.config.buy_params["MAX_GAS_ESTIMATE"] * 10 ** 18:
                log_utils.log_error("Transaction not executed, because the gas estimate is greater than the limit "
                                    f"configured in the buy_params-file. Gas estimate in wei : {tx['gas'] * tx['gasPrice']}")
                raise NotImplementedError

            tx['gas'] = gas_estimate + self.config.buy_params['GAS_LIMIT_BONUS']

        return tx

    def perform_uniswapv2_style_buy(
            self,
            token_address,
            swap_method='swapExactETHForTokensSupportingFeeOnTransferTokens'):

        wallet_address = self.w3.toChecksumAddress(self._get_wallet_address_from_key())

        tx = self.build_uniswapv2_style_tx(token_address, wallet_address, swap_method)

        signed_tx = self.w3.eth.account.signTransaction(tx, private_key=self.config.wallet_data['PRIVATE_KEY'])
        tx_hash = self.w3.eth.sendRawTransaction(signed_tx.rawTransaction)
        receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)

        log_utils.log_info(f"buy of {token_address} performed on DEX {self.dex_router.address}. receipt: {receipt}")

        if self.config.buy_params['APPROVE_AFTER_BUY']:
            self._approve(self.w3, self.dex_router.address, token_address, wallet_address)

        return receipt

    def _approve(self, w3, dex_address, token_address, wallet_address):
        erc20_token = w3.eth.contract(
            abi=ERC20_ABI,
            address=token_address
        )

        amount_to_approve = erc20_token.functions.balanceOf(wallet_address).call()

        tx = erc20_token.functions.approve(dex_address, amount_to_approve).buildTransaction({
            'nonce': w3.eth.getTransactionCount(wallet_address),
            'gas': 300000,  # arbitrary
            'gasPrice': w3.eth.gas_price + self.config.buy_params['GAS_PRICE_BONUS']
        })

        signed_tx = w3.eth.account.signTransaction(tx, private_key=self.config.wallet_data['PRIVATE_KEY'])
        tx_hash = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
        receipt = w3.eth.waitForTransactionReceipt(tx_hash)

        log_utils.log_info(f"approval given for dex {dex_address} to spend {amount_to_approve} of {token_address}. "
                           f"receipt: {receipt}")

    def _get_wallet_address_from_key(self):
        return self.w3.eth.account.from_key(self.config.wallet_data['PRIVATE_KEY']).address

    @abc.abstractmethod
    def buy_on_liquidity(self, buy_params, address=None, search_name=None, search_symbol=None):
        pass

    def _get_dex_router_contract(self, dex_name):
        return self.w3.eth.contract(
            abi=self.chain_data[f"ROUTER_ABI_{dex_name}"],
            address=self.chain_data[f"ROUTER_ADDRESS_{dex_name}"]
        )