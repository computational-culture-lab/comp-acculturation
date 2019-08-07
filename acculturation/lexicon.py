
import os
import csv

from collections import Counter, defaultdict
from acculturation.stemmer import PorterStemmer

"""
This file includes functionality for loading 
a CSV-based lexicon and using this lexicon
to score new text.

A lexicon here is considered to be a mapping
from words to word categories. 

The lexicon CSV should have the following format.
First, the file must include a header, with one 
column titled 'Word' and all other columns assumed 
to be lexical categories. Second, cell values are 
assumed to be boolean indicators of category belonging.
That is, if a cell for word W and column C is not null,
then word W is assumed to map to category C. If the 
cell is empty, however, then word W is assumed to
not map to category C.

This lexicon wrapper also includes support stemmed words.
If a word W ends in "*", then the lexicon entry
is assumed to be a word stem, matching all words with 
the same stem. For example, given the word "privileg*",
other words such as "privileges" and "privileged"
will match the lexicon entry.

A sample lexicon CSV file can be found 
at sample-data/sample-lexicon.csv.

"""

stemmer = PorterStemmer()


class CSVLexicon:

    def __init__(self, lex_fn, word_key='Word'):
        if not os.path.exists(lex_fn):
            print("Error: lexicon file '%s' not found." % lex_fn)
        self.word_key = word_key
        self.word2cat, self.stem2cat = self._load(lex_fn)


    def get_categories_from_word(self, w):
        if w in self.word2cat:
            cats = self.word2cat[w]
        else:
            cats = self.stem2cat.get(stemmer.stem_word(w), [])
        return cats

    def get_category_counts_from_words(self, words):
        cats = Counter()
        for w in words:
            cats.update(self.get_categories_from_word(w))
        return cats

    def get_categories_from_words(self, words):
        cats = [c for w in words for c in self.get_categories_from_word(w)]
        return cats

    def _load(self, fn):
        """
        Reads input csv to build mapping 
        from words and word stems to lexicon categories
        """
        word2cat, stem2cat = defaultdict(list), defaultdict(list)
        csvreader = csv.DictReader(open(fn))
        for row in csvreader:
            if self.word_key not in row:
                print("Error: lexicon must include a '%s' field." % self.word_key)
            w = row[self.word_key]
            cats = [c for c in row if c != self.word_key and row[c]]
            if "*" in w:
                # This entry should match all stems
                stem = stemmer.stem_word(w)
                stem2cat[stem] += cats
            else:
                # Only matches exact word
                word2cat[w] += cats
        return word2cat, stem2cat




