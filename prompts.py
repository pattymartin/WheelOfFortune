import os

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup

import data_caching
import strings
import values
from my_widgets import KeyboardBindable

Builder.load_file(values.file_kv_prompts)


class SavePuzzlePrompt(Popup):
    """A Popup prompting the user to save a puzzle."""

    def __init__(self, puzzle, **kwargs):
        """
        Create the Popup.

        :param puzzle: The puzzle as a string
        :type puzzle: str
        :param kwargs: Additional keyword arguments for the Popup
        """

        super(SavePuzzlePrompt, self).__init__(**kwargs)
        self.puzzle = puzzle

    def input_save(self):
        """
        Get text from the input fields and save the puzzle.

        :return: None
        """

        category = self.cat_input.text
        clue = self.clue_input.text

        if category:
            puzzle_dict = {
                'category': category,
                'clue': clue,
                'puzzle': self.puzzle}
            data_caching.add_puzzle(' '.join(self.puzzle.split()), puzzle_dict)
            self.dismiss()
        else:
            self.cat_label.color = values.color_red


class LoadGamePrompt(Popup):
    """A Popup to prompt the user to create a game."""

    def __init__(self, callback, **kwargs):
        """
        Create the Popup.

        When the game has been selected, it will be passed to `callback`
        as a game list.
        See :func:`data_caching.export_game` for a description of
        game lists.

        :param callback: A function that can accept a list of dicts
        :type callback: function
        :param kwargs: Additional keyword arguments for the Popup
        """

        super(LoadGamePrompt, self).__init__(**kwargs)
        self.callback = callback

        settings = data_caching.get_variables()
        self.order = settings.get('game_order', values.default_game_order)
        self.rewards = settings.get(
            'game_rewards', values.default_game_rewards)
        self.puzzles = []

        self.fill_puzzle_layout()

    def fill_puzzle_layout(self):
        """
        Fill the layout with the selected puzzles.

        :return: None
        """

        self.puzzle_layout.clear_widgets()

        # to make sure the button is only added once
        select_button_added = False

        for i, (round_type, reward) in enumerate(zip(
                self.order, self.rewards)):

            selection_callback = None
            try:
                puzzle = ' '.join(self.puzzles[i]['puzzle'].split())
            except IndexError:
                puzzle = ''
                if not select_button_added:
                    selection_callback = self.puzzles_selected
                    select_button_added = True
            psl = PuzzleSelectionLayout(
                i + 1, puzzle, round_type, reward,
                selection_callback=selection_callback)
            psl.round_type_spinner.bind(
                text=lambda instance, val: self.update_values())
            psl.reward_input.bind(
                text=lambda instance, val: self.update_values())
            self.puzzle_layout.add_widget(psl)

    def puzzles_selected(self, puzzles):
        """
        Add selected puzzles to the layout.

        `puzzles` is a list of puzzle dicts.
        See :func:`data_caching.add_puzzle` for a description of
        puzzle dicts.

        :param puzzles: A list of puzzle dicts
        :type puzzles: list
        :return: None
        """

        self.puzzles.extend(puzzles)
        self.fill_puzzle_layout()

    def clear_puzzles(self):
        """
        Remove all puzzles from the puzzle layout.

        :return: None
        """

        self.puzzles = []
        self.fill_puzzle_layout()

    def add_round(self):
        """
        Add another row to the puzzle layout.

        :return: None
        """

        self.order.append(strings.round_type_standard)
        self.rewards.append('0')
        self.fill_puzzle_layout()

    def remove_round(self):
        """
        Remove the last row from the puzzle layout.

        :return: None
        """

        self.order.pop(-1)
        self.rewards.pop(-1)
        self.fill_puzzle_layout()

    def import_game(self):
        """
        Prompt the user to select a file containing a game. When a file
        is chosen, it will be displayed in the layout.

        :return: None
        """

        FileChooserPrompt(
            self.import_game_from_file,
            multiselect=False
        ).open()

    def import_game_from_file(self, filenames):
        """
        Import a game from a selected file. This function accepts a list
        of filenames from a :class:`FileChooserPrompt` but only
        uses the first item in the list.

        The imported game will be displayed in the layout.

        :param filenames: A list of filename strings
        :type filenames: list
        :return: None
        """

        if filenames:
            filename = filenames[0]

            order = []
            rewards = []
            puzzles = []

            for puzzle in data_caching.import_game(filename):
                order.append(puzzle['round_type'])
                rewards.append(puzzle['round_reward'])
                puzzles.append(puzzle['puzzle'])

            if order and rewards and puzzles:
                self.order = order
                self.rewards = rewards
                self.puzzles = puzzles

            self.fill_puzzle_layout()

    def export_game(self):
        """
        Prompt the user to select a file. The displayed game will be
        saved to the selected file.

        :return: None
        """

        def file_selected(filename):
            """
            Create a game list and write it to the selected file.

            :param filename: The name of a file
            :type filename: str
            :return: None
            """

            data_caching.export_game(filename, self.create_game())

        FileSaverPrompt(file_selected).open()

    def update_values(self):
        """
        Update `order` and `values` to reflect the values selected by
        the user. This is called every time the user changes a value.

        :return: None
        """

        self.order = []
        self.rewards = []

        for child in self.puzzle_layout.children[::-1]:
            try:
                round_type = child.round_type_spinner.text
                round_reward = data_caching.str_to_int(child.reward_input.text)

                if not round_type:
                    round_type = strings.round_type_standard
                if not round_reward:
                    round_reward = '0'

                self.order.append(round_type)
                self.rewards.append(round_reward)
            except AttributeError:
                # not a PuzzleSelectionLayout
                continue

    def create_game(self):
        """
        Create a game list from the selected puzzles.
        See :func:`data_caching.export_game` for a description of
        game lists.

        :return: A game list
        :rtype: list
        """

        return [
            {
                'puzzle': puzzle,
                'round_type': round_type,
                'round_reward': round_reward}
            for puzzle, round_type, round_reward
            in zip(self.puzzles, self.order, self.rewards)]

    def confirm(self):
        """
        Create a game list from the selected files and pass the list to
        `callback`.
        See :func:`data_caching.export_game` for a description of
        game lists.

        :return: None
        """

        data_caching.update_variables({
            'game_order': self.order,
            'game_rewards': self.rewards})
        self.callback(self.create_game())
        self.dismiss()


