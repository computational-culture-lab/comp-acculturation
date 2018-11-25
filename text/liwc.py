
import os
import csv

from collections import Counter

from text.stemmer import PorterStemmer

"""
This LIWC category extraction implementation uses 
stem-matching rather than sequential regexes
because it's 100x faster that way.

When this file is imported, it loads the lexicon into memory.
This allows it to expose functions for accessing the lexicon--
    get_cats_from_word - for a word, returns LIWC categories
    count_cats - for a list of words, returns overall LIWC category counts

In order for this code to work, the LIWC dictionary file must be downloaded
and dropped into this directory. 
"""


lex_dir = os.path.dirname(os.path.realpath(__file__))
LIWC_FILENAME = os.path.join(lex_dir, "LIWC2007dictionary poster.csv")

if not os.path.exists(LIWC_FILENAME):
    print("error: LIWC csv file must be accessible. Please download the 'LIWC2007dictionary poster.csv' file online and make it accessible here: '%s'" % LIWC_FILENAME)
    exit(1)


def load_lex(filename, verbose=False):
    """
    Reads LIWC csv to build mapping 
    from word stems to lexicon terms

    """
    stemmer = PorterStemmer()
    word2cat, stem2cat = {}, {}
    match, no_match = 0, 0
    csvreader = csv.DictReader(open(filename))
    for row in csvreader:
        for cat, term in row.items():
            term = term.lower()
            if not term:
                continue
            if ".*" in term:
                # This is a prefix
                prefix = term.replace('.*', '')
                stem = stemmer.stem_word(prefix)
                if prefix != stem:
                    no_match += 1
                else: 
                    match += 1
                stem2cat.setdefault(stem, []).append(cat)
            else:
                # Full word
                word2cat.setdefault(term, []).append(cat)
    if verbose:
        print("Loaded LIWC by stem. (%d prefixes matched stems, %d didn't.)" % (match, no_match))
    return word2cat, stem2cat

## Load lexicon
word2cat, stem2cat = load_lex(LIWC_FILENAME)
stemmer = PorterStemmer()

def get_cats_from_word(w):
    w = w.lower()
    if w in word2cat:
        cats = word2cat[w]
    else:
        cats = stem2cat.get(stemmer.stem_word(w), [])
    return cats

def count_cats(words):
    cats = Counter()
    for w in words:
        cats.update(get_cats_from_word(w))
    return cats

def get_cats_from_words(words):
    cats = [c for w in words for c in get_cats_from_word(w)]
    return cats



