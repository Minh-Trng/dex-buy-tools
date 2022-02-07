import pathlib
from setuptools import setup, find_packages

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()

setup(
    name='DexBuyTools',
    version='0.1.post1',
    packages=find_packages(exclude=("tests", "my_config",)),
    license='MIT',
    author='minhtrng',
    author_email='minhtrng0x@gmail.com',
    include_package_data=True,
    description='CLI-application to perform buys on various decentralized exchanges and different networks',
    entry_points={
        'console_scripts': [
            'dexbuy = dexbuytools.__main__:dexbuy',
        ],
    },
)
