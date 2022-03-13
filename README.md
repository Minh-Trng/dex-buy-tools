# dex-buy-tools

CLI application to quickly buy tokens from various networks using the standard DEX of the network:
- Ethereum (eth): Uniswap (only V2 for now, V3 support not yet implemented)
- Binance Smart Chain (bsc): PancakeSwap
- Avalanche (avax): TraderJoe
- Fantom (ftm): Spookyswap
- Polygon (poly): Quickswap

Still a work-in-progress and will be continously updated, when I have time or the need for additional features.

# Installation:
pip install .

If you want to use this program on the Ethereum network, you need to specify a RPC-URL in config/general_params.yml

# Sample Usage

### 1) Buying instantly 
> dexbuy instant bsc 0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56 --buy_params_path ./my_config/bsc_buy_params.yml --wallet_data_path ./my_config/bsc_wallet_data.yml

Explanation:
Buys the token on address 0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56 (BUSD) on Binance smart chain with the wallet specified in 'bsc_wallet_data.yml'. The amount to buy and other parameters (such as amountOutMin, Deadline, or GasPrices) are specified in 'bsc_buy_params.yml'.
Templates for the yml-Files can be found in dexbuytools/config.

You can also omit the file paths for the configuration:
> dexbuy instant bsc 0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56

in this case, the application will attempt to use the values in the template files in the dexbuytools/config directory

### 2) Waiting for liquidity
> dexbuy onliquidity eth --token_address '0x123456...'

Wait for liquidity to get added to the given address and then buy it. 

> dexbuy onliquidity eth --search_term 'inu'

Buys anytime liquidity is added to a token that either has 'inu' in its name or symbol.

The optional arguments "buy_params_path"
and "wallet_data_path" can be specified as in the instant buy example.