class PuzzleSelectionLayout(BoxLayout):
    """
    A Layout to define what a row in the :class:`LoadGamePrompt`
    looks like.
    """

    def __init__(self, number, puzzle, round_type, reward,
                 selection_callback, **kwargs):
        """
        Create the layout.

        This layout contains a button to select puzzles to add to the
        :class:`LoadGamePrompt` layout. When puzzles are selected,
        they will be passed to `selection_callback` as a list of puzzle
        dicts.
        See :func:`data_caching.add_puzzle` for a description of
        puzzle dicts.

        :param number: The index displayed at the left of the layout
        :type number: int
        :param puzzle: The name of a puzzle
        :type puzzle: str
        :param round_type: The type of puzzle for this round
        :type round_type: str
        :param reward: The reward for solving the puzzle
        :type reward: int
        :param selection_callback: A function accepting a list
        :type selection_callback: function
        :param kwargs: Additional keyword arguments for the layout
        """

        super(PuzzleSelectionLayout, self).__init__(**kwargs)
        self.number = str(number)
        self.puzzle = str(puzzle)
        self.round_type = str(round_type)
        self.reward = str(reward)
        self.selection_callback = selection_callback

    def select_clicked(self):
        """
        Launch the LoadPuzzlePrompt, using `selection_callback` as the
        callback.

        :return: None
        """

        if self.selection_callback:
            LoadPuzzlePrompt(self.selection_callback).open()


