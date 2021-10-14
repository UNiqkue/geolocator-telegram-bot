import logging
import sys
from logging.handlers import RotatingFileHandler

def get_logger(name=__file__, file='log/log.log', encoding='utf-8'):
    logging.basicConfig(level=logging.DEBUG)

    log = logging.getLogger(name)
    sh = logging.StreamHandler(stream=sys.stdout)
    log.addHandler(sh)
    return log