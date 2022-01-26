from dexbuytools.helpers.AvaxHelper import AvaxHelper
from dexbuytools.helpers.EvmBaseHelper import EvmBaseHelper
from dexbuytools.helpers.BscHelper import BscHelper
from dexbuytools.helpers.EthHelper import EthHelper
from dexbuytools.helpers.FtmHelper import FtmHelper

SUPPORTED_NETWORKS = {'avax', 'bsc', 'eth', 'ftm'}


def get_helper(network_name, custom_rpc=None, dex_name=None) -> EvmBaseHelper:
    if network_name not in SUPPORTED_NETWORKS:
        raise ValueError(f'passed network "{network_name}" not supported')

    if network_name == 'avax':
        return AvaxHelper(dex_name, custom_rpc)

    if network_name == 'bsc':
        return BscHelper(dex_name, custom_rpc)

    if network_name == 'eth':
        return EthHelper(dex_name, custom_rpc)

    if network_name == 'ftm':
        return FtmHelper(dex_name, custom_rpc)
