import abc

class BaseHelper(abc.ABC):
    @abc.abstractmethod
    def buy_instantly(self, address, buy_params):
        pass

    @abc.abstractmethod
    def buy_on_liquidity(self, buy_params, address=None, search_name=None, search_symbol=None):
        pass

    @staticmethod
    def get_dex_contract(w3, chain_data, dex_name):
        return w3.eth.contract(
            abi=chain_data[f"ROUTER_ABI_{dex_name}"],
            address=chain_data[f"ROUTER_ADDRESS_{dex_name}"]
        )