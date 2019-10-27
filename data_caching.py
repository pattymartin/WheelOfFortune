import json
import os

import prompts, strings

def update_variables(new_values):
    """
    Update the dict stored in the file `strings.file_settings`
    with the specified dict `new_values`.
    """
    vars = get_variables()
    vars.update(new_values)
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

def read_puzzles():
    """
    Load the puzzles from the settings file.
    Returns an empty dict if the file does not exist.
    """
    return get_variables().get('puzzles', {})

def add_puzzle(name, puzzle_dict):
    """
    Add a puzzle to the settings file.
    Creates a confirmation prompt if a puzzle
    with the given name already exists.
    """
    
    puzzles = read_puzzles()
    
    def write_puzzle(instance=None):
        """
        Add `puzzle_dict` to `puzzles`
        and write `puzzles` to the settings file.
        """
        puzzles[name] = puzzle_dict
        update_variables({'puzzles': puzzles})
        
    if name in puzzles.keys():
        prompts.YesNoPrompt(
                strings.label_name_exists.format(
                    name),
                write_puzzle,
                None
            ).open()
    else:
        write_puzzle()

def import_puzzles(file_list):
    """
    Import puzzles from the files in `file_list`.
    Each file must be a dict parsable by JSON,
    resembling the following:
    {
        '(puzzle name)': {
            'puzzle': '(puzzle)',
            'category': '(category)',
            'clue (optional)': '(clue)'
        }
        '(second puzzle name)': {
            ...
        }
    }
    """
    unable_to_import = []
    for puzzle_file in file_list:
        try:
            with open(puzzle_file) as f:
                file_read = json.load(f)
                for k, v in file_read.items():
                    add_puzzle(k, {
                            'puzzle': v['puzzle'].ljust(52)[:52],
                            'category': v['category'],
                            'clue': v.get('clue', '')
                        })
        except PermissionError:
            pass
        except (json.decoder.JSONDecodeError, TypeError, KeyError,
                AttributeError):
            unable_to_import.append(puzzle_file)
    if unable_to_import:
        prompts.InfoPrompt(
                title=strings.title_import_error,
                text=strings.label_import_error.format(
                    '\r\n'.join(unable_to_import))
            ).open()

def delete_puzzle(name):
    """
    Delete the puzzle with the name `name`.
    """
    puzzles = read_puzzles()
    puzzles.pop(name, None)
    update_variables({'puzzles': puzzles})

def delete_all_puzzles():
    """
    Delete all puzzles.
    """
    update_variables({'puzzles': {}})

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
