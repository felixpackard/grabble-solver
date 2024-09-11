import os
from collections import Counter
from typing import Dict, Set, List, Optional, Tuple
import json
import base64

SCRABBLE_LETTER_FREQUENCY: Dict[str, int] = {
    'e': 12, 'a': 9, 'i': 9, 'o': 8, 'n': 6, 'r': 6, 't': 6, 'l': 4, 's': 4, 'u': 4,
    'd': 4, 'g': 3, 'b': 2, 'c': 2, 'm': 2, 'p': 2, 'f': 2, 'h': 2, 'v': 2, 'w': 2,
    'y': 2, 'k': 1, 'j': 1, 'x': 1, 'q': 1, 'z': 1
}

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

def load_wordlist(path: str) -> Set[str]:
    """
    Load a wordlist from a file and return it as a set of lowercase words.

    Args:
        path (str): The path to the wordlist file.

    Returns:
        Set[str]: A set containing all words from the file in lowercase.
    """
    with open(path, 'r') as file:
        return set(word.strip().lower() for word in file)

def check_word_against_pool(word: str, pool_counter: Counter) -> bool:
    """
    Check if a word can be formed using the letters in the pool.

    Args:
        word (str): The word to check.
        pool_counter (Counter): A Counter object representing the available letters.

    Returns:
        bool: True if the word can be formed, False otherwise.
    """
    return not Counter(word) - pool_counter

def check_word_with_existing(word: str, existing_word: str, combined_counter: Counter) -> bool:
    """
    Check if a new word can be formed by combining an existing word with letters from the pool.

    Args:
        word (str): The new word to check.
        existing_word (str): An existing word to potentially combine with.
        combined_counter (Counter): A Counter object representing the available letters including the existing word.

    Returns:
        bool: True if the new word can be formed, False otherwise.
    """
    word_counter = Counter(word)
    if len(word) > len(existing_word) and not word_counter - combined_counter:
        # Check if all letters of the existing word are used
        return all(word_counter[letter] >= count for letter, count in Counter(existing_word).items())
    return False

def get_missing_letter(word: str, pool_counter: Counter) -> Optional[str]:
    """
    Find the single missing letter needed to form a word from the pool.

    Args:
        word (str): The word to check.
        pool_counter (Counter): A Counter object representing the available letters.

    Returns:
        Optional[str]: The missing letter if only one is needed, None otherwise.
    """
    missing = Counter(word) - pool_counter
    if sum(missing.values()) == 1:
        return list(missing.keys())[0]
    return None

def get_possible_words(pool: List[str], wordlist: Set[str], existing_words: List[str]) -> List[Word]:
    """
    Get all possible words that can be formed from the pool and existing words.

    Args:
        pool (List[str]): List of available letters.
        wordlist (Set[str]): Set of valid words.
        existing_words (List[str]): List of words already formed.

    Returns:
        List[Word]: List of possible Word objects.
    """
    pool_counter = Counter(pool)
    possible: List[Word] = [Word(word, pool_letters=[l for l in word if l in pool]) for word in wordlist if check_word_against_pool(word, pool_counter)]
    
    for existing_word in existing_words:
        combined_pool = pool + list(existing_word)
        combined_counter = Counter(combined_pool)
        for word in wordlist:
            if check_word_with_existing(word, existing_word, combined_counter):
                new_letters = [l for l in word if l in pool and l not in existing_word]
                possible.append(Word(word, existing_word, new_letters))
    
    return sorted(possible, key=len, reverse=True)

def get_potential_words(pool: List[str], wordlist: Set[str], existing_words: List[str]) -> Dict[str, List[Word]]:
    """
    Get potential words that can be formed by adding one letter to the pool or existing words.

    Args:
        pool (List[str]): List of available letters.
        wordlist (Set[str]): Set of valid words.
        existing_words (List[str]): List of words already formed.

    Returns:
        Dict[str, List[Word]]: Dictionary of potential Word objects, keyed by the missing letter.
    """
    pool_counter = Counter(pool)
    potential: Dict[str, List[Word]] = {}
    
    for word in wordlist:
        word_counter = Counter(word)
        missing = word_counter - pool_counter
        
        if sum(missing.values()) == 1:
            letter = list(missing.keys())[0]
            if letter not in potential:
                potential[letter] = []
            potential[letter].append(Word(word, pool_letters=[l for l in word if l in pool]))
    
    # Check for potential words that can be made by combining pool letters with existing words
    for existing_word in existing_words:
        combined_pool = pool + list(existing_word)
        combined_counter = Counter(combined_pool)
        for word in wordlist:
            if len(word) > len(existing_word):
                word_counter = Counter(word)
                missing = word_counter - combined_counter
                if sum(missing.values()) == 1:
                    letter = list(missing.keys())[0]
                    if letter not in potential:
                        potential[letter] = []
                    new_letters = [l for l in word if l in pool and l not in existing_word]
                    potential[letter].append(Word(word, existing_word, new_letters))
    
    # Sort words by length in descending order for each letter
    for letter in potential:
        potential[letter].sort(key=len, reverse=True)
    
    return potential

def get_wordlists() -> List[str]:
    """
    Get a list of available wordlist files in the './wordlists' directory.

    Returns:
        List[str]: A sorted list of wordlist filenames (ending with .txt).

    Raises:
        FileNotFoundError: If the wordlists directory doesn't exist or contains no wordlists.
    """
    if not os.path.exists('./wordlists'):
        raise FileNotFoundError("Wordlists directory not found.")
    
    wordlists = [f for f in os.listdir('./wordlists') if f.endswith('.txt')]
    if not wordlists:
        raise FileNotFoundError("No wordlists found in the wordlists directory.")
    
    return sorted(wordlists)

def serialize_game_state(pool: List[str], existing_words: List[str]) -> str:
    """
    Convert the game state to a base64 encoded JSON string for clipboard.

    Args:
        pool (List[str]): List of available letters.
        existing_words (List[str]): List of words already formed.

    Returns:
        str: A base64 encoded JSON string representing the game state.
    """
    data = {
        'letters': ''.join(pool),
        'words': existing_words
    }
    json_str = json.dumps(data)
    return base64.b64encode(json_str.encode('utf-8')).decode('utf-8')

def deserialize_game_state(data_str: str) -> Tuple[List[str], List[str]]:
    """
    Convert a base64 encoded JSON string from clipboard to game state.

    Args:
        data_str (str): A base64 encoded JSON string representing the game state.

    Returns:
        Tuple[List[str], List[str]]: A tuple containing the pool and existing words.
    """
    try:
        json_str = base64.b64decode(data_str.encode('utf-8')).decode('utf-8')
        data = json.loads(json_str)
        pool = [letter.lower() for letter in data['letters'] if letter.isalpha()]
        existing_words = data['words']
        return pool, existing_words
    except (base64.binascii.Error, json.JSONDecodeError, KeyError):
        raise ValueError("Invalid input format. Please use the exported format.")
