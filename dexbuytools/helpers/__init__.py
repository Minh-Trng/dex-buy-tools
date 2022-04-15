from dexbuytools.helpers.AvaxHelper import AvaxHelper
from dexbuytools.helpers.EvmBaseHelper import EvmBaseHelper
from dexbuytools.helpers.BscHelper import BscHelper
from dexbuytools.helpers.EthHelper import EthHelper
from dexbuytools.helpers.FtmHelper import FtmHelper
from dexbuytools.helpers.PolyHelper import PolyHelper
from dexbuytools.helpers.CroHelper import CroHelper

SUPPORTED_NETWORKS = {'avax', 'bsc', 'cro', 'eth', 'ftm', 'poly'}


def get_helper(network_name, config, custom_rpc=None, dex_name=None) -> EvmBaseHelper:
    if network_name not in SUPPORTED_NETWORKS:
        raise ValueError(f'passed network "{network_name}" not supported')

    if network_name == 'avax':
        return AvaxHelper(config, dex_name, custom_rpc)

    if network_name == 'bsc':
        return BscHelper(config, dex_name, custom_rpc)

    if network_name == 'cro':
        return CroHelper(config, dex_name, custom_rpc)

    if network_name == 'eth':
        return EthHelper(config, dex_name, custom_rpc)

    if network_name == 'ftm':
        return FtmHelper(config, dex_name, custom_rpc)

    if network_name == 'poly':
        return PolyHelper(config, dex_name, custom_rpc)
