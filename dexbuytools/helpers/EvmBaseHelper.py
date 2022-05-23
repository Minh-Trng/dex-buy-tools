import abc
import json
import time

from eth_account import messages
from web3 import Web3
from dexbuytools import log_utils
from dexbuytools.helpers.data.general import ERC20_ABI, UNISWAP_V2_FACTORY_ABI, UNISWAP_V2_PAIR_ABI
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

        liquidity_requirements_passed = self._check_liquidity_requirements(token_address)
        if not liquidity_requirements_passed:
            return None

        wallet_address = self.w3.toChecksumAddress(self._get_wallet_address_from_key())

        tx = self.build_uniswapv2_style_tx(token_address, wallet_address, swap_method)

        signed_tx = self.w3.eth.account.signTransaction(tx, private_key=self.config.wallet_data['PRIVATE_KEY'])
        tx_hash = self.w3.eth.sendRawTransaction(signed_tx.rawTransaction)
        receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)

        log_utils.log_info(f"buy of {token_address} performed on DEX {self.dex_router.address}. receipt: {receipt}")

        if self.config.buy_params['APPROVE_AFTER_BUY']:
            self._approve(self.w3, self.dex_router.address, token_address, wallet_address)

        return receipt

    def _check_liquidity_requirements(self, token_address):
        factory = self.w3.eth.contract(abi=UNISWAP_V2_FACTORY_ABI, address=self.dex_router.functions.factory().call())
        pair_address = factory.functions.getPair(self.chain_data['MAIN_TOKEN_ADDRESS'], token_address).call()
        pair_contract = self.w3.eth.contract(abi=UNISWAP_V2_PAIR_ABI, address=pair_address)
        reserves = pair_contract.functions.getReserves().call()

        if pair_contract.functions.token0().call().lower() == self.chain_data['MAIN_TOKEN_ADDRESS'].lower():
            main_token_reserves, token_reserves = reserves[0], reserves[1]
        else:
            main_token_reserves, token_reserves = reserves[1], reserves[0]

        main_token_contract = self.w3.eth.contract(abi=ERC20_ABI, address=self.chain_data['MAIN_TOKEN_ADDRESS'])
        main_token_decimals = main_token_contract.functions.decimals().call()
        if main_token_reserves//main_token_decimals < self.config.buy_params['MIN_AMOUNT_OF_LIQUIDITY']:
            log_utils.log_info(f'The amount of {main_token_contract.functions.name().call()} provided as liquidity for '
                               f'token {token_address} is lower than the value of MIN_AMOUNT_OF_LIQUIDITY '
                               f'specified in buy_params')
            return False

        token_contract = self.w3.eth.contract(abi=ERC20_ABI, address=token_address)
        total_supply = token_contract.functions.totalSupply().call()

        percentage_of_supply_in_liq = token_reserves/total_supply*100

        if (percentage_of_supply_in_liq < self.config.buy_params['MIN_PERCENTAGE_OF_TOTAL_SUPPLY_IN_LIQUIDITY'] or
                percentage_of_supply_in_liq > self.config.buy_params['MAX_PERCENTAGE_OF_TOTAL_SUPPLY_IN_LIQUIDITY']):
            log_utils.log_info(f'The percentage of the total supply of token {token_address} provided to the pool is '
                               f'not within the min/max values specified with '
                               f'MIN(MAX)_PERCENTAGE_OF_TOTAL_SUPPLY_IN_LIQUIDITY')
            return False

        return True

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

    #REVIEW: this method is in need for refactoring. also should be made async, so tests can be run
    def buy_on_liquidity(self, search_address=None, search_term=None):
        latest_blocknumber = self.w3.eth.block_number
        while True:
            try:
                while latest_blocknumber < self.w3.eth.block_number:
                    latest_blocknumber = latest_blocknumber + 1
                    block = self.w3.eth.get_block(latest_blocknumber, full_transactions=True)

                    router_txs = [x for x in block['transactions'] if x['to'] == self.dex_router.address]

                    for tx in router_txs:
                        decoded_input = self.dex_router.decode_function_input(tx['input'])
                        token_address = None
                        func_name = decoded_input[0].fn_name
                        func_args = decoded_input[1]
                        if func_name == 'addLiquidity':
                            if func_args['tokenA'] == self.chain_data['MAIN_TOKEN_ADDRESS']:
                                token_address = func_args['tokenB']
                            elif func_args['tokenB'] == self.chain_data['MAIN_TOKEN_ADDRESS']:
                                token_address = func_args['tokenA']
                        elif 'addLiquidity' in func_name: # addLiquidityETH or addLiquidityAVAX
                            token_address = func_args['token']

                        if token_address is not None:
                            if search_address is not None:
                                if self.w3.toChecksumAddress(token_address) == self.w3.toChecksumAddress(search_address):
                                    self.perform_uniswapv2_style_buy(token_address)

                            if search_term is not None:
                                token_contract = self.w3.eth.contract(abi=ERC20_ABI, address=token_address)
                                token_name = token_contract.functions.name().call().lower()
                                token_symbol = token_contract.functions.symbol().call().lower()
                                if search_term in token_name or search_term in token_symbol:
                                    self.perform_uniswapv2_style_buy(token_address)

            except Exception as e:
                print(e)

            time.sleep(1)

    def _get_dex_router_contract(self, dex_name):
        return self.w3.eth.contract(
            abi=self.chain_data[f"ROUTER_ABI_{dex_name}"],
            address=self.chain_data[f"ROUTER_ADDRESS_{dex_name}"]
        )