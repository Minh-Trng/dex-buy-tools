import pytest
from brownie import network, accounts
import os
from dexbuytools import config
import secrets
from dexbuytools.helpers import BscHelper, FtmHelper, PolyHelper, AvaxHelper

BUSD_ADDRESS_BSC = '0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56'
USDC_ADDRESS_FTM = '0x04068DA6C83AFCFA0e13ba15A6696662335D5B75'
USDC_ADDRESS_POLY = '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174'
USDC_ADDRESS_AVAX = '0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E'
PRIVATE_KEY = secrets.token_hex(32)


@pytest.fixture()
def mainnet_fork(request):

    marker = request.node.get_closest_marker('brownie_network_name')
    if marker is None:
        raise ValueError("fixture used without passing network name with marker option")
    else:
        network_name = marker.args[0]

    network.connect(network_name)

    account = accounts.add(PRIVATE_KEY)
    accounts[0].transfer(account, "10 ether")

    yield

    network.disconnect(kill_rpc=True)

@pytest.fixture()
def configuration():
    file_dir = os.path.dirname(__file__)
    buy_params_path = f"{file_dir}/test_config/test_buy_params.yml"
    config_instance = config.get_config(buy_params_path=buy_params_path)
    config_instance.wallet_data["PRIVATE_KEY"] = PRIVATE_KEY
    return config_instance

@pytest.mark.brownie_network_name('bsc-main-fork')
def test_BscHelper(mainnet_fork, configuration):
    local_bsc_fork_rpc_url = network.web3.provider.endpoint_uri
    helper = BscHelper(configuration, custom_rpc=local_bsc_fork_rpc_url)
    tx = helper.buy_instantly(BUSD_ADDRESS_BSC)
    assert tx.transactionHash is not None
    assert accounts[-1].balance() <= network.web3.toWei(9, "ether")

@pytest.mark.brownie_network_name('ftm-main-fork')
def test_FtmHelper(mainnet_fork, configuration):
    local_ftm_fork_rpc_url = network.web3.provider.endpoint_uri
    helper = FtmHelper(configuration, custom_rpc=local_ftm_fork_rpc_url)
    tx = helper.buy_instantly(USDC_ADDRESS_FTM)
    assert tx.transactionHash is not None
    assert accounts[-1].balance() <= network.web3.toWei(9, "ether")

@pytest.mark.brownie_network_name('polygon-main-fork')
def test_PolyHelper(mainnet_fork, configuration):
    local_poly_fork_rpc_url = network.web3.provider.endpoint_uri
    helper = PolyHelper(configuration, custom_rpc=local_poly_fork_rpc_url)
    tx = helper.buy_instantly(USDC_ADDRESS_POLY)
    assert tx.transactionHash is not None
    assert accounts[-1].balance() <= network.web3.toWei(9, "ether")

@pytest.mark.brownie_network_name('avax-main-fork')
def test_AvaxHelper(mainnet_fork, configuration):
    local_avax_fork_rpc_url = network.web3.provider.endpoint_uri
    helper = PolyHelper(configuration, custom_rpc=local_avax_fork_rpc_url)
    tx = helper.buy_instantly(USDC_ADDRESS_AVAX)
    assert tx.transactionHash is not None
    assert accounts[-1].balance() <= network.web3.toWei(9, "ether")