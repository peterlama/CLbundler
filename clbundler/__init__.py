import logging
import sys
from clbundler.config import global_config
from clbundler.commandparser import CommandParser
from clbundler import cli
        
def main():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    parser = CommandParser()
    cli.setup_parser(parser)
    parser.parse_args()