class LoadPuzzlePrompt(Popup):
    """A Popup to prompt the user to select puzzles by name."""

    selected_names = []
    all_puzzles = {}

    def __init__(self, callback, **kwargs):
        """
        Create the Popup.

        When puzzles are selected, they will be passed to `callback` as
        a list of puzzle dicts.
        See :func:`data_caching.add_puzzle` for a description of
        puzzle dicts.

        :param callback: A function accepting a list of puzzle dicts
        :type callback: function
        :param kwargs: Additional keyword arguments for the Popup
        """

        super(LoadPuzzlePrompt, self).__init__(**kwargs)

        self.callback = callback
        self.fill_puzzle_layout()

    def fill_puzzle_layout(self, _instance=None):
        """
        Fill in the layout with existing puzzles.

        :param _instance: A Popup instance, defaults to None
        :type _instance: kivy.uix.popup.Popup, optional
        :return: None
        """

        self.puzzle_layout.clear_widgets()
        self.selected_names = []

        self.all_puzzles = data_caching.read_puzzles()
        for name in self.all_puzzles.keys():
            button = PuzzleButton(
                name, self.puzzle_selected, self.fill_puzzle_layout)
            self.puzzle_layout.add_widget(button)

    def input_save(self):
        """
        Get the selected puzzles, and pass them to `callback` as a list
        of puzzle dicts.
        See :func:`data_caching.add_puzzle` for a description of
        puzzle dicts.

        :return: None
        """

        selected_puzzles = [
            self.all_puzzles[name] for name in self.selected_names]
        if selected_puzzles:
            self.callback(selected_puzzles)

        self.dismiss()

    def import_puzzles(self):
        """
        Prompt the user to select a file containing puzzles. When a file
        is selected, the puzzles will be imported and displayed in the
        layout.

        :return: None
        """

        FileChooserPrompt(
            data_caching.import_puzzles,
            on_dismiss=self.fill_puzzle_layout).open()

    def export_puzzles(self):
        """
        Prompt the user to select a file. The selected puzzles will be
        saved to the selected file.

        :return: None
        """

        def file_selected(filename):
            """
            Save the selected puzzles to the selected file.

            :param filename: The name of a file
            :type filename: str
            :return: None
            """

            data_caching.export_puzzles_by_name(filename, self.selected_names)

        FileSaverPrompt(file_selected).open()

    def prompt_delete_all(self):
        """
        Prompt the user to delete all puzzles.

        :return: None
        """

        def confirm_delete():
            """
            Delete all puzzles.

            :return: None
            """

            data_caching.delete_all_puzzles()
            # reload layout to reflect deletion
            self.fill_puzzle_layout()

        YesNoPrompt(
            strings.label_delete_all_puzzles,
            yes_callback=confirm_delete,
            title=strings.title_delete_all_puzzles
        ).open()

    def puzzle_selected(self, name):
        """
        Add `name` to `self.selected_names`, or remove if it is already
        there.

        :param name: The name of a puzzle
        :type name: str
        :return: None
        """

        if name in self.selected_names:
            self.selected_names.remove(name)
        else:
            self.selected_names.append(name)


class PuzzleButton(BoxLayout):
    """
    A layout containing a ToggleButton to select a puzzle, and a button
    to delete the puzzle.
    """

    def __init__(self, name, selection_callback, deletion_callback, **kwargs):
        """
        Create the layout.

        `name` will be passed to `selection_callback` when the
        ToggleButton is toggled.
        If the puzzle is deleted, `deletion_callback` will be called
        afterwards.

        :param name: The name of the puzzle
        :type name: str
        :param selection_callback: A function accepting a string
        :type selection_callback: function
        :param deletion_callback: A function with no arguments
        :type deletion_callback: function
        :param kwargs: Additional keyword arguments for the layout
        """

        super(PuzzleButton, self).__init__(**kwargs)
        self.toggle_button.text = name
        self.selection_cb = selection_callback
        self.deleted_cb = deletion_callback

    def prompt_delete_puzzle(self):
        """
        Prompt the user to delete the puzzle whose name is displayed in
        this layout.

        :return: None
        """

        def confirm_delete():
            """
            Delete the puzzle.

            :return: None
            """

            data_caching.delete_puzzle(self.toggle_button.text)
            self.deleted_cb()

        YesNoPrompt(
            strings.label_delete_puzzle.format(
                self.toggle_button.text),
            yes_callback=confirm_delete,
            title=strings.title_delete_puzzle
        ).open()


class YesNoPrompt(Popup):
    """
    A Popup prompting the user with text, with yes and no buttons.
    """

    def __init__(self, text, yes_callback=None, no_callback=None,
                 **kwargs):
        """
        Create the Popup.

        :param text: Text displayed in the Popup
        :type text: str
        :param yes_callback: Function called when 'yes' is clicked,
                             defaults to None
        :type yes_callback: function, optional
        :param no_callback: Function called when 'no' is clicked,
                            defaults to None
        :type no_callback: function, optional
        :param kwargs: Additional keyword arguments for the Popup
        """

        super(YesNoPrompt, self).__init__(**kwargs)
        self.scroll_label.label_text = text
        self.no_callback = no_callback
        self.yes_callback = yes_callback


