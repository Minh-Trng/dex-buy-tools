from setuptools import setup, find_packages

setup(
    name='DexBuyTools',
    version='0.1.0',
    packages=find_packages(),
    license='MIT',
    author='minhtrng',
    author_email='minhtrng0x@gmail.com',
    description='CLI-application to perform buys on various decentralized exchanges and different networks',
    entry_points={
        'console_scripts': [
            'dexbuy = dexbuytools.main:dexbuy',
        ],
    },
)
