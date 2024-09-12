import os
from collections import Counter
from typing import Dict, Set, List, Optional, Generator
import json
import base64
import functools

SCRABBLE_LETTER_FREQUENCY: Dict[str, int] = {
    'e': 12, 'a': 9, 'i': 9, 'o': 8, 'n': 6, 'r': 6, 't': 6, 'l': 4, 's': 4, 'u': 4,
    'd': 4, 'g': 3, 'b': 2, 'c': 2, 'm': 2, 'p': 2, 'f': 2, 'h': 2, 'v': 2, 'w': 2,
    'y': 2, 'k': 1, 'j': 1, 'x': 1, 'q': 1, 'z': 1
}

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_word = False
        self.word = None
    
    def __str__(self):
        return json.dumps(self, default=lambda o: o.__dict__, indent=4)

class Trie:
    def __init__(self):
        self.root = TrieNode()
    
    def __str__(self):
        return self.root.__str__()

    def insert(self, word: str):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_word = True
        node.word = word

class Word:
    def __init__(self, word: str, existing_word: Optional[str] = None, pool_letters: Optional[List[str]] = None):
        self.word = word
        self.existing_word = existing_word
        self.pool_letters = pool_letters or list(word)

    def __len__(self):
        return len(self.word)

    def __str__(self):
        if self.existing_word:
            return f"{self.word} (from {self.existing_word})"
        return self.word

class GameState:
    def __init__(self):
        self.pool: List[str] = []
        self.existing_words: List[str] = []
        self.trie = Trie()
        self.word_bits: Dict[str, int] = {}
        self.letter_to_bit = {chr(i + 97): 1 << i for i in range(26)}
        self.existing_word_counters: Dict[str, Counter] = {}
        self.existing_word_bits: Dict[str, int] = {}

    def debug_print(self):
        """Print the game state for debugging."""

        print(f"Pool: {self.pool}")
        print(f"Existing words: {self.existing_words}")
        print(f"Trie: {self.trie}")
        print(f"Word bits: {self.word_bits}")
        print(f"Letter to bit: {self.letter_to_bit}")

    def load_wordlist(self, path: str) -> None:
        """Load all words from a wordlist file into the trie."""

        with open(path, 'r') as file:
            for word in file:
                self.load_word(word)
    
    def add_existing_words(self, words: List[str]) -> None:
        """Add existing words to the game state."""

        for word in words:
            self.add_existing_word(word)
    
    def add_existing_word(self, word: str) -> None:
        """Add an existing word to the game state."""
        self.existing_words.append(word)
        self.existing_word_counters[word] = Counter(word)
        self.existing_word_bits[word] = self.calculate_word_bits(word)

    def load_words(self, words: List[str]) -> None:
        """Load a list of words into the trie."""

        for word in words:
            self.load_word(word)

    def load_word(self, word: str) -> None:
        """Load a word into the trie."""

        word = word.strip().lower()
        self.trie.insert(word)
        self.word_bits[word] = self.calculate_word_bits(word)

    @functools.lru_cache(maxsize=1024)
    def calculate_word_bits(self, word: str) -> int:
        return functools.reduce(lambda x, y: x | y, (self.letter_to_bit[c] for c in word), 0)

    def add_letters(self, letters: str) -> None:
        """Add letters to the pool."""

        for letter in letters:
            self.add_letter(letter)

    def add_letter(self, letter: str) -> None:
        """Add a letter to the pool."""

        self.pool.append(letter.lower())

    def remove_word(self, word: Word) -> None:
        """Remove a word from the game state."""

        if word.existing_word:
            self.existing_words.remove(word.existing_word)
            del self.existing_word_counters[word.existing_word]
            del self.existing_word_bits[word.existing_word]
        
        self.existing_words.append(word.word)
        self.existing_word_counters[word.word] = Counter(word.word)
        self.existing_word_bits[word.word] = self.calculate_word_bits(word.word)

        letter_counts = Counter(word.pool_letters)
        new_pool = []
        for letter in self.pool:
            if letter in letter_counts and letter_counts[letter] > 0:
                letter_counts[letter] -= 1
            else:
                new_pool.append(letter)
        self.pool = new_pool

    def delete_letters(self, letters: str) -> None:
        """Delete letters from the pool."""

        for letter in letters.lower():
            if letter in self.pool:
                self.pool.remove(letter)

    def get_possible_words(self) -> List[Word]:
        """
        Get all words that can be formed from the current pool of letters,
        or from a combination of all the letters in an existing word and one or
        more letters from the pool.

        :return: A list of Word objects, sorted by length in descending order.
        """

        if not self.trie.root.children:
            raise ValueError("Trie is empty. Make sure the wordlist is loaded.")

        possible: List[Word] = []
        
        # Find anagrams from the pool
        for word in anagram(self, self.pool):
            possible.append(Word(word, pool_letters=list(word)))
        
        # Check for words that can be formed using existing words
        for existing_word in self.existing_words:
            existing_bits = self.existing_word_bits[existing_word]
            existing_counter = self.existing_word_counters[existing_word]
            combined_letters = self.pool + list(existing_word)
            for word in anagram(self, combined_letters):
                word_bits = self.word_bits[word]
                if len(word) > len(existing_word) and (word_bits & existing_bits) == existing_bits:
                    # Quick check passed, now verify letter frequencies
                    word_counter = Counter(word)
                    if all(word_counter[letter] >= count for letter, count in existing_counter.items()):
                        new_letters = [l for l in word if l in self.pool and word_counter[l] > existing_counter[l]]
                        if new_letters:  # Ensure at least one letter from the pool is used
                            possible.append(Word(word, existing_word, new_letters))
        
        return sorted(possible, key=len, reverse=True)

    def get_potential_words(self) -> Dict[str, List[Word]]:
        """
        Get all words that could be formed from the current pool of letters,
        or from a combination of all the letters in an existing word and one or
        more letters from the pool, if one more letter was added to the pool.

        :return: A dictionary with the missing letter as the key and a list of
        Word objects sorted by length in descending order as the value.
        """

        if not self.trie.root.children:
            raise ValueError("Trie is empty. Make sure the wordlist is loaded.")

        potential_words: Dict[str, List[Word]] = {}
        pool_bits = self.calculate_word_bits(''.join(self.pool))

        def check_and_add_word(word: str, pool_bits: int, existing_word: Optional[str] = None):
            word_bits = self.word_bits[word]
            if existing_word:
                existing_bits = self.existing_word_bits[existing_word]
                if (word_bits & existing_bits) != existing_bits:
                    return
                if word_bits == existing_bits:  # No new letter used
                    return
            diff_bits = word_bits & ~pool_bits
            if bin(diff_bits).count('1') == 1:
                missing_letter = chr(diff_bits.bit_length() + 96)
                new_letters = [l for l in word if l not in (existing_word or '') or self.letter_to_bit[l] & (word_bits & ~existing_bits)]
                if new_letters:  # Ensure at least one new letter is used
                    new_word = Word(word, existing_word, new_letters)
                    potential_words.setdefault(missing_letter, []).append(new_word)

        # Check potential words from the pool and existing words
        letters_checked = 0
        for letter, _ in sorted(SCRABBLE_LETTER_FREQUENCY.items(), key=lambda x: x[1], reverse=True):
            if letter not in self.pool:
                # Check potential words from the pool
                temp_pool = self.pool + [letter]
                for word in anagram(self, temp_pool):
                    check_and_add_word(word, pool_bits)

                # Check potential words from existing words
                for existing_word in self.existing_words:
                    combined_letters = self.pool + list(existing_word)
                    if letter not in combined_letters:
                        temp_combined = combined_letters + [letter]
                        combined_bits = pool_bits | self.existing_word_bits[existing_word]
                        for word in anagram(self, temp_combined):
                            if len(word) > len(existing_word):
                                check_and_add_word(word, combined_bits, existing_word)

                letters_checked += 1
                if letters_checked >= 11:
                    break

        # Sort word lists by length in descending order
        for letter in potential_words:
            potential_words[letter].sort(key=len, reverse=True)

        return potential_words

    def serialize(self) -> str:
        """Serialize the game state to a string."""

        data = {
            'letters': ''.join(self.pool),
            'words': self.existing_words
        }
        json_str = json.dumps(data)
        return base64.b64encode(json_str.encode('utf-8')).decode('utf-8')

    def deserialize(self, data_str: str) -> 'GameState':
        """Deserialize the game state from a string."""

        try:
            json_str = base64.b64decode(data_str.encode('utf-8')).decode('utf-8')
            data = json.loads(json_str)
            
            # Add letters to the pool
            self.add_letters(data['letters'])
            
            # Add existing words
            self.add_existing_words(data['words'])
            
            return self
        except (base64.binascii.Error, json.JSONDecodeError, KeyError):
            raise ValueError("Invalid input format. Please use the exported format.")


