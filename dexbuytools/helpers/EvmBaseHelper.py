import abc
import json
import time

from eth_account import messages
from web3 import Web3

import dexbuytools.config as config
from dexbuytools import log_utils
from dexbuytools.helpers.data.general import ERC20_ABI
from dexbuytools.helpers.data.eth import chain_data as eth_chain_data
from eth_account.account import Account
import requests


class EvmBaseHelper(abc.ABC):
    DEADLINE_OFFSET = config.buy_params['DEADLINE_OFFSET']

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
            ).buildTransaction(self._get_tx_params(w3, wallet_address, {
                'nonce': w3.eth.getTransactionCount(wallet_address),
                'gas': 3000000,
                'gasPrice': w3.eth.gas_price + config.buy_params['GAS_PRICE_BONUS']
            }))
        else:
            tx = dex_router.functions[swap_method](
                amount_out_min,
                path,
                to,
                deadline
            ).buildTransaction(self._get_tx_params(w3, wallet_address, {
                'value': int(config.buy_params['AMOUNT'] * 10 ** 18),
                'nonce': w3.eth.getTransactionCount(wallet_address),
                'gasPrice': w3.eth.gas_price + config.buy_params['GAS_PRICE_BONUS']
            }))

            # for some reason estimating gas does not work for method 'swapExactTokensForTokensSupportingFeeOnTransferTokens'
            gas_estimate = w3.eth.estimate_gas(tx)
            if gas_estimate * tx['gasPrice'] > config.buy_params["MAX_GAS_ESTIMATE"] * 10 ** 18:
                log_utils.log_error("Transaction not executed, because the gas estimate is greater than the limit "
                                    f"configured in the buy_params-file. Gas estimate in wei : {tx['gas'] * tx['gasPrice']}")
                raise NotImplementedError

            tx['gas'] = gas_estimate + config.buy_params['GAS_LIMIT_BONUS']

        receipt = self._sign_and_send_tx(w3, tx, wallet_address)

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
            'gas': 300000,  # arbitrary
            'gasPrice': w3.eth.gas_price + config.buy_params['GAS_PRICE_BONUS']
        })

        signed_tx = w3.eth.account.signTransaction(tx, private_key=config.wallet_data['PRIVATE_KEY'])
        tx_hash = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
        receipt = w3.eth.waitForTransactionReceipt(tx_hash)

        log_utils.log_info(f"approval given for dex {dex_address} to spend {amount_to_approve} of {token_address}. "
                           f"receipt: {receipt}")

    def _get_wallet_address_from_key(self, w3, value=None):
        return w3.eth.account.from_key(config.wallet_data['PRIVATE_KEY']).address

    def _get_tx_params(self, w3, wallet_address, defaults):
        if w3.provider.endpoint_uri == config.general_params['ETH_RPC_URL']:
            latest_block = w3.eth.get_block('latest')

            # maxFeePerGas gets set automatically: https://github.com/ethereum/web3.py/pull/2055/commits/0e32f9d96844b1e267d7e51079395a1eeceddd78
            return {
                'nonce': w3.eth.getTransactionCount(wallet_address),
                'type': 2,  # EIP-1559
                'gas': 300000,  # =gasLimit; REVIEW: use params to set this?
                'chainId': 1,

                # send bribe directly with flashbots later on, hence no priority fee
                'maxPriorityFeePerGas': 0,
                'maxFeePerGas': 2 * latest_block['baseFeePerGas']
            }

        return defaults

    def _sign_and_send_tx(self, w3, tx, wallet_address):
        if w3.provider.endpoint_uri == config.general_params['ETH_RPC_URL']:

            signed_tx = w3.eth.account.signTransaction(tx, private_key=config.wallet_data['PRIVATE_KEY'])

            flashbots_check_and_send_contract = w3.eth.contract(
                abi=eth_chain_data[f"FLASHBOTS_CHECK_AND_SEND_ABI"],
                address=eth_chain_data[f"FLASHBOTS_CHECK_AND_SEND_ADDRESS"]
            )
            latest_block = w3.eth.get_block('latest')
            bribe_tx = flashbots_check_and_send_contract.functions.checkBytesAndSendMulti([], [], []).buildTransaction({
                'nonce': w3.eth.getTransactionCount(wallet_address) + 1,
                'type': 2,  # EIP-1559
                'chainId': 1,
                'gas': 300000,  # =gasLimit; REVIEW: use params to set this?
                'value': int(config.buy_params['BRIBE'] * 10 ** 18),
                # bribe send with 'value' param
                'maxPriorityFeePerGas': 0,
                'maxFeePerGas': 2 * latest_block['baseFeePerGas']
            })

            signed_bribe_tx = w3.eth.account.signTransaction(bribe_tx, private_key=config.wallet_data['PRIVATE_KEY'])

            bundle = [w3.toHex(signed_tx.rawTransaction), w3.toHex(signed_bribe_tx.rawTransaction)]

            'TODO: simulation keeps returning 500 internal server error, not debuggable atm'
            FlashBotsUtil.simulate(bundle, w3.eth.block_number + 1, config.wallet_data['PRIVATE_KEY'])
            pass

            # block_number = w3.eth.block_number
            # for i in range(1, 3):
            #     w3.flashbots.send_bundle(bundle, target_block_number=block_number + i)

        else:
            signed_tx = w3.eth.account.signTransaction(tx, private_key=config.wallet_data['PRIVATE_KEY'])
            tx_hash = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
            return w3.eth.waitForTransactionReceipt(tx_hash)

    @abc.abstractmethod
    def buy_on_liquidity(self, buy_params, address=None, search_name=None, search_symbol=None):
        pass

    @staticmethod
    def get_dex_router_contract(w3, chain_data, dex_name):
        return w3.eth.contract(
            abi=chain_data[f"ROUTER_ABI_{dex_name}"],
            address=chain_data[f"ROUTER_ADDRESS_{dex_name}"]
        )


class FlashBotsUtil:
    RELAY_URL = 'https://relay.flashbots.net/'

    @staticmethod
    def send_bundle(bundle, block_number, private_key):
        headers = {
            'Content-Type': 'application/json'
        }

        payload = json.dumps({
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'eth_sendBundle',
            'params': [
                {
                    'txs': bundle,
                    'blockNumber': block_number
                }
            ]
        })

        headers['X-Flashbots-Signature'] = FlashBotsUtil._get_flashbots_signature(private_key, payload)

        response = requests.post(FlashBotsUtil.RELAY_URL, data=payload, headers=headers)
        log_utils.log_info(f'Bundle sent to FlashBots. Response: {response.text}')

    @staticmethod
    def simulate(bundle, block_number, private_key):
        headers = {
            'Content-Type': 'application/json'
        }

        payload = json.dumps({
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'eth_callBundle',
            'params': [
                {
                    'txs': bundle,
                    'blockNumber': block_number,
                    'stateBlockNumer': 'latest'
                }
            ]
        })

        headers['X-Flashbots-Signature'] = FlashBotsUtil._get_flashbots_signature(private_key, payload)

        response = requests.post(FlashBotsUtil.RELAY_URL, data=payload, headers=headers)
        log_utils.log_info(f'Called for bundle simulation. Response: {response.text}')

    @staticmethod
    def _get_flashbots_signature(private_key, payload_json):
        message = messages.encode_defunct(text=Web3.keccak(text=payload_json).hex())
        return Account.from_key(private_key).address + ':' + Web3.toHex(Account.sign_message(message, private_key).signature)
