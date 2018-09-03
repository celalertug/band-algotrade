import logging


def getlogger(path):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s')

    file_handler = logging.FileHandler(path)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    return logger


xlogger = getlogger("logs/all.log")


def logprint(*args):
    global xlogger

    r = ""
    for i in args:
        r += str(i) + " "
    xlogger.info(r)
    print("LOG : ", r)