def get_wordlists() -> List[str]:
    """Get the wordlists from the wordlists directory."""

    if not os.path.exists('./wordlists'):
        raise FileNotFoundError("Wordlists directory not found.")
    
    wordlists = [f for f in os.listdir('./wordlists') if f.endswith('.txt')]
    if not wordlists:
        raise FileNotFoundError("No wordlists found in the wordlists directory.")
    
    return sorted(wordlists)


def in_trie(trie: Trie, word: str) -> bool:
    """Check if a word is in the trie."""

    node = trie.root
    for char in word:
        if char not in node.children:
            return False
        node = node.children[char]
    return node.is_word


def anagram(game_state: GameState, letters: List[str]) -> Generator[str, None, None]:
    """Return (yield) all partial anagrams that can be formed from the letters."""

    if not game_state.trie.root.children:
        raise ValueError("Trie is empty. Make sure the wordlist is loaded.")

    def _anagram(letter_counts: Counter, path: List[str], node: TrieNode) -> Generator[str, None, None]:
        """Find partial anagrams of the letters and counts in the Counter letter_counts."""
        
        if node.is_word:
            yield ''.join(path)
        
        for letter, child in node.children.items():
            count = letter_counts.get(letter, 0)
            if count == 0:
                continue
            letter_counts[letter] -= 1
            path.append(letter)
            yield from _anagram(letter_counts, path, child)
            path.pop()
            letter_counts[letter] += 1

    letter_counts = Counter(letters)
    yield from _anagram(letter_counts, [], game_state.trie.root)
