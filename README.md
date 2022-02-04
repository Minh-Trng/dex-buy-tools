# dex-buy-tools

CLI application to quickly buy tokens from various networks using the standard DEX of the network:
- Ethereum: Uniswap (only V2 for now, V3 support not yet implemented)
- Binance Smart Chain: PancakeSwap
- Avalanche: TraderJoe
- Fantom: Spookyswap
- Polygon: Quickswap

Still a work-in-progress and will be continously updated, when I have time or the need for additional features.

# Installation:
pip install .

# Sample Usage
> dexbuy instant bsc 0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56 --buy_params_path ./my_config/bsc_buy_params.yml --wallet_data_path ./my_config/bsc_wallet_data.yml

Explanation:
Buys the token on address 0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56 (BUSD) on Binance smart chain with the wallet specified in 'bsc_wallet_data.yml'. The amount to buy and other parameters (such as amountOutMin, Deadline, or GasPrices) are specified in 'bsc_buy_params.yml'.
Templates for the yml-Files can be found in dexbuytools/config.