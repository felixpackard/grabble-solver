import urwid
from typing import Dict, List
from grabble_logic import (
    GameState, get_wordlists, Word
)
import pyperclip
class GrabbleUI:
    def __init__(self) -> None:
        self.game_state = GameState()
        self.is_wordlist_selection = True
        self.setup_ui()

    def setup_ui(self) -> None:
        self.wordlist_selector: urwid.Widget = self.create_wordlist_selector()
        self.main_view: urwid.Widget = self.create_main_view()
        
        self.palette = [
            ('possible_words', 'light green,bold', 'default'),
            ('potential_words', 'yellow,bold', 'default'),
        ]
        
        self.loop: urwid.MainLoop = urwid.MainLoop(self.wordlist_selector, unhandled_input=self.global_input, palette=self.palette)
        self.loop.run()

    def create_wordlist_selector(self) -> urwid.Filler:
        wordlists: List[str] = get_wordlists()
        body: List[urwid.Widget] = [urwid.Text("Select a wordlist:"), urwid.Divider()]
        for w in wordlists:
            button: urwid.Button = urwid.Button(w)
            urwid.connect_signal(button, 'click', self.on_wordlist_chosen, w)
            body.append(urwid.AttrMap(button, None, focus_map='reversed'))
        pile = urwid.Pile(body)
        box = urwid.LineBox(urwid.Padding(pile, left=2, right=2))
        return urwid.Filler(urwid.Padding(box, 'center', ('relative', 50)))

    def on_wordlist_chosen(self, button: urwid.Button, choice: str) -> None:
        loading_text = urwid.Text("Loading wordlist... Please wait.")
        loading_filler = urwid.Filler(urwid.Padding(loading_text, align='center', width='pack'))
        centered_loading = urwid.Padding(loading_filler, align='center', width='pack')
        self.loop.widget = centered_loading
        
        def load_wordlist():
            self.game_state.load_wordlist(f"./wordlists/{choice}")
            self.loop.widget = self.main_view
            self.is_wordlist_selection = False
            self.update_display()
        
        self.loop.set_alarm_in(0.1, lambda loop, user_data: load_wordlist())

    def create_main_view(self) -> urwid.Widget:
        self.word_pool: urwid.Text = urwid.Text("")
        self.letter_pool: urwid.Text = urwid.Text("")
        self.potential_words: urwid.Text = urwid.Text("")
        self.possible_words: urwid.Text = urwid.AttrMap(urwid.Text(""), 'possible_words')
        self.actions: urwid.Text = urwid.Text("")

        def padded_linebox(widget, title):
            return urwid.LineBox(urwid.Padding(urwid.Filler(widget), left=1, right=1), title)

        top_row: urwid.Columns = urwid.Columns([
            ('weight', 1, padded_linebox(self.word_pool, "Word Pool")),
            ('weight', 1, padded_linebox(self.letter_pool, "Letter Pool")),
        ])
        bottom_row: urwid.Columns = urwid.Columns([
            ('weight', 2, padded_linebox(self.potential_words, "Potential Words")),
            ('weight', 2, padded_linebox(self.possible_words, "Possible Words")),
            ('weight', 1, padded_linebox(self.actions, "Actions")),
        ])
        
        layout: urwid.Frame = urwid.Frame(
            urwid.Pile([
                ('weight', 1, top_row),
                ('weight', 4, bottom_row),
            ])
        )

        return layout

    def update_display(self) -> None:
        self.word_pool.set_text(", ".join(self.game_state.existing_words))
        self.letter_pool.set_text(" ".join(self.game_state.pool))

        potential: Dict[str, List[Word]] = self.game_state.get_potential_words()
        potential_text: List[List] = []
        for i, (letter, words) in enumerate(potential.items()):
            if i >= 10:
                potential_text.append("\n")
                potential_text.append("...")
                break
            word_list = [('potential_words', letter + ": ")]
            if words:
                word_list.extend([('potential_words', str(words[0])), ", "])
                word_list.extend([str(w) + ", " for w in words[1:3]])
            if len(words) > 3:
                word_list.append("...")
            potential_text.append(word_list)
            if i < 9 and i < len(potential) - 1:  # Add line break if not the last item
                potential_text.append("\n")
        self.potential_words.set_text(potential_text)

        possible: List[Word] = self.game_state.get_possible_words()
        possible_text: List[str] = [f"{i+1}. {str(word)}" for i, word in enumerate(possible[:10])]
        if len(possible) > 10:
            possible_text.append("...")
        self.possible_words.original_widget.set_text("\n".join(possible_text))

        actions_text: str = "a: Add Letter\nr: Remove Word\nd: Delete Letters\ni: Import State\ne: Export State\nq: Quit"
        self.actions.set_text(actions_text)

    def global_input(self, key: str) -> None:
        if self.is_wordlist_selection:
            if key in ('q', 'Q'):
                raise urwid.ExitMainLoop()
            return

        if key in ('q', 'Q'):
            raise urwid.ExitMainLoop()
        elif key in ('a', 'A'):
            self.prompt_input("Enter letter to add:", self.add_letter, 
                              validator=lambda x: len(x) == 1 and x.isalpha())
        elif key in ('r', 'R'):
            self.prompt_input("Enter word number to remove:", self.remove_word, 
                              validator=lambda x: x.isdigit())
        elif key in ('d', 'D'):
            self.prompt_input("Enter letters to remove:", self.delete_letters)
        elif key in ('i', 'I'):
            self.prompt_input("Paste exported state:", self.import_state)
        elif key in ('e', 'E'):
            self.export_state()

    def prompt_input(self, prompt: str, callback: callable, validator: callable = None) -> None:
        edit = urwid.Edit(prompt + " ")

        def reset_widget() -> None:
            self.loop.widget = self.main_view
            self.loop.unhandled_input = self.global_input
        
        def handle_input(key: str) -> None:
            if key == 'enter':
                text = edit.edit_text.strip()
                if text and (not validator or validator(text)):
                    callback(text)
                    reset_widget()
                else:
                    self.show_popup("Invalid input. Please try again.")
            elif key == 'esc':
                reset_widget()

        # Create a horizontally scrollable edit widget
        edit_box = urwid.BoxAdapter(urwid.Filler(edit), height=1)
        scrollable_edit = urwid.Columns([('weight', 1, edit_box)], dividechars=1, min_width=1)
        input_box = urwid.LineBox(scrollable_edit)
        
        bottom_pile = urwid.Pile([
            urwid.BoxAdapter(urwid.SolidFill(), height=1),
            ('pack', input_box)
        ])
        
        overlay = urwid.Overlay(
            bottom_pile,
            self.main_view,
            align='center',
            width=('relative', 80),
            valign='bottom',
            height='pack'
        )
        
        self.loop.widget = overlay
        self.loop.unhandled_input = handle_input

    def add_letter(self, letter: str) -> None:
        self.game_state.add_letter(letter)
        self.update_display()

    def remove_word(self, index: str) -> None:
        try:
            index = int(index) - 1
            possible: List[Word] = self.game_state.get_possible_words()
            if 0 <= index < len(possible):
                self.game_state.remove_word(possible[index])
            else:
                self.show_popup(f"Invalid index. Please enter a number between 1 and {len(possible)}.")
            self.update_display()
        except ValueError:
            self.show_popup("Invalid input. Please enter a valid number.")

    def delete_letters(self, letters: str) -> None:
        self.game_state.delete_letters(letters)
        self.update_display()

    def import_state(self, input_str: str) -> None:
        try:
            self.game_state = self.game_state.deserialize(input_str)
            self.update_display()
        except ValueError as e:
            self.show_popup(str(e))

    def export_state(self) -> None:
        exported = self.game_state.serialize()
        pyperclip.copy(exported)
        self.show_popup(f"Exported data: {exported}\n\nCopied to clipboard!")

    def show_popup(self, message: str) -> None:
        popup = urwid.LineBox(urwid.Pile([
            urwid.Text(message),
            urwid.Divider(),
            urwid.Text("Press any key to dismiss")
        ]))
        overlay = urwid.Overlay(popup, self.main_view, 'center', ('relative', 80), 'middle', ('relative', 20))
        
        def dismiss_popup(key: str) -> None:
            self.loop.widget = self.main_view
            self.loop.unhandled_input = self.global_input

        self.loop.widget = overlay
        self.loop.unhandled_input = dismiss_popup

def run_grabble_ui() -> None:
    GrabbleUI()

if __name__ == "__main__":
    run_grabble_ui()