class ChooseLetterPrompt(Popup, KeyboardBindable):
    """A Popup asking the user to choose a letter."""

    def __init__(self, letter_callback, unavailable_letters=None, **kwargs):
        """
        Create the Popup.

        When a letter is chosen, it will be passed to `letter_callback`
        as a single-character string.

        Letters in the list `unavailable_letters` will not be shown in
        the layout.

        :param letter_callback: A function accepting a string
        :type letter_callback: function
        :param unavailable_letters: A list of unavailable letters,
                                    defaults to None
        :type unavailable_letters: list, optional
        :param kwargs: Additional keyword arguments for the Popup
        """

        self.letter_callback = letter_callback
        self.unavailable_letters = (
            unavailable_letters if unavailable_letters is not None else [])
        super(ChooseLetterPrompt, self).__init__(**kwargs)

    def letter_chosen(self, letter):
        """
        Pass `letter` to `letter_callback` and dismiss this Popup.

        :param letter: A single-character string
        :type letter: str
        :return: None
        """

        self.letter_callback(letter)
        self.dismiss()

    def _on_keyboard_down(self, _keyboard, keycode, _text, _modifiers):
        """
        If a letter is pressed, pass the letter to `letter_chosen`.

        :param _keyboard: A Keyboard
        :type _keyboard: kivy.core.window.Keyboard
        :param keycode: An integer and a string representing the keycode
        :type keycode: tuple
        :param _text: The text of the pressed key
        :type _text: str
        :param _modifiers: A list of modifiers
        :type _modifiers: list
        :return: None
        """

        letter = keycode[1]
        if letter.lower() in self.unavailable_letters:
            return
        self.letter_chosen(letter)


class ManagerSettingsPrompt(Popup):
    """A Popup with settings for the manager."""

    def input_save(self):
        """
        Get values from the input fields and save them to settings.

        :return: None
        """

        timer_minutes = data_caching.str_to_int(self.timer_input.text[:-2])
        timer_seconds = data_caching.str_to_int(self.timer_input.text[-2:])
        if not (timer_minutes or timer_seconds):
            timer_time = ''
        else:
            timer_time = '{}:{:02}'.format(timer_minutes, timer_seconds)

        vowel_price = data_caching.str_to_int(self.vowel_input.text, None)
        min_win = data_caching.str_to_int(self.min_input.text, None)
        clue_solve_reward = data_caching.str_to_int(
            self.clue_reward_input.text, None)
        final_spin_bonus = data_caching.str_to_int(
            self.final_spin_bonus_input.text, None)
        cash_values = [data_caching.str_to_int(line, None)
                       for line in self.wedges_input.text.split()]

        data_caching.update_variables({
            'timer_time': timer_time,
            'vowel_price': vowel_price if vowel_price is not None else '',
            'min_win': min_win if min_win is not None else '',
            'clue_solve_reward':
                clue_solve_reward if clue_solve_reward is not None else '',
            'final_spin_bonus':
                final_spin_bonus if final_spin_bonus is not None else '',
            'cash_values': sorted([v for v in cash_values if v is not None])})

        self.dismiss()

    @staticmethod
    def edit_hotkeys():
        """
        Prompt the user to edit hotkeys.

        :return: None
        """

        EditHotkeysPrompt(title=strings.title_edit_hotkeys).open()


class EditHotkeysPrompt(Popup):
    """
    A Popup allowing the user to define hotkeys for several app actions.
    """

    def __init__(self, **kwargs):
        """
        Create the Popup.

        :param kwargs: Keyword arguments for the Popup
        """

        super(EditHotkeysPrompt, self).__init__(**kwargs)

        self.problem_hotkeys = []
        existing_hotkeys = data_caching.get_hotkeys()

        for hotkey in values.hotkeys:
            layout = HotkeyLayout(
                hotkey['name'],
                hotkey['description'],
                hotkey_text=existing_hotkeys.get(
                    hotkey['name'], hotkey['default']
                ).title())
            layout.bind(
                hotkey_text=lambda i, v: self.check_for_problems())
            self.hotkey_layout.add_widget(layout)

    def check_for_problems(self):
        """
        Check the hotkeys entered to make sure that there are no
        duplicates, and that none are set to the letters A-Z.
        If any problems are found, display an alert icon next to
        problematic hotkeys.

        :return: None
        """

        invalid_hotkeys = list(strings.alphabet)
        self.problem_hotkeys = []

        for layout in self.hotkey_layout.children[::-1]:
            hotkey = layout.hotkey_text_label.text.lower()
            if not hotkey:
                continue
            elif hotkey not in invalid_hotkeys:
                invalid_hotkeys.append(hotkey)
            else:
                self.problem_hotkeys.append(hotkey)

        for layout in self.hotkey_layout.children[::-1]:
            hotkey = layout.hotkey_text_label.text.lower()
            if hotkey and hotkey in self.problem_hotkeys:
                layout.warning = True
            else:
                layout.warning = False

    def confirm(self):
        """
        Confirm the hotkeys defined by the user.

        :return: None
        """

        if not self.problem_hotkeys:
            data_caching.write_hotkeys({
                layout.name: layout.hotkey_text_label.text.lower()
                for layout in self.hotkey_layout.children[::-1]})
            self.dismiss()


