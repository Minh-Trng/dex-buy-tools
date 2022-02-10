import yaml
import os

file_dir = os.path.dirname(__file__)

class Config:
    def __init__(self, buy_params, wallet_data, general_params):
        self.buy_params = buy_params
        self.wallet_data = wallet_data
        self.general_params = general_params

def get_config(buy_params_path=None, wallet_data_path=None, general_params_path=None):

    buy_params_path = f'{file_dir}/buy_params.yml' if buy_params_path is None else buy_params_path
    wallet_data_path = f'{file_dir}/wallet_data_template.yml' if wallet_data_path is None else wallet_data_path
    general_params_path = f'{file_dir}/general_params.yml' if general_params_path is None else general_params_path

    with open(buy_params_path, 'r') as f:
        buy_params = yaml.safe_load(f)

    with open(wallet_data_path, 'r') as f:
        wallet_data = yaml.safe_load(f)

    with open(general_params_path, 'r') as f:
        general_params = yaml.safe_load(f)

    return Config(buy_params, wallet_data, general_params)