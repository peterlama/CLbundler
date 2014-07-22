import commands
from commandparser import Subcommand
import config

def on_new(parser, options, args):
    if len(args) < 3:
        parser.error("too few arguments")
    if not (args[1] == "vc9" or args[1] == "vc12"):
        parser.error("only vc9, vc12 are supported at the moment")
    if not (args[2] == "x86" or args[2] == "x64"):
        parser.error("Unknown architecture '{0}' (needs to be one of [x86, x64])".format(args[2]))
    commands.cmd_new(args[0], args[1], args[2])

def on_install(parser, options, args):
    if not args:
        parser.error("no formula specified")
    for n in args:
        commands.cmd_install(n, options.interactive_mode, options.force_install)

def on_uninstall(parser, options, args):
    if not args:
        parser.error("no formula specified")
    for n in args:
        commands.cmd_uninstall(n)
    
def on_archive(parser, options, args):
    commands.cmd_archive(options.path)

def setup_parser(parser):
    parser.usage = "clbundler <command> [options]" 
    parser.description = "Type 'clbundler <command> --help' for more information "\
                         "on a specific command"
    
    usage = "{0} {1} [options]"

    subcommand = Subcommand("new", callback=on_new,
                            usage=usage.format("new","PATH TOOLCHAIN ARCH"), 
                            short_help="Sets up a new bundle",
                            detailed_help="Currently, only vc9 is the only supported TOOLCHAIN")
    parser.add_subcommand(subcommand)

    subcommand = Subcommand("install", callback=on_install,
                            usage=usage.format("install","FORMULA"),
                            short_help="Install a library into a bundle")
    subcommand.add_option("-f", "--force", dest="force_install", action="store_true",
                          help="Install even if already installed")
    subcommand.add_option("-i", "--interactive", dest="interactive_mode", action="store_true",
                          help="Start a shell after downloading and patching the source")
    parser.add_subcommand(subcommand)
    
    subcommand = Subcommand("uninstall", callback=on_uninstall,
                          usage=usage.format("uninstall","FORMULA"),
                          short_help="Remove a library from a bundle")
    parser.add_subcommand(subcommand)
    
    subcommand = Subcommand("archive", callback=on_archive,
                            usage="archive [options]",
                            short_help="Create a compressed archive of current bundle")
    subcommand.add_option("-p", "--path", dest="path",
                          help="Specify a directory to create the archive in")
    parser.add_subcommand(subcommand)
    