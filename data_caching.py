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
    
    def write_puzzle():
        """
        Add `puzzle_dict` to `puzzles`
        and write `puzzles` to the settings file.
        """
        puzzles[name] = puzzle_dict
        update_variables({'puzzles': puzzles})
        
    if name in puzzles.keys():
        prompts.YesNoPrompt(
                strings.label_name_exists.format(name),
                write_puzzle,
                None,
                title=strings.title_name_exists
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
    
    def overwrite():
        """
        Write all puzzles, overwriting duplicates.
        """
        
        existing_puzzles.update(puzzles)
        update_variables({'puzzles': existing_puzzles})
    
    def no_overwrite():
        """
        Write all puzzles, but ignore duplicates.
        """
        
        existing_puzzles.update(not_duplicates)
        update_variables({'puzzles': existing_puzzles})
    
    if duplicates:
        prompts.YesNoPrompt(
                strings.label_names_exist.format('\n'.join(duplicates)),
                overwrite,
                no_overwrite,
                title=strings.title_names_exist
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

def export_puzzles_by_name(filename, puzzle_names):
    """
    Export puzzles with names in `puzzle_names`
    to the file `filename`.
    """
    
    if not puzzle_names:
        prompts.YesNoPrompt(
                strings.label_no_export_selected,
                lambda: export_puzzles(filename, read_puzzles()),
                None,
                title=strings.title_no_export_selected
            ).open()
    else:
        puzzles = read_puzzles()
        export_puzzles(
            filename,
            OrderedDict((name, puzzles[name]) for name in puzzle_names))

def export_puzzles(filename, puzzles):
    """
    Export `puzzles` to the file `filename`.
    `puzzles` should be a puzzles dict.
    """
    
    if not '.' in filename:
        filename += '.txt'
    
    def write():
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
                strings.label_file_exists.format(filename),
                write,
                None,
                title=strings.title_file_exists
            ).open()
    else:
        write()

def import_game(filename):
    """
    Read a game from a file
    and return the game.
    
    Each line in the file must consist
    of tab-separated values,
    of the form:
    {round_type} {round_reward} {puzzle} {category} ({clue})
    """
    
    game = []
    
    try:
        with open(filename) as f:
            for line in f.readlines():
                if line:
                    fields = line.split('\t')
                    
                    round_type = fields[0].strip()
                    round_reward = fields[1].strip()
                    puzzle = fields[2].ljust(52)[:52].upper()
                    category = fields[3].strip()
                    try:
                        clue = fields[4].strip()
                    except IndexError:
                        clue = ''
                    
                    game.append({
                        'round_type': round_type,
                        'round_reward': round_reward,
                        'puzzle': {
                            'puzzle': puzzle,
                            'category': category,
                            'clue': clue}})
    except:
        prompts.InfoPrompt(
                title=strings.title_import_error,
                text=strings.label_import_error.format(filename)
            ).open()
    
    return game

def export_game(filename, game):
    """
    Export `game` to the file `filename`.
    """
    
    if not '.' in filename:
        filename += '.txt'
    
    def write():
        """
        Write the game to the file.
        """
        
        with open(filename, 'w') as f:
            for puzzle in game:
                f.write('{}\t{}\t{}\t{}\t{}\n'.format(
                    puzzle['round_type'],
                    puzzle['round_reward'],
                    puzzle['puzzle']['puzzle'],
                    puzzle['puzzle']['category'],
                    puzzle['puzzle']['clue']))
    
    if os.path.exists(filename):
        prompts.YesNoPrompt(
                strings.label_file_exists.format(filename),
                write,
                None,
                title=strings.title_file_exists
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

def get_hotkeys():
    """
    Load the hotkeys from the settings file.
    Returns an empty dict if the file does not exist,
    or if there are no hotkeys saved.
    """
    
    return get_variables().get('hotkeys', {})

def write_hotkeys(hotkeys):
    """
    Save a dict of hotkeys to the settings file.
    """
    
    update_variables({'hotkeys': hotkeys})

def str_to_int(s, default_value=0):
    """
    Convert a string to an int,
    ignoring non-numeric characters.
    If there are no numeric characters,
    returns `default_value`.
    """
    try:
        return int(''.join(
            [c for c in str(s) if c.isnumeric()]))
    except ValueError:
        return default_value
