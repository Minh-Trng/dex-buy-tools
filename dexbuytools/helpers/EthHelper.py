import json

import requests
import web3
from eth_account import messages, Account
from web3 import Web3
from web3.middleware import geth_poa_middleware

from dexbuytools import log_utils
from dexbuytools.helpers.EvmBaseHelper import EvmBaseHelper
from dexbuytools.helpers.data.eth import chain_data
from uniswap import Uniswap
from dexbuytools.helpers.data.eth import chain_data as eth_chain_data


class EthHelper(EvmBaseHelper):
    DEFAULT_DEX = "UNI"

    def __init__(self, config, dex_name=None, custom_rpc=None):
        w3 = Web3(Web3.HTTPProvider(config.general_params['ETH_RPC_URL'] if custom_rpc is None else custom_rpc))

        dex_name = EthHelper.DEFAULT_DEX if dex_name is None else dex_name
        super().__init__(w3, chain_data, dex_name, config)

    def buy_instantly(self, token_address):
        uniswap_v2 = Uniswap(address=None, private_key=None, version=2,
                             provider=self.config.general_params['ETH_RPC_URL'])
        uniswap_v3 = Uniswap(address=None, private_key=None, version=3,
                             provider=self.config.general_params['ETH_RPC_URL'])
        token_address = self.w3.toChecksumAddress(token_address)
        weth_address = self.w3.toChecksumAddress(self.chain_data['MAIN_TOKEN_ADDRESS'])

        output_v2 = 0
        output_v3 = 0

        try:
            output_v2 = uniswap_v2.get_price_input(weth_address, token_address,
                                                   int(self.config.buy_params["AMOUNT"] * 10 ** 18))
        except web3.exceptions.ContractLogicError as e:
            pass

        try:
            output_v3 = uniswap_v3.get_price_input(weth_address, token_address,
                                                   int(self.config.buy_params["AMOUNT"] * 10 ** 18))
        except web3.exceptions.ContractLogicError as e:
            pass

        if output_v2 == 0 and output_v3 == 0:
            log_utils.log_error(f"No liquidity on uniswap for token f{token_address}")
            return

        if output_v2 > output_v3:
            return self._perform_uniswapv2_buy(token_address)
        else:
            return self._perform_uniswapv3_buy(token_address)

    def _perform_uniswapv2_buy(self, token_address):
        wallet_address = self.w3.toChecksumAddress(self._get_wallet_address_from_key())
        tx = self.build_uniswapv2_style_tx(token_address, wallet_address)

        del tx['gasPrice']  # not required post EIP-1559

        latest_block = self.w3.eth.get_block('latest')
        tx['type'] = 2
        tx['chainId'] = 1
        tx['maxPriorityFeePerGas'] = 0  # send bribe directly with flashbots later on, hence no priority fee
        tx['maxFeePerGas'] = 2 * latest_block['baseFeePerGas']
        tx['nonce'] = self.w3.eth.getTransactionCount(wallet_address)

        self._send_flashbots_bundle(tx, wallet_address)

    def _perform_uniswapv3_buy(self, token_address):
        uniswapv3 = self.w3.eth.contract(
            abi=chain_data['ROUTER_ABI_UNIV3'],
            address=chain_data['ROUTER_ADDRESS_UNIV3']
        )

        log_utils.log_error("Buying on UniswapV3 not yet implemented")

    def buy_on_liquidity(self, buy_params, address=None, search_name=None, search_symbol=None):
        raise NotImplementedError()

    def _send_flashbots_bundle(self, tx, wallet_address):

        signed_tx = self.w3.eth.account.signTransaction(tx, private_key=self.config.wallet_data['PRIVATE_KEY'])

        flashbots_check_and_send_contract = self.w3.eth.contract(
            abi=eth_chain_data[f"FLASHBOTS_CHECK_AND_SEND_ABI"],
            address=eth_chain_data[f"FLASHBOTS_CHECK_AND_SEND_ADDRESS"]
        )
        latest_block = self.w3.eth.get_block('latest')
        bribe_tx = flashbots_check_and_send_contract.functions.checkBytesAndSendMulti([], [], []).buildTransaction({
            'nonce': self.w3.eth.getTransactionCount(wallet_address) + 1,
            'type': 2,  # EIP-1559
            'chainId': 1,
            'gas': 300000,  # =gasLimit; REVIEW: use params to set this?
            'value': int(self.config.buy_params['BRIBE'] * 10 ** 18),
            # bribe send with 'value' param
            'maxPriorityFeePerGas': 0,
            'maxFeePerGas': 2 * latest_block['baseFeePerGas']
        })

        signed_bribe_tx = self.w3.eth.account.signTransaction(bribe_tx, private_key=self.config.wallet_data['PRIVATE_KEY'])

        bundle = [self.w3.toHex(signed_tx.rawTransaction), self.w3.toHex(signed_bribe_tx.rawTransaction)]

        # FlashBotsUtil.simulate(bundle, Web3.toHex(self.w3.eth.block_number + 1), self.config.wallet_data['PRIVATE_KEY'])
        # pass

        block_number = self.w3.eth.block_number
        for i in range(1, 3):
            FlashBotsUtil.send_bundle(bundle, block_number+i, self.config.wallet_data['PRIVATE_KEY'])

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
                    'stateBlockNumber': 'latest'
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
