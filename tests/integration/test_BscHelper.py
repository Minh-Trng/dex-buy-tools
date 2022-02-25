import os

stream = os.popen('ganache-cli --fork https://bsc-dataseed.binance.org/')
output = stream.read()
print(output)