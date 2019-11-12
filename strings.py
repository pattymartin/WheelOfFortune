alphabet = 'abcdefghijklmnopqrstuvwxyz'
vowels = 'aeiou'
consonants = ''.join([c for c in alphabet if c not in vowels])

bonus_round_letters = 'RSTLNE'

button_bank = 'Bank Score'
button_bankrupt = 'Bankrupt'
button_buy_vowel = 'Buy a\nVowel'
button_clear = 'Clear Puzzle'
button_clear_puzzles = 'Clear puzzles'
button_close = 'Close'
button_clue_solve = 'Clue\nSolve'
button_confirm = 'Confirm'
button_default = 'Default'
button_edit_hotkeys = 'Hotkeys'
button_export = 'Export'
button_delete_all = 'Delete All'
button_final_spin = 'Final\nSpin'
button_fullscreen = 'Toggle\nFullscreen'
button_increase_score = 'Add Value\n× {}'
button_load = 'Import'
button_lose_turn = 'Lose a\nTurn'
button_next_puzzle = 'Next Puzzle'
button_no = 'No'
button_ok = 'OK'
button_player_wins = '{}\nwins'
button_player1 = 'Player 1'
button_player2 = 'Player 2'
button_player3 = 'Player 3'
button_reveal = 'Reveal'
button_save = 'Save'
button_select_puzzle = 'Select Puzzle'
button_select_puzzles = 'Select puzzles'
button_solve = 'Solve'
button_timer_pause = 'Pause'
button_timer_reset = 'Reset'
button_timer_resume = 'Resume'
button_timer_start = 'Final Spin\nTimer'
button_tossup = 'Toss-Up'
button_tossup_stop = 'Stop\nToss-Up'
button_yes = 'Yes'

currency_format = '${:,}'
dropdown_select_value = 'Select cash value'

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
label_hotkey_buy_vowel = 'Buy a Vowel:'
label_hotkey_buzzer = 'Buzzer:'
label_hotkey_clear_puzzle = 'Clear puzzle:'
label_hotkey_increase_score = 'Increase score:'
label_hotkey_lose_turn = 'Lose a turn:'
label_hotkey_select_1 = 'Select player 1:'
label_hotkey_select_2 = 'Select player 2:'
label_hotkey_select_3 = 'Select player 3:'
label_hotkey_select_next = 'Select next player:'
label_hotkey_select_puzzle = 'Select puzzle:'
label_hotkey_solve = 'Solve/Next puzzle:'
label_hotkey_start_tossup = 'Toss-Up/Final Spin:'
label_hotkey_timer_reset = 'Reset timer:'
label_hotkey_timer_start = 'Start timer:'
label_import_duplicates = (
    'The puzzles below were encountered more than once.\n'
    'Only the first instance of each puzzle is recorded\n'
    '(puzzles with the same text, but different spacing,\n'
    'are considered to be duplicates).\n\n'
    '{}')
label_import_game_error = (
    'The following file could not be imported:\n'
    '{}\n\n'
    'Files must consist of tab-separated values, with the form:\n'
    '{{round_type}} {{round_reward}} {{puzzle}} {{category}} ({{clue}})')
label_import_puzzle_error = (
    'The following file(s) could not be imported:\n'
    '{}\n\n'
    'Files must consist of tab-separated values, with the form:\n'
    '{{puzzle}} {{category}} ({{clue}})')
label_manager_clue = 'Clue: '
label_matches = '{matches} "{letter}"s'
label_min_win = 'Round Prize\nMinimum'
label_name = 'Name'
label_name_exists = 'A puzzle with the name "{}" already exists.\nOverwrite?'
label_names_exist = 'The puzzles below already exist. Overwrite?\n\n{}'
label_no_export_selected = 'No puzzles were selected. Export all?'
label_puzzle = 'Puzzle'
label_reward = 'Reward'
label_round_type = 'Round Type'
label_select_tiebreaker = (
    'Tie! Select a puzzle to use as a tiebreaker tossup,\n'
    'or manually select a winner.')
label_time_out = 'Time is up!'
label_timer = 'Time remaining: {}:{:02}'
label_timer_set = 'Final Spin\nTimer:'
label_vowel_price = 'Vowel Price'
label_wedges = 'Cash Values'

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
title_settings = 'Settings'
title_tie = 'Tie'

round_type_bonus = 'Bonus'
round_type_express = 'Express'
round_type_mystery = 'Mystery'
round_type_speedup = 'Speed-Up'
round_type_standard = 'Standard'
round_type_tossup = 'Toss-Up'
round_type_triple_tossup = 'Triple Toss-Up 1-2'
round_type_triple_tossup_final = 'Triple Toss-Up 3'

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
