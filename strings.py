import os

button_close = 'Close'
button_confirm = 'Confirm'
button_guess_letter = 'Guess\nLetter'
button_delete_all = 'Delete All'
button_fullscreen = 'Toggle\nFullscreen'
button_load = 'Load'
button_no = 'No'
button_save = 'Save'
button_yes = 'Yes'

input_adjust_score = 'Adjust score'
input_cash_values = 'Enter numbers separated by any whitespace'
input_custom = 'Enter custom cash value'
input_min_win = 'Enter a number (default $1,000)'
input_name = 'Edit player name'
input_vowel_price = 'Enter a number (default $250)'

label_category = 'Category'
label_clue = 'Clue'
label_delete_puzzle = 'Delete puzzle "{}"?'
label_matches = '{matches} "{letter}"s'
label_min_win = 'Round Prize\nMinimum'
label_name = 'Name'
label_name_exists = 'A puzzle with the name "{}" already exists.\nOverwrite?'
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
title_name_exists = 'Name exists'
title_save_puzzle = 'Save puzzle'
title_select_puzzle = 'Select puzzle'

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
