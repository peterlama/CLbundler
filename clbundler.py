from config import global_config
from commandparser import CommandParser
import cli
        
def main():
    parser = CommandParser()
    cli.setup_parser(parser)
    parser.parse_args()
        
if __name__ == "__main__":
    main()