class HotkeyLayout(BoxLayout):
    """
    A single row in the hotkeys layout of an
    :class:`EditHotkeysPrompt`. Contains a description of a hotkey, a
    :class:`RecordHotkeyLabel`, and a button to reset the hotkey to
    default.
    """

    def __init__(self, name, description, hotkey_text, **kwargs):
        """
        Create the layout.

        :param name: The name defining this hotkey in the settings
        :type name: str
        :param description: Text identifying the hotkey for the user
        :type description: str
        :param hotkey_text: Text representation of the keystroke
        :type hotkey_text: str
        :param kwargs: Additional keyword arguments for the layout
        """

        super(HotkeyLayout, self).__init__(**kwargs)
        self.name = name
        self.description = description
        self.hotkey_text_label.text = hotkey_text


class RecordHotkeyLabel(ButtonBehavior, Label, KeyboardBindable):
    """
    A Label which, when clicked, will record a key combination, and set
    its text to indicate the key combination.

    After the label is clicked, it will wait for a key combination for a
    maximum time defined by `values.edit_hotkey_timeout`.
    """

    def __init__(self, **kwargs):
        """
        Create the label.

        :param kwargs: Keyword arguments for the label
        """

        super(RecordHotkeyLabel, self).__init__(**kwargs)

        self.initial_text = ''
        self.hotkey_entered = False
        self.seconds_left = 0

    def default(self):
        """
        Set the hotkey to its default.

        :return: None
        """

        for hotkey in values.hotkeys:
            if hotkey['name'] == self.name:
                self.text = hotkey['default'].title()
                return
        self.text = ''

    def start_listening(self):
        """
        Start waiting for the user to press a key.

        :return: None
        """

        self.get_keyboard()

        # get current text, set back to this if out of time
        self.initial_text = self.text
        self.hotkey_entered = False
        self.seconds_left = values.edit_hotkey_timeout
        self.text = strings.label_edit_hotkey_waiting.format(self.seconds_left)
        Clock.schedule_once(self.clock_tick, 1)

    def clock_tick(self, _dt):
        """
        Update text to indicate how much time is left. If time is up,
        release the keyboard and change the label's text back to its
        original value.

        :param _dt: The time elapsed between scheduling and calling
        :type _dt: float
        :return: None
        """

        if not self.hotkey_entered:
            self.seconds_left -= 1

            if self.seconds_left <= 0:  # time up
                self.text = self.initial_text
                self._keyboard.release()
            else:
                self.text = strings.label_edit_hotkey_waiting.format(
                    self.seconds_left)
                Clock.schedule_once(self.clock_tick, 1)

    def _on_keyboard_down(self, keyboard, keycode, _text, modifiers):
        """
        Check the keys pressed. If a valid key combination is detected,
        display the new hotkey and release the keyboard.

        :param keyboard: A Keyboard
        :type keyboard: kivy.core.window.Keyboard
        :param keycode: An integer and a string representing the keycode
        :type keycode: tuple
        :param _text: The text of the pressed key
        :type _text: str
        :param modifiers: A list of modifiers
        :type modifiers: list
        :return: True, to indicate that the key is consumed
        :rtype: bool
        """

        valid_modifiers = ['ctrl', 'alt', 'shift']

        # these characters cannot be used for hotkeys
        # (except as modifiers, in the case of ctrl, alt, and shift):
        invalid_chars = [
            'tab', 'rshift', 'shift', 'alt', 'rctrl', 'lctrl', 'super',
            'alt-gr', 'compose', 'capslock', 'escape', 'insert', 'numlock',
            'print', 'screenlock', 'ctrl']

        key = keycode[1]
        if key == 'escape':
            self.hotkey_entered = True
            self.text = ''
            keyboard.release()
        elif key not in invalid_chars:
            self.hotkey_entered = True
            mods = [mod for mod in valid_modifiers if mod in modifiers]
            self.text = '+'.join(mods + [key]).title()
            keyboard.release()
        return True


