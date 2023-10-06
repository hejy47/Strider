import logging

def initLogger(path, cmdLevel = logging.DEBUG, fileLevel = logging.DEBUG):
    logger = logging.getLogger(path)
    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter('[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    # cmd log
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    sh.setLevel(cmdLevel)
    # file log
    fh = logging.FileHandler(path)
    fh.setFormatter(fmt)
    fh.setLevel(fileLevel)
    logger.addHandler(sh)
    logger.addHandler(fh)
    return logger