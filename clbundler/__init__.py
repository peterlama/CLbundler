from clbundler.config import global_config
from clbundler.commandparser import CommandParser
from clbundler import cli
        
def main():
    parser = CommandParser()
    cli.setup_parser(parser)
    parser.parse_args()