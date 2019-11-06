import os

alphabet = 'abcdefghijklmnopqrstuvwxyz'

bonus_round_letters = 'RSTLNE'

button_bonus_round = 'Bonus\nRound'
button_buy_vowel = 'Buy a\nVowel'
button_clear_puzzles = 'Clear puzzles'
button_close = 'Close'
button_clue_solve = 'Clue\nSolve'
button_confirm = 'Confirm'
button_default = 'Default'
button_edit_hotkeys = 'Hotkeys'
button_export = 'Export'
button_guess_letter = 'Guess\nLetter'
button_delete_all = 'Delete All'
button_final_spin = 'Final\nSpin'
button_fullscreen = 'Toggle\nFullscreen'
button_load = 'Import'
button_next_puzzle = 'Next Puzzle'
button_no = 'No'
button_ok = 'OK'
button_reveal = 'Reveal'
button_save = 'Save'
button_select_puzzle = 'Select Puzzle'
button_select_puzzles = 'Select puzzles'
button_timer_pause = 'Pause'
button_timer_reset = 'Reset'
button_timer_resume = 'Resume'
button_timer_start = 'Final Spin\nTimer'
button_yes = 'Yes'

currency_format = '${:,}'

input_adjust_score = 'Adjust score'
input_cash_values = 'Enter numbers separated by any whitespace'
input_custom = 'Enter custom cash value'
input_name = 'Edit player name'

label_category = 'Category'
label_clue = 'Clue'
label_clue_solve_reward = 'Clue Solve\nReward'
label_delete_all_puzzles = 'Delete all puzzles?'
label_delete_puzzle = 'Delete puzzle "{}"?'
label_edit_hotkey_info = (
    'Click on a hotkey to change it.\n'
    'Letters A-Z (without modifiers) are reserved for guessing letters.\n'
    'Press Escape to remove a hotkey.')
label_edit_hotkey_waiting = 'Waiting... {}'
label_exit_app = 'Exit app?'
label_file_exists = 'File "{}" already exists. Overwrite?'
label_filename = 'File name:'
label_final_spin_bonus = 'Final Spin\nBonus'
label_hotkey_bank_score = 'Bank score:'
label_hotkey_bankrupt = 'Bankrupt:'
label_hotkey_bonus_round = 'Bonus Round:'
label_hotkey_buy_vowel = 'Buy a Vowel:'
label_hotkey_clear_puzzle = 'Clear puzzle:'
label_hotkey_lose_turn = 'Lose a turn:'
label_hotkey_select_1 = 'Select player 1:'
label_hotkey_select_2 = 'Select player 2:'
label_hotkey_select_3 = 'Select player 3:'
label_hotkey_select_next = 'Select next player:'
label_hotkey_select_puzzle = 'Select puzzle:'
label_hotkey_solve = 'Solve/Next puzzle:'
label_hotkey_start_tossup = 'Start Toss-Up/Final Spin:'
label_hotkey_timer_reset = 'Reset timer:'
label_hotkey_timer_start = 'Start timer:'
label_matches = '{matches} "{letter}"s'
label_min_win = 'Round Prize\nMinimum'
label_name = 'Name'
label_name_exists = 'A puzzle with the name "{}" already exists.\nOverwrite?'
label_names_exist = 'The puzzles below already exist. Overwrite?\n\n{}'
label_no_export_selected = 'No puzzles were selected. Export all?'
label_puzzle = 'Puzzle'
label_reward = 'Reward'
label_round_type = 'Round Type'
label_time_out = 'Time is up!'
label_timer = 'Time remaining: {}:{:02}'
label_timer_set = 'Final Spin\nTimer:'
label_vowel_price = 'Vowel Price'
label_wedges = 'Cash Values'

mgr_btn_bank = 'Bank Score'
mgr_btn_bankrupt = 'Bankrupt'
mgr_btn_clear = 'Clear Puzzle'
mgr_btn_lose_turn = 'Lose a\nTurn'
mgr_btn_reveal = 'Solve'
mgr_btn_tossup = 'Toss-Up'
mgr_btn_tossup_stop = 'Stop\nToss-Up'
mgr_label_clue = 'Clue: '
mgr_select_value = 'Select cash value'
mgr_title_settings = 'Settings'

