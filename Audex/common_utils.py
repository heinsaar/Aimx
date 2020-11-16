from termcolor import colored
from pathlib   import Path
from time      import sleep
import json
import glob
import sys
import os

class AimxPath:
    WORKDIR          = os.path.join(Path().resolve().parent, "workdir")
    GEN_PLOTS        = os.path.join(WORKDIR, "gen_plots")
    GEN_SAVED_MODELS = os.path.join(WORKDIR, "gen_saved_models")
    DATA_JSON        = os.path.join(WORKDIR, "data_json")
    DATAPREP_RESULT_META_FILENAME = "dataprep_result_meta.json"

def exists(x):
    return x is not None

def provided(cmd_arg):
    return cmd_arg is not None

def quote(me):
    return '\'' + str(me) + '\''

# TODO: This function seems to not always return as expected
# Currently disabled, but kept as it looks useful if perfected.
def get_most_recent_file_in_dir(data_json_path, ext):
    files = glob.iglob(data_json_path + '/*.' + ext)
    return max(files, key = os.path.getctime)

def get_dataset_code(dataset_json_filepath):
    return Path(dataset_json_filepath).stem[8:]

def progress_bar(current, total):
     j = (current + 1) / total
     sys.stdout.write('\r')
     sys.stdout.write("[%-20s] %d%%" % ('█'*int(20*j), 100*j))
     sys.stdout.flush()

def extract_filename(fullpath):
    return os.path.splitext(fullpath)[0]

def extract_fileext(fullpath):
    return os.path.splitext(fullpath)[1]

class Colors:
    PURPLE      = '\033[95m'
    BLUE        = '\033[94m'
    CYAN        = '\033[96m'
    GREENBRIGHT = '\033[92m'
    LIGHTYELLOW = '\033[93m'
    PINKRED     = '\033[91m'
    ENDC        = '\033[0m'
    BOLD        = '\033[1m'
    UNDERLINE   = '\033[4m'

    def disable(self):
        self.PURPLE      = ''
        self.BLUE        = ''
        self.GREENBRIGHT = ''
        self.LIGHTYELLOW = ''
        self.PINKRED     = ''
        self.ENDC        = ''

# Forwarding string colorization functions using termcolor Python module
"""
Available text colors:
    red, green, yellow, blue, magenta, cyan, white.

Available text highlights:
    on_red, on_green, on_yellow, on_blue, on_magenta, on_cyan, on_white.

Available attributes:
    bold, dark, underline, blink, reverse, concealed.

Example:
    colored('Hello, World!', 'red', 'on_grey', ['blue', 'blink'])
    colored('Hello, World!', 'green')
"""
def yellow(s):
    return colored(s, 'yellow')

def magenta(s):
    return colored(s, 'magenta')

def cyansky(s):
    return colored(s, 'cyan')

def white(s):
    return colored(s, 'white')

def red(s):
    return colored(s, 'red')

def green(s):
    return colored(s, 'green')

# Forwarding string colorization functions using ASCII escape sequences
def purple(s):
    return f"{Colors.PURPLE}" + str(s) + f"{Colors.ENDC}"

def blue(s):
    return f"{Colors.BLUE}" + str(s) + f"{Colors.ENDC}"

def cyan(s):
    return f"{Colors.CYAN}" + str(s) + f"{Colors.ENDC}"

def greenbright(s):
    return f"{Colors.GREENBRIGHT}" + str(s) + f"{Colors.ENDC}"

def lightyellow(s):
    return f"{Colors.LIGHTYELLOW}" + str(s) + f"{Colors.ENDC}"

def pinkred(s):
    return f"{Colors.PINKRED}" + str(s) + f"{Colors.ENDC}"

# Semantic print functions
def print_info(s, *args, verbose = True, **kwargs):
    if verbose:
        print(yellow(s), *args, **kwargs)