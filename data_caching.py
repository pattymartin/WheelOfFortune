import json
import os
from collections import OrderedDict

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
                strings.title_name_exists,
                strings.label_name_exists.format(name),
                write_puzzle,
                None
            ).open()
    else:
        write_puzzle()

def add_puzzles(puzzles):
    """
    Add puzzles to the settings file.
    Creates a confirmation prompt if any duplicates are detected.
    `puzzles` is a dict containing puzzles.
    """
    
    existing_puzzles = read_puzzles()
    duplicates = {}
    not_duplicates = {}
    for name, puzzle in puzzles.items():
        if name in existing_puzzles:
            duplicates.update({name: puzzle})
        else:
            not_duplicates.update({name: puzzle})
    
    def overwrite(instance):
        """
        Write all puzzles, overwriting duplicates.
        """
        
        existing_puzzles.update(puzzles)
        update_variables({'puzzles': existing_puzzles})
    
    def no_overwrite(instance=None):
        """
        Write all puzzles, but ignore duplicates.
        """
        
        existing_puzzles.update(not_duplicates)
        update_variables({'puzzles': existing_puzzles})
    
    if duplicates:
        prompts.YesNoPrompt(
                strings.title_names_exist,
                strings.label_names_exist.format('\n'.join(duplicates)),
                overwrite,
                no_overwrite
            ).open()
    else:
        no_overwrite()

def import_puzzles(file_list):
    """
    Import puzzles from the files in `file_list`.
    Files must consist of tab-separated values,
    of the form:
    {puzzle} {category} ({clue})
    """
    unable_to_import = []
    all_found_puzzles = {}
    all_duplicate_names = []
    for puzzle_file in file_list:
        try:
            with open(puzzle_file) as f:
                found_puzzles = {}
                duplicate_names = []
                for line in f.readlines():
                    if line:
                        fields = line.split('\t')
                        puzzle = fields[0].ljust(52)[:52].upper()
                        category = fields[1].strip()
                        try:
                            clue = fields[2].strip()
                        except IndexError:
                            clue = ''
                        
                        name = ' '.join(puzzle.split())
                        if not (name in all_found_puzzles
                                or name in found_puzzles):
                            found_puzzles.update({
                                name: {
                                    'puzzle': puzzle,
                                    'category': category,
                                    'clue': clue}
                            })
                        else:
                            if not name in duplicate_names:
                                duplicate_names.append(name)
                
                # only add any puzzles if no errors encountered above
                all_found_puzzles.update(found_puzzles)
                all_duplicate_names += duplicate_names
        except:
            unable_to_import.append(puzzle_file)
    add_puzzles(all_found_puzzles)
    if unable_to_import:
        prompts.InfoPrompt(
                title=strings.title_import_error,
                text=strings.label_import_error.format(
                    '\r\n'.join(unable_to_import))
            ).open()
    if all_duplicate_names:
        prompts.InfoPrompt(
                title=strings.title_duplicates,
                text=strings.label_import_duplicates.format(
                    '\r\n'.join(all_duplicate_names))
            ).open()

def export_puzzles_by_name(puzzle_names, filename):
    """
    Export puzzles with names in `puzzle_names`
    to the file `filename`.
    """
    
    if not puzzle_names:
        prompts.YesNoPrompt(
                strings.title_no_export_selected,
                strings.label_no_export_selected,
                lambda i: export_puzzles(read_puzzles(), filename),
                None
            ).open()
    else:
        puzzles = read_puzzles()
        export_puzzles(
            OrderedDict((name, puzzles[name]) for name in puzzle_names),
            filename)

def export_puzzles(puzzles, filename):
    """
    Export `puzzles` to the file `filename`.
    `puzzles` should be a puzzles dict.
    """
    
    if not '.' in filename:
        filename += '.txt'
    
    def write(instance=None):
        """
        Write the puzzles to the file `filename`.
        """
        with open(filename, 'w') as f:
            for puzzle in puzzles.values():
                f.write('{}\t{}\t{}\n'.format(
                    puzzle['puzzle'],
                    puzzle['category'],
                    puzzle['clue']))
    
    if os.path.exists(filename):
        prompts.YesNoPrompt(
                strings.title_file_exists,
                strings.label_file_exists.format(filename),
                write,
                None
            ).open()
    else:
        write()

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
