import click
from enum import Enum
from web3 import Web3
from web3.middleware import geth_poa_middleware
import config.general

def get_avax_connnection():
    w3 = Web3(Web3.HTTPProvider("https://api.avax.network/ext/bc/C/rpc"))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    return w3

def get_bsc_connection():
    w3 = Web3(Web3.HTTPProvider('https://bsc-dataseed1.ninicoin.io/'))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    return w3

def get_eth_connection():
    w3 = Web3(Web3.HTTPProvider(config.general.ETH_RPC_URL))
    return w3

def get_ftm_connection():
    w3 = Web3(Web3.HTTPProvider("https://rpc.ftm.tools/"))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    return w3

connectors = {
    "avax": get_avax_connnection,
    "bsc": get_bsc_connection,
    "eth": get_eth_connection,
    "ftm": get_ftm_connection,
}

def connect(network_name):
    return connectors[network_name].__call__()


def buy(**kwargs):
    helper = connect(kwargs['network'])
    output = '{0}, {1}!'.format(kwargs['greeting'],
                                kwargs['name'])
    if kwargs['caps']:
        output = output.upper()
    print(output)

def listen():
    pass #TODO

@click.group()
def dexbuy():
    pass


@dexbuy.command()
@click.argument('address')
@click.argument('network')
def instant(**kwargs):
    buy(**kwargs)


@dexbuy.command()
#TODO: entweder address, name, oder symbol müssen gegeben sein
@click.argument('network')
def onliquidity(**kwargs):
    listen(**kwargs)

if __name__ == '__main__':
    dexbuy()
