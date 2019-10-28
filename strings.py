import os

button_close = 'Close'
button_confirm = 'Confirm'
button_guess_letter = 'Guess\nLetter'
button_delete_all = 'Delete All'
button_fullscreen = 'Toggle\nFullscreen'
button_load = 'Import'
button_no = 'No'
button_ok = 'OK'
button_save = 'Export'
button_yes = 'Yes'

currency_format = '${:,}'

input_adjust_score = 'Adjust score'
input_cash_values = 'Enter numbers separated by any whitespace'
input_custom = 'Enter custom cash value'
input_min_win = 'Enter a number (default $1,000)'
input_name = 'Edit player name'
input_vowel_price = 'Enter a number (default $250)'

label_category = 'Category'
label_clue = 'Clue'
label_delete_all_puzzles = 'Delete all puzzles?'
label_delete_puzzle = 'Delete puzzle "{}"?'
label_file_exists = 'File "{}" already exists. Overwrite?'
label_filename = 'File name:'
label_matches = '{matches} "{letter}"s'
label_min_win = 'Round Prize\nMinimum'
label_name = 'Name'
label_name_exists = 'A puzzle with the name "{}" already exists.\nOverwrite?'
label_names_exist = 'The following puzzles already exist:\n{}\n\nOverwrite?'
label_no_export_selected = 'No puzzles were selected. Export all?'
label_vowel_price = 'Vowel Price'
label_wedges = 'Cash Values'

mgr_btn_bank = 'Bank Score'
mgr_btn_bankrupt = 'Bankrupt'
mgr_btn_clear = 'Clear puzzle'
mgr_btn_lose_turn = 'Lose a\nTurn'
mgr_btn_reveal = 'Solve Puzzle'
mgr_btn_tossup = 'Start\nToss-Up'
mgr_btn_tossup_stop = 'Stop\nToss-Up'
mgr_label_clue = 'Clue: '
mgr_select_value = 'Select cash value'
mgr_title_settings = 'Settings'

title_choose_letter = 'Choose a letter'
title_delete_puzzle = 'Delete puzzle'
title_delete_all_puzzles = 'Delete all puzzles'
title_duplicates = 'Duplicate puzzles found'
title_file_exists = 'File exists'
title_import_error = 'Unable to import'
title_name_exists = 'Name exists'
title_names_exist = 'Puzzles already exist'
title_no_export_selected = 'No puzzles selected'
title_save_puzzle = 'Save puzzle'
title_select_puzzle = 'Select puzzle'

label_import_duplicates = (
    'The following puzzles were encountered more than once:\n'
    '{}\n\n'
    'Only the first instance of each puzzle is recorded\n'
    '(puzzles with the same text, but different spacing,\n'
    'are considered to be duplicates).')
label_import_error = (
    'The following file(s) could not be imported:\n'
    '{}\n\n'
    'Files must consist of tab-separated values, with the form:\n'
    '{{puzzle}} {{category}} ({{clue}})')

dir_assets = os.path.join(os.path.dirname(__file__),
    r'assets')
file_panel = os.path.join(dir_assets,
    r'panel.png')
file_panel_blue = os.path.join(dir_assets,
    r'panel_blue.png')
file_panel_white = os.path.join(dir_assets,
    r'panel_white.png')
file_panel_corner = os.path.join(dir_assets,
    r'panel_corner.png')
file_category_background = os.path.join(dir_assets,
    r'category_background.png')
file_settings_icon = os.path.join(dir_assets,
    r'settings.png')

file_settings = r'settings.json'
