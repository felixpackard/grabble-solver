# Grabble Solver

Grabble is a fast-paced word game where players take it in turns to flip over tiles, form words, and steal words from other players. Grabble Solver is a Python-based tool that helps you solve word puzzles by finding possible and potential words from a given set of letters and existing words.

## Grabble Rules

For the uninitiated, here's a quick overview of the rules:

1. All the letter tiles are turned face downwards or kept in a bag.
2. Players take it in turns to flip over tiles, and form words from the letters on the board.
3. A word may also be formed by creating an anagram of an existing word, either their own or another player's,  and adding one or more letters to it.

There are some limitations to the words that can be formed:

1. The word must be at least 3 letters long.
2. If creating an anagram of an existing word, it can't be a different inflection or morphological variant of the word. e.g. if the word is "cat", you can't add an "s" to the end to make it "cats" – you could however create "cast".

When no more words can be found, the game is scored by counting the first three letters of each word as a single point, and each additional letter as another point. e.g. "cat" is 1 point, "casts" is 3 points, "catfish" is 5 points, etc.

## Features

- [x] Load custom wordlists
- [x] Find possible words from available letters
- [x] Discover potential words by adding one letter
- [x] Manage letter pool and existing words
- [x] Import and export game state
- [x] User-friendly terminal interface
- [ ] Optimised performance for large wordlists
- [ ] Intelligently discards illegal moves such as adding 's' or 'er' to the end of a word

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/grabble-solver.git
   cd grabble-solver
   ```

2. Create a virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

To run the Grabble Solver:

```
python main.py
```

The interface will guide you through the following steps:
1. Select a wordlist
2. Manage your letter pool and existing words
3. View possible and potential words

## Key Commands

- `a`: Add a letter to the pool
- `r`: Remove a word (and add it to existing words)
- `d`: Delete letters from the pool
- `i`: Import game state
- `e`: Export game state
- `q`: Quit the application

## Project Structure

- `main.py`: Entry point of the application
- `grabble_logic.py`: Core logic for word finding and game state management
- `grabble_ui.py`: User interface using the urwid library
- `tests.py`: Unit tests for the core logic
- `wordlists/`: Directory containing wordlist files

## Testing

To run the tests:

```
python tests.py
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.
