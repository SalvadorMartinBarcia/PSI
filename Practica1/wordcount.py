#!/usr/bin/python3 -tt
# Copyright 2010 Google Inc.
# Licensed under the Apache License, Version 2.0
# http://www.apache.org/licenses/LICENSE-2.0

# Google's Python Class
# http://code.google.com/edu/languages/google-python-class/

"""Wordcount exercise
Google's Python class
The main() below is already defined and complete. It calls print_words()
and print_top() functions which you write.
1. For the --count flag, implement a print_words(filename) function that counts
how often each word appears in the text and prints:
word1 count1
word2 count2
...
Print the above list in order sorted by word (python will sort punctuation to
come before letters -- that's fine). Store all the words as lowercase,
so 'The' and 'the' count as the same word.
2. For the --topcount flag, implement a print_top(filename) which is similar
to print_words() but which prints just the top 20 most common words sorted
so the most common word is first, then the next most common, and so on.
Use str.split() (no arguments) to split on all whitespace.
Workflow: don't build the whole program at once. Get it to an intermediate
milestone and print your data structure and sys.exit(0).
When that's working, try for the next milestone.
Optional: define a helper function to avoid code duplication inside
print_words() and print_top().
"""

import sys
import re


def text_to_dict(filename):
    """Función de ayuda que crea un diccionario
    a partir de un texto en el que se encuentran
    las palabras que aparecen y su cantidad de
    apariciones, sin repeticiones"""
    f = open(filename)
    contents = f.read().lower().splitlines()
    f.close()
    words = {}
    for c in contents:
        line = c.split(" ")
        for w in line:
            f = re.sub('[^a-z0-9 \n]', '', w)
            if f in words:
                words[f] += 1
            else:
                words[f] = 1
    return words


def print_words(filename):
    """Mediante text_to_dict, devuelve un
    diccionario ordenando alfabéticamente
    todas las palabras"""
    words = text_to_dict(filename)
    for w in sorted(words):
        print(w + "\t\t\t" + str(words[w]))
    return


def print_top(filename):
    """Mediante text_to_dict, devuelve
    todas las 20 primeras palabas más
    frecuentes y su número de apariciones"""
    words = text_to_dict(filename)
    for w in sorted(words, key=words.get, reverse=True)[1:21]:
        print(w + "\t\t\t" + str(words[w]))
    return


# This basic command line argument parsing code is provided and
# calls the print_words() and print_top() functions which you must define.
def main():
    """Función principal con la que contar
    como deseemos las palabras de un determinado texto"""
    if len(sys.argv) != 3:
        print('usage: ./wordcount.py {--count | --topcount} file')
        sys.exit(1)

    option = sys.argv[1]
    filename = sys.argv[2]
    if option == '--count':
        print_words(filename)
    elif option == '--topcount':
        print_top(filename)
    else:
        print('unknown option: ' + option)
        sys.exit(1)


if __name__ == '__main__':
    main()
