import json
import os

import strings

def update_variables(new_values):
    """
    Update the dict stored in the file `strings.file_settings`
    with the specified dict `new_values`.
    """
    vars = get_variables()
    vars.update(new_values)
    check_exists(strings.dir_data)
    with open(strings.file_settings, 'w') as f:
        json.dump(vars, f)

def get_variables():
    """
    Get the JSON dict stored in the file `strings.file_settings`.
    Returns an empty dict if the file does not exist.
    """
    
    try:
        with open(strings.file_settings) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def write_puzzle(puzzles, new_name, new_dict):
    """Write `puzzles` to the puzzles file."""
    puzzles[new_name] = new_dict
    check_exists(strings.dir_data)
    with open(strings.file_puzzles, 'w') as f:
        json.dump(puzzles, f)

def read_puzzles():
    """
    Load from the puzzles file with JSON.
    Returns an empty dict if the file does not exist.
    """
    try:
        with open(strings.file_puzzles) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def check_exists(dir_):
    """
    Check if a directory exists,
    and create it if it does not.
    """
    
    if not os.path.isdir(dir_):
        os.mkdir(dir_)

def str_to_int(s):
    """
    Convert a string to an int,
    ignoring non-numeric characters.
    """
    try:
        return int(''.join(
            [c for c in str(s) if c.isnumeric()]))
    except ValueError:
        return 0
