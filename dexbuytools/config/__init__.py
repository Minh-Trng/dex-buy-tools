import yaml
import os

file_dir = os.path.dirname(__file__)

#convenience initialization for development or usage by local installation
with open(f'{file_dir}/buy_params.yml', 'r') as f:
    buy_params = yaml.safe_load(f)

with open(f'{file_dir}/wallet_data_template.yml', 'r') as f:
    wallet_data = yaml.safe_load(f)

with open(f'{file_dir}/general_params.yml', 'r') as f:
    general_params = yaml.safe_load(f)

def replace_buy_params(file_path):
    global buy_params
    with open(file_path, 'r') as f:
        buy_params = yaml.safe_load(f)

def replace_wallet_data(file_path):
    global wallet_data
    with open(file_path, 'r') as f:
        wallet_data = yaml.safe_load(f)

def replace_general_params(file_path):
    global general_params
    with open(file_path, 'r') as f:
        general_params = yaml.safe_load(f)