import json
import os

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.widget import Widget

puzzle_file = 'puzzles.json'

def save_puzzle_prompt(puzzle, callback):
    """
    Prompt the user to save a puzzle,
    Then run `callback` when popup is dismissed.
    """
    
    content = BoxLayout(orientation='vertical')
    
    name_layout, name_label, name_input = _input_layout('Name')
    cat_layout, cat_label, cat_input = _input_layout('Category')
    clue_layout, clue_label, clue_input = _input_layout('Clue')
    
    content.add_widget(name_layout)
    content.add_widget(cat_layout)
    content.add_widget(clue_layout)
    # create blank space with an empty widget
    content.add_widget(Widget())
    
    button_layout = BoxLayout(orientation='horizontal')
    button_close = Button(text='Close')
    button_save = Button(text='Save')
    button_layout.add_widget(button_close)
    button_layout.add_widget(button_save)
    content.add_widget(button_layout)
    
    popup = Popup(title='Save puzzle', content=content)
    
    def wrap_with_callback(function1, function2):
        """
        Wrap `function1` to call `function2` afterwards.
        """
        
        def do_callback(instance=None):
            if function1:
                function1()
            if function2:
                function2()
        return do_callback
    
    popup.dismiss = wrap_with_callback(popup.dismiss, callback)
    
    def input_save(instance):
        """
        Get text from the input fields,
        and save the puzzle.
        """
        name = name_input.text
        category = cat_input.text
        clue = clue_input.text
        
        if name and category:
            puzzle_dict = {
                'category': category,
                'clue': clue,
                'puzzle': puzzle}
            add_puzzle(name, puzzle_dict)
            popup.dismiss()
        else:
            if not name:
                name_label.color = [1, 0, 0, 1]
            if not category:
                cat_label.color = [1, 0, 0, 1]
            pass
    
    button_close.bind(on_press=popup.dismiss)
    button_save.bind(on_press=input_save)
    
    popup.open()

def load_puzzle_prompt(callback):
    """
    Prompt the user to select a puzzle by name.
    The selected puzzle will then be passed to `callback`.
    """
    content = BoxLayout(orientation='vertical')
    
    puzzle_layout = BoxLayout(orientation='vertical', size_hint=(1, None))
    puzzle_layout.bind(minimum_height=puzzle_layout.setter('height'))
    puzzles = read_puzzles()
    for name in puzzles.keys():
        toggle_button = ToggleButton(text=name)
        toggle_button.size_hint_y = toggle_button.size_hint_min_y
        puzzle_layout.add_widget(toggle_button)
    puzzle_layout.add_widget(Widget())
    puzzle_scroll = ScrollView()
    puzzle_scroll.add_widget(puzzle_layout)
    content.add_widget(puzzle_scroll)
    
    content.add_widget(Widget(size_hint=(1, 0.02)))
    
    button_layout = BoxLayout(orientation='horizontal')
    button_layout.size_hint_y = button_layout.size_hint_min_y
    button_close = Button(text='Close')
    button_close.size_hint_y = button_close.size_hint_min_y
    button_confirm = Button(text='Confirm')
    button_confirm.size_hint_y = button_confirm.size_hint_min_y
    button_layout.add_widget(button_close)
    button_layout.add_widget(button_confirm)
    content.add_widget(button_layout)
    
    popup = Popup(title='Select puzzle', content=content)
    
    def input_save(instance):
        """
        Check which buttons are selected,
        then run `callback` on the first puzzle selected.
        """
        
        names = []
        for button in puzzle_layout.children[::-1]:
            try:
                if button.state == 'down':
                    names.append(button.text)
            except AttributeError:
                # empty widget
                pass
        selected_puzzles = [
            puzzles[name]['puzzle']
            for name in names]
        callback(selected_puzzles[0])
        
        popup.dismiss()
    
    button_close.bind(on_press=popup.dismiss)
    button_confirm.bind(on_press=input_save)
    
    popup.open()

def yes_no_prompt(text, yes_callback, no_callback):
    """
    Open a popup prompting the user with `text`,
    with yes and no buttons.
    Yes and no buttons are bound to `yes_callback` and `no_callback`
    respectively.
    """
    content = BoxLayout(orientation='vertical')
    content.add_widget(Label(text=text))
    
    button_layout = BoxLayout(orientation='horizontal')
    button_layout.size_hint_y = button_layout.size_hint_min_y
    button_no = Button(text='No')
    button_no.size_hint_y = button_no.size_hint_min_y
    button_yes = Button(text='Yes')
    button_yes.size_hint_y = button_yes.size_hint_min_y
    button_layout.add_widget(button_no)
    button_layout.add_widget(button_yes)
    content.add_widget(button_layout)
    
    popup = Popup(title='Name exists', content=content)
    
    def wrap_with_dismiss(callback):
        """
        Wrap a function so that it calls popup.dismiss at the end.
        """
        
        def do_callback(instance):
            if callback:
                callback()
            popup.dismiss()
        return do_callback
    
    button_no.bind(on_press=wrap_with_dismiss(no_callback))
    button_yes.bind(on_press=wrap_with_dismiss(yes_callback))
    
    popup.open()

def add_puzzle(name, puzzle_dict):
    """
    Add a puzzle to `puzzle_file`.
    Creates a confirmation prompt if a puzzle
    with the given name already exists.
    """
    
    puzzles = read_puzzles()
    if name in puzzles.keys():
        yes_no_prompt(
            'A puzzle with the name "{}" already exists.\nOverwrite?'.format(
                name),
            lambda: write_puzzle(puzzles, name, puzzle_dict),
            None
            )
    else:
        write_puzzle(puzzles, name, puzzle_dict)

def write_puzzle(puzzles, new_name, new_dict):
    """Write `puzzles` to `puzzle_file`."""
    puzzles[new_name] = new_dict
    
    cwd = os.path.dirname(__file__)
    filename = os.path.join(cwd, puzzle_file)
    with open(filename, 'w') as f:
        json.dump(puzzles, f)

def read_puzzles():
    """
    Load from `puzzle_file` with JSON.
    Returns an empty dict if the file does not exist.
    """
    cwd = os.path.dirname(__file__)
    filename = os.path.join(cwd, puzzle_file)
    try:
        with open(filename) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def _input_layout(title):
    """
    Create a horizontal BoxLayout with text and an input box.
    Returns the BoxLayout, the text Label, and the TextInput
    """
    
    layout = BoxLayout(orientation='horizontal')
    
    layout_label = Label(text=title)
    layout_label.size_hint = layout_label.size_hint_min
    
    input = TextInput()
    
    layout.add_widget(layout_label)
    layout.add_widget(input)
    
    layout.size_hint_y = layout.size_hint_min_y
    return layout, layout_label, input
