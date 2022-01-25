import click
from web3 import Web3
from web3.middleware import geth_poa_middleware
from dexbuytools.helpers import get_helper
import yaml

# TODO: check whether path or just filename should be passed
def load_buy_params(file_path):
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)

@click.group()
def dexbuy():
    pass


@dexbuy.command()
@click.argument('address')
@click.argument('network_name')
@click.option('--buy_params_path', default='config/buy_params.yml')
@click.option('--dex_name', default=None)
def instant(address, network_name, buy_params_path, dex_name):
    helper = get_helper(network_name)
    buy_params = load_buy_params(buy_params_path)

    helper.buy_instantly(address, buy_params, dex_name)



@dexbuy.command()
#TODO: address, name or symbol have to be given
@click.argument('network')
def onliquidity(**kwargs):
    """
        Buy once liquidity gets added for token of given address or any token that matches the given search_name or
        search_term
    """
    raise NotImplementedError

if __name__ == '__main__':
    dexbuy()
