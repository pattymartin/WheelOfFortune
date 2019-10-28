import json
import os

from kivy.lang import Builder
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.widget import Widget

import data_caching, strings, used_letters, values

Builder.load_file(strings.file_kv_prompts)

class SavePuzzlePrompt(Popup):
    """
    A Popup prompting the user to save a puzzle.
    """
    
    def __init__(self, puzzle, **kwargs):
        """Create the Popup."""
        super(SavePuzzlePrompt, self).__init__(**kwargs)
        self.puzzle = puzzle
        
    def input_save(self):
        """
        Get text from the input fields,
        and save the puzzle.
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
            cat_label.color = values.color_red

class LoadPuzzlePrompt(Popup):
    """
    A Popup to prompt the user to select a puzzle by name.
    The selected puzzle will then be passed to `callback`.
    `callback` should be a function accepting a dict
    with the keys 'category', 'clue', and 'puzzle'.
    """
    def __init__(self, callback, **kwargs):
        """Create the Popup."""
        super(LoadPuzzlePrompt, self).__init__(
            title=strings.title_select_puzzle, **kwargs)
        
        self.callback = callback
        self.create_layout()
    
    def create_layout(self, instance=None):
        content = BoxLayout(orientation='vertical')
        self.toggle_buttons = []
        self.selected_names = []
        
        content.add_widget(self._options_box())
        
        content.add_widget(Widget(size_hint_y=0.02))
        
        puzzle_layout = BoxLayout(orientation='vertical', size_hint_y=None)
        puzzle_layout.bind(minimum_height=puzzle_layout.setter('height'))
        puzzles = data_caching.read_puzzles()
        for name in puzzles.keys():
            puzzle_layout.add_widget(self._puzzle_button(name))
        puzzle_layout.add_widget(Widget())
        puzzle_scroll = ScrollView()
        puzzle_scroll.add_widget(puzzle_layout)
        content.add_widget(puzzle_scroll)
        
        content.add_widget(Widget(size_hint_y=0.02))
        
        button_layout = BoxLayout(orientation='horizontal')
        button_layout.size_hint_y = 0.25
        button_close = Button(text=strings.button_close)
        button_confirm = Button(text=strings.button_confirm)
        button_layout.add_widget(button_close)
        button_layout.add_widget(button_confirm)
        content.add_widget(button_layout)
        
        def input_save(instance):
            """
            Check which buttons are selected,
            then run `callback` on the first puzzle selected.
            """
            
            selected_puzzles = [puzzles[name] for name in self.selected_names]
            if selected_puzzles:
                self.callback(selected_puzzles[0])
            
            self.dismiss()
        
        button_close.bind(on_release=self.dismiss)
        button_confirm.bind(on_release=input_save)
        
        self.content = content
    
    def _options_box(self):
        """
        Create a layout containing buttons
        for puzzle management.
        """
        
        def prompt_delete_all(instance):
            """
            Prompt the user to delete all puzzles.
            """
            YesNoPrompt(
                    strings.label_delete_all_puzzles,
                    confirm_delete,
                    None,
                    title=strings.title_delete_all_puzzles
                ).open()
        
        def confirm_delete(instance):
            """
            Delete all puzzles.
            """
            data_caching.delete_all_puzzles()
            #reload layout to reflect deletion
            self.create_layout()
        
        def load_button_click(instance):
            """
            """
            prompt = FileChooserPrompt(data_caching.import_puzzles)
            prompt.bind(on_dismiss=self.create_layout)
            prompt.open()
        
        layout = BoxLayout(orientation='horizontal')
        
        btn_load = Button(text=strings.button_load)
        btn_load.bind(on_release=load_button_click)
        layout.add_widget(btn_load)
        
        btn_save = Button(text=strings.button_export)
        btn_save.bind(on_release=FileSaverPrompt(self.selected_names).open)
        layout.add_widget(btn_save)
        
        btn_delete_all = Button(text=strings.button_delete_all)
        btn_delete_all.bind(on_release=prompt_delete_all)
        layout.add_widget(btn_delete_all)
        
        layout.size_hint_y = 0.25
        
        return layout
    
    def _puzzle_button(self, name):  
        """
        Create a ToggleButton with text `name`,
        and a button to delete the puzzle.
        """
        
        def prompt_delete_puzzle(instance):
            """
            Prompt the user to delete the puzzle
            with the name `name`.
            """
            YesNoPrompt(
                    strings.label_delete_puzzle.format(
                        name),
                    confirm_delete,
                    None,
                    title=strings.title_delete_puzzle
                ).open()
        
        def confirm_delete(instance):
            """
            Delete the puzzle with the name `name`.
            """
            data_caching.delete_puzzle(name)
            # reload layout to reflect deletion
            self.create_layout()
        
        def select_name(instance):
            """
            Add `name` to `self.selected_names`,
            or remove if it is already there.
            """
            if name in self.selected_names:
                self.selected_names.remove(name)
            else:
                self.selected_names.append(name)
        
        layout = BoxLayout(orientation='horizontal')
        
        toggle_button = ToggleButton(text=name)
        self.toggle_buttons.append(toggle_button)
        toggle_button.bind(on_release=select_name)
        layout.add_widget(toggle_button)
        
        delete_button = Button(text='X')
        delete_button.size_hint_x = 0.1
        delete_button.bind(
            on_release=prompt_delete_puzzle)
        layout.add_widget(delete_button)
        
        layout.size_hint_y = None
        layout.height = 50
        
        return layout

class YesNoPrompt(Popup):
    """
    A Popup prompting the user with `text`,
    with yes and no buttons.
    Yes and no buttons are bound to `yes_callback` and `no_callback`
    respectively.
    """
    
    def __init__(self, text, yes_callback, no_callback, **kwargs):
        """Create the Popup."""
        super(YesNoPrompt, self).__init__(**kwargs)
        self.text_label.text = text
        self.button_no.bind(on_release=_wrap_with_dismiss(no_callback, self))
        self.button_yes.bind(on_release=_wrap_with_dismiss(yes_callback, self))

class ChooseLetterPrompt(Popup):
    """
    A Popup asking the user to choose a letter.
    """
    
    def __init__(self, callback, unavailable_letters=[], **kwargs):
        """Create the Popup."""
        super(ChooseLetterPrompt, self).__init__(
            title=strings.title_choose_letter, **kwargs)
        self.callback = _wrap_with_dismiss(callback, self)
        self.unavailable_letters = unavailable_letters
        letterboard = used_letters.LetterboardLayout(
            self.callback, unavailable=unavailable_letters)
        self.content = letterboard
    
    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        """Reveal the puzzle when the Enter key is pressed."""
        letter = keycode[1]
        if letter.lower() in self.unavailable_letters:
            return
        self.callback(letter)
    
    def _keyboard_closed(self):
        """Remove keyboard binding when the keyboard is closed."""
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

class ManagerSettingsPrompt(Popup):
    """
    A Popup with settings for the manager.
    """
    
    def input_save(self):
        """
        Get the text from the input fields,
        and save them.
        """
        vowel_price = data_caching.str_to_int(self.vowel_input.text)
        min_win = data_caching.str_to_int(self.min_input.text)
        cash_values = [data_caching.str_to_int(line)
            for line in self.wedges_input.text.split()]
        
        data_caching.update_variables({
            'vowel_price': vowel_price if vowel_price else '',
            'min_win': min_win if min_win else '',
            'cash_values': sorted([v for v in cash_values if v])})
        
        self.dismiss()

class FileChooserPrompt(Popup):
    """
    A Popup allowing the user to select files.
    """
    
    def __init__(self, callback, **kwargs):
        """
        Create the Popup.
        Files selected will be passed to `callback`
        as a list.
        """
        super(FileChooserPrompt, self).__init__(
            title=strings.button_load, **kwargs)
        
        chooser_path = data_caching.get_variables().get(
            'file_chooser_path', '')
        if not chooser_path or not os.path.exists(chooser_path):
            chooser_path = os.getcwd()
        
        layout = BoxLayout(orientation='vertical')
        chooser = FileChooserIconView(path=chooser_path, multiselect=True)
        layout.add_widget(chooser)
        
        def confirm(instance):
            """
            Pass the FileChooser's selection to `callback`.
            """
            callback(chooser.selection)
            data_caching.update_variables({
                'file_chooser_path': chooser.path})
            self.dismiss()
        
        button_layout = BoxLayout(orientation='horizontal')
        button_cancel = Button(text=strings.button_close)
        button_confirm = Button(text=strings.button_confirm)
        button_cancel.bind(on_release=self.dismiss)
        button_confirm.bind(on_release=confirm)
        button_layout.add_widget(button_cancel)
        button_layout.add_widget(button_confirm)
        button_layout.size_hint_y = 0.25
        layout.add_widget(button_layout)
        
        self.content = layout

class FileSaverPrompt(Popup):
    """
    A Popup allowing the user to save puzzles to a file.
    """
    
    def __init__(self, puzzle_names, **kwargs):
        super(FileSaverPrompt, self).__init__(
            title=strings.button_export, **kwargs)
        
        chooser_path = data_caching.get_variables().get(
            'file_chooser_path', '')
        if not chooser_path or not os.path.exists(chooser_path):
            chooser_path = os.getcwd()
        
        layout = BoxLayout(orientation='vertical')
        chooser = FileChooserIconView(path=chooser_path)
        layout.add_widget(chooser)
        
        layout.add_widget(Widget(size_hint_y=0.02))
        
        filename_layout, filename_label, filename_input = _input_layout(
            strings.label_filename)
        filename_layout.size_hint_y = None
        filename_layout.height = 30
        layout.add_widget(filename_layout)
        
        def set_filename_input():
            if chooser.selection:
                filename_input.text = os.path.basename(chooser.selection[0])
        chooser.select_callback = set_filename_input
        
        layout.add_widget(Widget(size_hint_y=0.02))
        
        button_layout = BoxLayout(orientation='horizontal')
        button_cancel = Button(text=strings.button_close)
        button_confirm = Button(text=strings.button_confirm)
        button_layout.add_widget(button_cancel)
        button_layout.add_widget(button_confirm)
        button_layout.size_hint_y = 0.25
        layout.add_widget(button_layout)
        
        def input_save(instance):
            """
            Get text from the input box,
            and save puzzles to the filename specified.
            """
            
            filename = filename_input.text
            
            if filename:
                data_caching.export_puzzles_by_name(
                    puzzle_names,
                    os.path.join(chooser.path, filename))
                data_caching.update_variables({
                    'file_chooser_path': chooser.path})
                self.dismiss()
            else:
                filename_label.color = values.color_red
        
        button_cancel.bind(on_release=self.dismiss)
        button_confirm.bind(on_release=input_save)
        
        self.content = layout

class InfoPrompt(Popup):
    """
    A simple Popup with text and one button to dismiss.
    """
    
    def __init__(self, text, **kwargs):
        """Create the popup."""
        super(InfoPrompt, self).__init__(**kwargs)
        self.text_label.text = text

class ScrollableLabel(AnchorLayout):
    """
    A layout containing a label
    which is centered vertically,
    and can scroll if the text is longer
    than the widget containing it.
    """
    pass

def _wrap_with_dismiss(callback, popup):
    """
    Wrap a function so that it calls popup.dismiss at the end.
    """
    
    def do_callback(*args, **kwargs):
        if callback:
            callback(*args, **kwargs)
        popup.dismiss()
    return do_callback

def _input_layout(title, hint_text=''):
    """
    Create a horizontal BoxLayout with text and an input box.
    Returns the BoxLayout, the text Label, and the TextInput
    """
    
    layout = BoxLayout(orientation='horizontal')
    
    layout_label = Label(text=title)
    layout_label.size_hint_x = None
    layout_label.valign = 'center'
    layout_label.halign = 'center'
    
    input = TextInput()
    input.hint_text = hint_text
    
    layout.add_widget(layout_label)
    layout.add_widget(input)
    
    layout.size_hint_y = 0.25
    return layout, layout_label, input
