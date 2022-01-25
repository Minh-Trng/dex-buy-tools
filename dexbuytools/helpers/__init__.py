from dexbuytools.helpers.AvaxHelper import AvaxHelper
from dexbuytools.helpers.BaseHelper import BaseHelper
from dexbuytools.helpers.BscHelper import BscHelper
from dexbuytools.helpers.EthHelper import EthHelper
from dexbuytools.helpers.FtmHelper import FtmHelper

SUPPORTED_NETWORKS = {'avax', 'bsc', 'eth', 'ftm'}


def get_helper(network_name) -> BaseHelper:
    if network_name not in SUPPORTED_NETWORKS:
        raise ValueError(f'passed network "{network_name}" not supported')

    if network_name == 'avax':
        return AvaxHelper()

    if network_name == 'bsc':
        return BscHelper()

    if network_name == 'eth':
        return EthHelper()

    if network_name == 'ftm':
        return FtmHelper()
