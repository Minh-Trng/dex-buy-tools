import click

def buyer(**kwargs):
    output = '{0}, {1}!'.format(kwargs['greeting'],
                                kwargs['name'])
    if kwargs['caps']:
        output = output.upper()
    print(output)

@click.group()
def dexbuy():
    pass


@dexbuy.command()
@click.argument('address')
@click.argument('network')
def instant(**kwargs):
    buyer(**kwargs)


@dexbuy.command()
#TODO: entweder address, name, oder symbol müssen gegeben sein
@click.argument('network')
def onliquidity(**kwargs):
    listener(**kwargs)

if __name__ == '__main__':
    dexbuy()