title_bonus_round = 'Bonus Round'
title_choose_letter = 'Choose a letter'
title_delete_puzzle = 'Delete puzzle'
title_delete_all_puzzles = 'Delete all puzzles'
title_duplicates = 'Duplicate puzzles found'
title_edit_hotkeys = 'Edit hotkeys'
title_exit_app = 'Exit app'
title_file_exists = 'File exists'
title_import_error = 'Unable to import'
title_name_exists = 'Name exists'
title_names_exist = 'Puzzles already exist'
title_no_export_selected = 'No puzzles selected'
title_save_puzzle = 'Save puzzle'
title_select_game = 'Select game'
title_select_puzzle = 'Select puzzle'

round_type_bonus = 'Bonus'
round_type_express = 'Express'
round_type_mystery = 'Mystery'
round_type_speedup = 'Speed-Up'
round_type_standard = 'Standard'
round_type_tossup = 'Toss-Up'
round_type_triple_tossup = 'Triple Toss-Up 1-2'
round_type_triple_tossup_final = 'Triple Toss-Up 3'

label_import_duplicates = (
    'The puzzles below were encountered more than once.\n'
    'Only the first instance of each puzzle is recorded\n'
    '(puzzles with the same text, but different spacing,\n'
    'are considered to be duplicates).\n\n'
    '{}')
label_import_error = (
    'The following file(s) could not be imported:\n'
    '{}\n\n'
    'Files must consist of tab-separated values, with the form:\n'
    '{{puzzle}} {{category}} ({{clue}})')

dir_assets = os.path.join(os.path.dirname(__file__),
    r'assets')
file_alert_icon = os.path.join(dir_assets,
    r'alert.png')
file_cancel_icon = os.path.join(dir_assets,
    r'cancel.png')
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
file_sound_bankrupt = os.path.join(dir_assets,
    r'bankrupt.mp3')
file_sound_buzz = os.path.join(dir_assets,
    r'buzz.wav')
file_sound_clue_correct = os.path.join(dir_assets,
    r'clue_correct.wav')
file_sound_ding = os.path.join(dir_assets,
    r'ding.wav')
file_sound_no_more_consonants = os.path.join(dir_assets,
    r'no_more_consonants.wav')
file_sound_no_more_vowels = os.path.join(dir_assets,
    r'no_more_vowels.wav')
file_sound_reveal_puzzle = os.path.join(dir_assets,
    r'puzzle_reveal.wav')
file_sound_reveal_tossup = os.path.join(dir_assets,
    r'tossup_reveal.wav')
file_sound_solve = os.path.join(dir_assets,
    r'solve.wav')
file_sound_solve_bonus = os.path.join(dir_assets,
    r'bonus_round_solve.wav')
file_sound_solve_clue = os.path.join(dir_assets,
    r'clue_solve.wav')
file_sound_solve_tossup = os.path.join(dir_assets,
    r'tossup_solve.wav')
file_sound_solve_triple_tossup = os.path.join(dir_assets,
    r'triple_tossup_1-2_solve.wav')

dir_kv = os.path.join(os.path.dirname(__file__),
    r'kv')
file_kv_manager = os.path.join(dir_kv,
    r'ManagerLayout.kv')
file_kv_my_widgets = os.path.join(dir_kv,
    r'MyWidgets.kv')
file_kv_prompts = os.path.join(dir_kv,
    r'Prompts.kv')

file_settings = r'settings.json'

# circular import, can't import at top
import values

input_clue_solve_reward = 'Enter a number (default {})'.format(
    currency_format.format(values.default_clue_solve_reward))
input_final_spin_bonus = 'Enter a number (default {})'.format(
    currency_format.format(values.default_final_spin_bonus))
input_min_win = 'Enter a number (default {})'.format(
    currency_format.format(values.default_min_win))
input_vowel_price = 'Enter a number (default {})'.format(
    currency_format.format(values.default_vowel_price))
