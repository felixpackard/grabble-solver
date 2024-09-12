from pprint import pprint
import unittest
from grabble_logic import GameState, Word, in_trie
import os

class TestGrabbleLogic(unittest.TestCase):
    def test_load_wordlist(self):
        test_wordlist_path = '/tmp/test_wordlist.txt'
        with open(test_wordlist_path, 'w') as f:
            f.write('cat\ndog\nbird\n')
        
        state = GameState()
        state.load_wordlist(test_wordlist_path)

        self.assertTrue(in_trie(state.trie, 'cat'))
        self.assertTrue(in_trie(state.trie, 'dog'))
        self.assertTrue(in_trie(state.trie, 'bird'))
        self.assertFalse(in_trie(state.trie, 'elephant'))
        self.assertFalse(in_trie(state.trie, 'catfish'))
        self.assertFalse(in_trie(state.trie, 'dogfish'))

        os.remove(test_wordlist_path)
    
    def test_add_letter(self):
        state = GameState()

        state.add_letter('a')
        state.add_letter('b')

        self.assertIn('a', state.pool)
        self.assertIn('b', state.pool)
    
    def test_remove_word(self):
        state = GameState()

        state.load_words(['cat', 'dog'])
        state.add_letters('catat')

        word = Word("cat", None, list('cat'))

        state.remove_word(word)

        self.assertIn('cat', state.existing_words)
        self.assertIn('a', state.pool)
        self.assertIn('t', state.pool)
        self.assertNotIn('c', state.pool)
    
    def test_delete_letters(self):
        state = GameState()

        state.pool = ['a', 'b', 'c', 'd', 'e']

        state.delete_letters('abc')

        self.assertNotIn('a', state.pool)
        self.assertNotIn('b', state.pool)
        self.assertNotIn('c', state.pool)
    
    def test_get_possible_words(self):
        state = GameState()

        state.add_existing_word('fish')
        state.pool = ['c', 'a', 't', 'd', 'o', 'z']
        state.load_words(['cat', 'dog', 'catfish', 'zoo'])
        
        possible = state.get_possible_words()

        possible_words = [word.word for word in possible]

        self.assertIn('cat', possible_words)
        self.assertIn('catfish', possible_words)
        self.assertNotIn('dog', possible_words)
        self.assertNotIn('zoo', possible_words)

    def test_get_potential_words(self):
        state = GameState()
        state.add_existing_words(['fish', 'dog'])
        state.add_letters('catdoz')
        state.load_words(['dog', 'dogfish', 'dogfiat'])
        
        potential = state.get_potential_words()

        self.assertIn('g', potential)

        potential_words = [word.word for word in potential['g']]

        self.assertIn('dog', potential_words)
        self.assertIn('dogfish', potential_words)
        self.assertNotIn('cat', potential_words)
        self.assertNotIn('dogfiat', potential_words)


class TestSerializationDeserialization(unittest.TestCase):
    def setUp(self):
        self.game_state = GameState()
        self.game_state.load_words(['cat', 'dog'])
        self.game_state.add_letters('abcde')
        self.game_state.add_existing_words(['cat', 'dog'])

    def test_serialize_deserialize_roundtrip(self):
        serialized = self.game_state.serialize()
        
        state = GameState()
        state.load_words(['cat', 'dog'])
        state.deserialize(serialized)

        self.assertEqual(self.game_state.pool, state.pool)
        self.assertEqual(self.game_state.existing_words, state.existing_words)
        self.assertTrue(in_trie(state.trie, 'cat'))
        self.assertTrue(in_trie(state.trie, 'dog'))

    def test_deserialize_invalid_base64(self):
        invalid_base64 = 'This is not a valid base64 string'
        with self.assertRaises(ValueError):
            state = GameState()
            state.deserialize(invalid_base64)

    def test_deserialize_invalid_json(self):
        invalid_json = 'eyJsZXR0ZXJzIjogImFiY2RlIiwgIndvcmRzIjogWyJjYXQiLCAiZG9nIl0='  # Invalid JSON
        with self.assertRaises(ValueError):
            state = GameState()
            state.deserialize(invalid_json)

    def test_deserialize_missing_keys(self):
        missing_keys_json = 'eyJsZXR0ZXJzIjogImFiY2RlIn0='  # Missing 'words' key
        with self.assertRaises(ValueError):
            state = GameState()
            state.deserialize(missing_keys_json)

    def test_deserialize_non_alpha_characters(self):
        non_alpha_json = self.game_state.serialize()
        self.game_state.pool = ['a', 'b', 'c', '1', '2', '3', '!', '@', '#']
        
        state = GameState()
        state.deserialize(non_alpha_json)

        self.assertEqual(state.pool, ['a', 'b', 'c', 'd', 'e'])
        self.assertEqual(state.existing_words, ['cat', 'dog'])

if __name__ == '__main__':
    unittest.main()
