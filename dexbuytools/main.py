import click
from web3 import Web3
from web3.middleware import geth_poa_middleware
from dexbuytools.helpers import get_helper
import dexbuytools.config as config
import yaml


# TODO: check whether path or just filename should be passed
def adjust_config(buy_params_path, wallet_data_path):
    if buy_params_path is not None:
        config.replace_buy_params(buy_params_path)

    if wallet_data_path is not None:
        config.replace_wallet_data(wallet_data_path)


@click.group()
def dexbuy():
    pass


@dexbuy.command()
@click.argument('network_name')
@click.argument('token_address')
@click.option('--buy_params_path', default=None)
@click.option('--wallet_data_path', default=None)
@click.option('--dex_name', default=None)
@click.option('--custom_rpc', default=None)
def instant(network_name, token_address, buy_params_path, wallet_data_path, dex_name, custom_rpc):
    helper = get_helper(network_name, dex_name, custom_rpc)
    adjust_config(buy_params_path, wallet_data_path)

    helper.buy_instantly(token_address)


@dexbuy.command()
# TODO: address, name or symbol have to be given
@click.argument('network')
def onliquidity(**kwargs):
    """
        Buy once liquidity gets added for token of given address or any token that matches the given search_name or
        search_term
    """
    raise NotImplementedError


if __name__ == '__main__':
    dexbuy()
