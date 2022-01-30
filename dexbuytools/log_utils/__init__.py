import logging

logging = logging

logging.basicConfig(filename="dexbuytools.log", format="[%(asctime)s] %(levelname)s: %(message)s",
                    datefmt='%d/%m/%Y %H:%M:%S', level=logging.INFO)

def log_info(message):
    print(message)
    logging.info(message)

def log_error(message):
    print(message)
    logging.error(message)