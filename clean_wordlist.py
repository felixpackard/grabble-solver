"""
If you have a wordlist with words that are less than 3 characters,
you can use this script to clean it up.
"""

filename = 'dictionary.txt'

with open(f'./wordlists/{filename}', 'r') as file:
    lines = [line.strip() for line in file if len(line.strip()) >= 3]

with open(f'./wordlists/{filename}', 'w') as file:
    file.write('\n'.join(lines))
