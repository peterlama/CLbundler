import sys
import optparse
import textwrap

class CustomHelpFormatter(optparse.IndentedHelpFormatter):
    """
    Formatter that allows paragraphs in the description
    """
    def __init__(self,
                 indent_increment=0,
                 max_help_position=24,
                 width=None,
                 short_first=0):
        optparse.IndentedHelpFormatter.__init__(
            self, indent_increment, max_help_position, width, short_first)
        
    def format_description(self, description):
        paragraphs = description.split("\n\n")
        result = []
        
        for p in paragraphs:
            s = optparse.IndentedHelpFormatter.format_description(self, p)
            if s:
                result.append(s)
                result.append('\n')
        if result:
            #drop last \n
            return "".join(result[:-1])
        return ""
        
class Subcommand:
    def __init__(self, name, options=None, args=None, callback=None,
                 usage="", short_help="", detailed_help=""):
        self.name = name
        self.options = []
        if options is not None: self.options = options
        self.args = args
        self.callback = callback
        self.usage = usage
        self.short_help = short_help
        self.detailed_help = detailed_help
    
    def add_option(self, *args, **kwargs):
        self.options.append(optparse.Option(*args, **kwargs))
            
    def parse_args(self, arg_list):
        help = self.short_help + "\n\n" + self.detailed_help
        
        parser = optparse.OptionParser(usage=self.usage, description=help,
                                       formatter=CustomHelpFormatter())
        parser.add_options(self.options)
        opts, args = parser.parse_args(arg_list)
        
        if self.callback != None:
            self.callback(parser, opts, args)
            
        parser.destroy()
        
class CommandParser(optparse.OptionParser):
    """
    Extends OptionParser to handle subcommands
    """
    def __init__(self, usage=None, description=None):
        optparse.OptionParser.__init__(self, usage=usage, description=description)

        self.subcommands = {}

    def add_subcommand(self, subcommand):
        self.subcommands[subcommand.name] = subcommand

    def parse_args(self, args=None, values=None):
        if args == None:
            args = sys.argv[1:]
        if len(args) == 0:
            self.print_help()
            sys.exit(1)
        if args[0] in self.subcommands.keys():
            self.subcommands[args[0]].parse_args(args[1:])
        elif not args[0].startswith("-"):
            self.error("unknown subcommand " + args[0])
        else:
            optparse.OptionParser.parse_args(self, args, values)
    
    def _compute_help_indentation(self, formatter):
        formatter.indent()
        max_len = 0
        #find the longest command name
        for k in self.subcommands.keys():
            max_len = max(max_len, len(self.subcommands[k].name) + formatter.current_indent)
        formatter.dedent()
        
        formatter.help_position = min(max_len + 2, formatter.max_help_position)
        formatter.help_width = max(formatter.width - formatter.help_position, 11)
        
    def format_command_help(self, formatter):
        self._compute_help_indentation(formatter)
        command_help = []
        command_help.append(formatter.format_heading("Commands"))

        formatter.indent()
        
        help_list = []
        for k in self.subcommands.keys():
            cmd = self.subcommands[k]
            width = formatter.help_position - formatter.current_indent - 2
            cmd_str = "%*s%-*s  " % (formatter.current_indent, "", width, cmd.name)
            indent_first = 0
            help_list.append(cmd_str)
            
            if cmd.short_help:
                help_lines = textwrap.wrap(cmd.short_help, formatter.help_width)
                help_list.append("%*s%s\n" % (indent_first, "", help_lines[0]))
                help_list.extend(["%*s%s\n" % (formatter.help_position, "", line)
                               for line in help_lines[1:]])
        
            else:
                help_list.append("\n")
                
        command_help.append("".join(help_list))
        command_help.append("\n")
        
        formatter.dedent()
        
        return "".join(command_help)
        
    def format_help(self, formatter=None):
        if formatter is None:
            formatter = self.formatter
        result = []
        if self.usage:
            result.append(self.get_usage() + "\n")
        if self.description:
            result.append(self.format_description(formatter) + "\n")
        result.append(self.format_command_help(formatter))
        result.append(self.format_option_help(formatter))
        result.append(self.format_epilog(formatter))
        return "".join(result)