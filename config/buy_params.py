# many tokens impose limit on how many tokens can be bought
MAX_PERCENTAGE_OF_TOTAL_SUPPLY_BUY_LIMIT = 5

# attempt to filter fake tokens, when trying to snipe based on name and if tokenomics details are known
MIN_PERCENTAGE_OF_TOTAL_SUPPLY_IN_LIQUIDITY = 10
MAX_PERCENTAGE_OF_TOTAL_SUPPLY_IN_LIQUIDITY = 100

# denominated in dollars, using BinanceApi as source
MIN_VALUE_OF_LIQUIDITY = 1000

# cancel buy, if current gas costs of the network are too high, especially useful for Ethereum network
MAX_GAS_ESTIMATE = None

# repeat buy this many times with different wallets (generated from seed phrase in wallet_config)
WALLET_COUNT = 1

MAX_SLIPPAGE_PERCENTAGE = 90