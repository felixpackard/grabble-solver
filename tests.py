import unittest
from grabble_logic import (
    load_wordlist,
    check_word_against_pool,
    check_word_with_existing,
    get_missing_letter,
    get_possible_words,
    get_potential_words,
    serialize_game_state, deserialize_game_state
)
from collections import Counter
import base64
import os

class TestGrabbleLogic(unittest.TestCase):
    def setUp(self):
        self.sample_wordlist = {'cat', 'dog', 'bird', 'fish', 'elephant', 'catfish', 'dogfish'}
        self.sample_pool = ['c', 'a', 't', 'd', 'o']

    def test_load_wordlist(self):
        # This test assumes you have a test wordlist file
        test_wordlist_path = './test_wordlist.txt'
        with open(test_wordlist_path, 'w') as f:
            f.write('cat\ndog\nbird\n')
        
        loaded_wordlist = load_wordlist(test_wordlist_path)
        self.assertEqual(loaded_wordlist, {'cat', 'dog', 'bird'})

        os.remove(test_wordlist_path)

    def test_check_word_against_pool(self):
        pool_counter = Counter(self.sample_pool)
        self.assertTrue(check_word_against_pool('cat', pool_counter))
        self.assertFalse(check_word_against_pool('dog', pool_counter))

    def test_check_word_with_existing(self):
        combined_counter = Counter(self.sample_pool + list('fish'))
        self.assertTrue(check_word_with_existing('catfish', 'fish', combined_counter))
        self.assertFalse(check_word_with_existing('nulfish', 'fish', combined_counter))

    def test_get_missing_letter(self):
        pool_counter = Counter(self.sample_pool)
        self.assertEqual(get_missing_letter('cats', pool_counter), 's')
        self.assertIsNone(get_missing_letter('cat', pool_counter))

    def test_get_possible_words(self):
        possible = get_possible_words(self.sample_pool, self.sample_wordlist, ['fish'])
        self.assertIn('cat', [word.word for word in possible])
        self.assertIn('catfish', [word.word for word in possible if word.existing_word == 'fish'])
        self.assertNotIn('dog', [word.word for word in possible])

    def test_get_potential_words(self):
        potential = get_potential_words(self.sample_pool, self.sample_wordlist, ['fish'])
        self.assertIn('g', potential)
        self.assertTrue(any(word.word == 'dog' for word in potential['g']))
        self.assertTrue(any(word.word == 'dogfish' for word in potential['g']))

class TestSerializationDeserialization(unittest.TestCase):

    def test_serialize_game_state(self):
        pool = ['a', 'b', 'c', 'd', 'e']
        existing_words = ['cat', 'dog']
        serialized = serialize_game_state(pool, existing_words)
        self.assertTrue(isinstance(serialized, str))
        self.assertTrue(serialized.replace('=', '').isalnum())  # Check if it's base64 encoded

    def test_deserialize_game_state(self):
        serialized = serialize_game_state(['a', 'b', 'c', 'd', 'e'], ['cat', 'dog'])
        pool, existing_words = deserialize_game_state(serialized)
        self.assertEqual(pool, ['a', 'b', 'c', 'd', 'e'])
        self.assertEqual(existing_words, ['cat', 'dog'])

    def test_serialize_deserialize_roundtrip(self):
        original_pool = ['x', 'y', 'z', 'a', 'b']
        original_words = ['xyz', 'ab']
        serialized = serialize_game_state(original_pool, original_words)
        deserialized_pool, deserialized_words = deserialize_game_state(serialized)
        self.assertEqual(original_pool, deserialized_pool)
        self.assertEqual(original_words, deserialized_words)

    def test_deserialize_invalid_base64(self):
        invalid_base64 = 'This is not a valid base64 string'
        with self.assertRaises(ValueError):
            deserialize_game_state(invalid_base64)

    def test_deserialize_invalid_json(self):
        invalid_json = base64.b64encode(b'{"letters": "abcde", "words": ["cat", "dog"').decode('utf-8')
        with self.assertRaises(ValueError):
            deserialize_game_state(invalid_json)

    def test_deserialize_missing_keys(self):
        missing_keys_json = base64.b64encode(b'{"letters": "abcde"}').decode('utf-8')
        with self.assertRaises(ValueError):
            deserialize_game_state(missing_keys_json)

    def test_deserialize_non_alpha_characters(self):
        non_alpha_json = serialize_game_state(['a', 'b', 'c', '1', '2', '3', '!', '@', '#'], ['cat', 'dog'])
        pool, words = deserialize_game_state(non_alpha_json)
        self.assertEqual(pool, ['a', 'b', 'c'])
        self.assertEqual(words, ['cat', 'dog'])

if __name__ == '__main__':
    unittest.main()