class FileChooserPrompt(Popup):
    """A Popup allowing the user to select files."""

    def __init__(self, callback, multiselect=True, **kwargs):
        """
        Create the Popup.

        When files have been selected, a list of filenames will be
        passed to `callback`.

        :param callback: A function accepting a list of strings
        :type callback: function
        :param multiselect: True if the user can select multiple files,
                            otherwise False, defaults to True
        :type multiselect: bool, optional
        :param kwargs: Additional keyword arguments for the Popup
        """

        self.callback = callback
        self.multiselect = multiselect

        self.chooser_path = data_caching.get_variables().get(
            'file_chooser_path', '')
        if not os.path.exists(self.chooser_path):
            self.chooser_path = os.getcwd()

        super(FileChooserPrompt, self).__init__(**kwargs)

    def confirm(self):
        """
        Pass the FileChooser's selection to `callback`.

        :return: None
        """

        self.callback(self.chooser.selection)
        data_caching.update_variables({
            'file_chooser_path': self.chooser.path})
        self.dismiss()


class FileSaverPrompt(Popup):
    """A Popup prompting the user to select a file to write to."""

    def __init__(self, callback, **kwargs):
        """
        Create the Popup.

        When a file is selected, the filename will be passed to
        `callback`.

        :param callback: A function accepting a string filename
        :type callback: function
        :param kwargs: Additional keyword arguments for the Popup
        """

        super(FileSaverPrompt, self).__init__(**kwargs)
        self.callback = callback

        self.chooser_path = data_caching.get_variables().get(
            'file_chooser_path', '')
        if not os.path.exists(self.chooser_path):
            self.chooser_path = os.getcwd()

    def input_save(self):
        """
        Get text from the input box and pass the selected filename to
        `callback`.

        :return: None
        """

        filename = self.filename_input.text

        if filename:
            self.callback(os.path.join(self.chooser.path, filename))
            data_caching.update_variables({
                'file_chooser_path': self.chooser.path})
            self.dismiss()
        else:
            self.filename_label.color = values.color_red


class InfoPrompt(Popup):
    """A simple Popup with text and one button to dismiss."""

    def __init__(self, text, **kwargs):
        """
        Create the Popup.

        :param text: Text to display to the user
        :type text: str
        :param kwargs: Additional keyword arguments for the Popup
        """

        super(InfoPrompt, self).__init__(**kwargs)
        self.label_text = text


class TiebreakerPrompt(Popup):
    """A Popup prompting the user to select a puzzle as a tiebreaker."""

    def __init__(self, load_tiebreaker_cb, select_player_cb,
                 eligible_players, player_names, **kwargs):
        """
        Create the Popup.

        If a tiebreaker puzzle is selected, it will be passed
        to `load_tiebreaker_cb` as a puzzle dict.
        See :func:`data_caching.add_puzzle` for a description of
        puzzle dicts.

        If a winner is manually selected instead,
        the number of the player will be passed to
        `select_player_cb`.

        :param load_tiebreaker_cb: A function accepting a puzzle dict
        :type load_tiebreaker_cb: function
        :param select_player_cb: A function accepting an int
        :type select_player_cb: function
        :param eligible_players: A list of eligible player numbers
        :type eligible_players: list
        :param player_names: A list of all players' names
        :type player_names: list
        :param kwargs: Additional keyword arguments for the Popup
        """

        super(TiebreakerPrompt, self).__init__(**kwargs)

        self.load_tiebreaker_cb = load_tiebreaker_cb
        self.select_player_cb = select_player_cb
        self.eligible_players = eligible_players
        self.player_names = player_names

        self.permission_to_dismiss = False
        self.bind(on_dismiss=self.dismiss_callback)

    def select_puzzle(self):
        """
        Open a LoadPuzzlePrompt.

        :return: None
        """

        def puzzles_chosen_callback(puzzles):
            """
            Get the puzzles chosen in the LoadPuzzlePrompt and pass the
            first one to `load_tiebreaker_cb`.

            :param puzzles: A list of puzzle dicts
            :type puzzles: dict
            :return: None
            """

            self.load_tiebreaker_cb(puzzles[0])
            self.permission_to_dismiss = True
            self.dismiss()

        LoadPuzzlePrompt(puzzles_chosen_callback).open()

    def dismiss_callback(self, _instance):
        """
        Prevent the Popup from closing until a choice has been made.

        :param _instance: A TiebreakerPrompt instance
        :type _instance: TiebreakerPrompt
        :return: True if the Popup will be kept open, otherwise False
        :rtype: bool
        """

        return not self.permission_to_dismiss
