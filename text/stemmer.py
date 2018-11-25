
"""
Code credit: NLTK
Bird, Steven, Edward Loper and Ewan Klein (2009).
Natural Language Processing with Python.  O'Reilly Media Inc.
Included to remove full nltk code dependency.
Licensed under the Apache License, Version 2.0
"""

import re

class PorterStemmer:

    ## --NLTK--
    ## Add a module docstring
    """
    A word stemmer based on the Porter stemming algorithm.

        Porter, M. \"An algorithm for suffix stripping.\"
        Program 14.3 (1980): 130-137.

    A few minor modifications have been made to Porter's basic
    algorithm.  See the source code of this module for more
    information.

    The Porter Stemmer requires that all tokens have string types.
    """

    # The main part of the stemming algorithm starts here.
    # Note that only lower case sequences are stemmed. Forcing to lower case
    # should be done before stem(...) is called.

    def __init__(self):

        ## --NEW--
        ## This is a table of irregular forms. It is quite short, but still
        ## reflects the errors actually drawn to Martin Porter's attention over
        ## a 20 year period!
        ##
        ## Extend it as necessary.
        ##
        ## The form of the table is:
        ##  {
        ##  "p1" : ["s11","s12","s13", ... ],
        ##  "p2" : ["s21","s22","s23", ... ],
        ##  ...
        ##  "pn" : ["sn1","sn2","sn3", ... ]
        ##  }
        ##
        ## String sij is mapped to paradigm form pi, and the main stemming
        ## process is then bypassed.

        irregular_forms = {
            "sky" :     ["sky", "skies"],
            "die" :     ["dying"],
            "lie" :     ["lying"],
            "tie" :     ["tying"],
            "news" :    ["news"],
            "inning" :  ["innings", "inning"],
            "outing" :  ["outings", "outing"],
            "canning" : ["cannings", "canning"],
            "howe" :    ["howe"],

            # --NEW--
            "proceed" : ["proceed"],
            "exceed"  : ["exceed"],
            "succeed" : ["succeed"], # Hiranmay Ghosh
            }

        self.pool = {}
        for key in irregular_forms:
            for val in irregular_forms[key]:
                self.pool[val] = key

        self.vowels = frozenset(['a', 'e', 'i', 'o', 'u'])

    def _cons(self, word, i):
        """cons(i) is TRUE <=> b[i] is a consonant."""
        if word[i] in self.vowels:
            return False
        if word[i] == 'y':
            if i == 0:
                return True
            else:
                return (not self._cons(word, i - 1))
        return True

    def _m(self, word, j):
        """m() measures the number of consonant sequences between k0 and j.
        if c is a consonant sequence and v a vowel sequence, and <..>
        indicates arbitrary presence,

           <c><v>       gives 0
           <c>vc<v>     gives 1
           <c>vcvc<v>   gives 2
           <c>vcvcvc<v> gives 3
           ....
        """
        n = 0
        i = 0
        while True:
            if i > j:
                return n
            if not self._cons(word, i):
                break
            i = i + 1
        i = i + 1

        while True:
            while True:
                if i > j:
                    return n
                if self._cons(word, i):
                    break
                i = i + 1
            i = i + 1
            n = n + 1

            while True:
                if i > j:
                    return n
                if not self._cons(word, i):
                    break
                i = i + 1
            i = i + 1

    def _vowelinstem(self, stem):
        """vowelinstem(stem) is TRUE <=> stem contains a vowel"""
        for i in range(len(stem)):
            if not self._cons(stem, i):
                return True
        return False

    def _doublec(self, word):
        """doublec(word) is TRUE <=> word ends with a double consonant"""
        if len(word) < 2:
            return False
        if (word[-1] != word[-2]):
            return False
        return self._cons(word, len(word)-1)

    def _cvc(self, word, i):
        """cvc(i) is TRUE <=>

        a) ( --NEW--) i == 1, and word[0] word[1] is vowel consonant, or

        b) word[i - 2], word[i - 1], word[i] has the form consonant -
           vowel - consonant and also if the second c is not w, x or y. this
           is used when trying to restore an e at the end of a short word.
           e.g.

               cav(e), lov(e), hop(e), crim(e), but
               snow, box, tray.
        """
        if i == 0: return 0  # i == 0 never happens perhaps
        if i == 1: return (not self._cons(word, 0) and self._cons(word, 1))
        if not self._cons(word, i) or self._cons(word, i-1) or not self._cons(word, i-2): return 0

        ch = word[i]
        if ch == 'w' or ch == 'x' or ch == 'y':
            return 0

        return 1

    def _step1ab(self, word):
        """step1ab() gets rid of plurals and -ed or -ing. e.g.

           caresses  ->  caress
           ponies    ->  poni
           sties     ->  sti
           tie       ->  tie        (--NEW--: see below)
           caress    ->  caress
           cats      ->  cat

           feed      ->  feed
           agreed    ->  agree
           disabled  ->  disable

           matting   ->  mat
           mating    ->  mate
           meeting   ->  meet
           milling   ->  mill
           messing   ->  mess

           meetings  ->  meet
        """
        if word[-1] == 's':
            if word.endswith("sses"):
                word = word[:-2]
            elif word.endswith("ies"):
                if len(word) == 4:
                    word = word[:-1]
                # this line extends the original algorithm, so that
                # 'flies'->'fli' but 'dies'->'die' etc
                else:
                    word = word[:-2]
            elif word[-2] != 's':
                word = word[:-1]

        ed_or_ing_trimmed = False
        if word.endswith("ied"):
            if len(word) == 4:
                word = word[:-1]
            else:
                word = word[:-2]
        # this line extends the original algorithm, so that
        # 'spied'->'spi' but 'died'->'die' etc

        elif word.endswith("eed"):
            if self._m(word, len(word)-4) > 0:
                word = word[:-1]


        elif word.endswith("ed") and self._vowelinstem(word[:-2]):
            word = word[:-2]
            ed_or_ing_trimmed = True
        elif word.endswith("ing") and self._vowelinstem(word[:-3]):
            word = word[:-3]
            ed_or_ing_trimmed = True

        if ed_or_ing_trimmed:
            if word.endswith("at") or word.endswith("bl") or word.endswith("iz"):
                word += 'e'
            elif self._doublec(word):
                if word[-1] not in ['l', 's', 'z']:
                    word = word[:-1]
            elif (self._m(word, len(word)-1) == 1 and self._cvc(word, len(word)-1)):
                word += 'e'

        return word

    def _step1c(self, word):
        """step1c() turns terminal y to i when there is another vowel in the stem.
        --NEW--: This has been modified from the original Porter algorithm so that y->i
        is only done when y is preceded by a consonant, but not if the stem
        is only a single consonant, i.e.

           (*c and not c) Y -> I

        So 'happy' -> 'happi', but
          'enjoy' -> 'enjoy'  etc

        This is a much better rule. Formerly 'enjoy'->'enjoi' and 'enjoyment'->
        'enjoy'. Step 1c is perhaps done too soon; but with this modification that
        no longer really matters.

        Also, the removal of the vowelinstem(z) condition means that 'spy', 'fly',
        'try' ... stem to 'spi', 'fli', 'tri' and conflate with 'spied', 'tried',
        'flies' ...
        """
        if word[-1] == 'y' and len(word) > 2 and self._cons(word, len(word) - 2):
            return word[:-1] + 'i'
        else:
            return word

    def _step2(self, word):
        """step2() maps double suffices to single ones.
        so -ization ( = -ize plus -ation) maps to -ize etc. note that the
        string before the suffix must give m() > 0.
        """
        if len(word) <= 1: # Only possible at this stage given unusual inputs to stem_word like 'oed'
            return word

        ch = word[-2]

        if ch == 'a':
            if word.endswith("ational"):
                return word[:-7] + "ate" if self._m(word, len(word)-8) > 0 else word
            elif word.endswith("tional"):
                return word[:-2] if self._m(word, len(word)-7) > 0 else word
            else:
                return word
        elif ch == 'c':
            if word.endswith("enci"):
                return word[:-4] + "ence" if self._m(word, len(word)-5) > 0 else word
            elif word.endswith("anci"):
                return word[:-4] + "ance" if self._m(word, len(word)-5) > 0 else word
            else:
                return word
        elif ch == 'e':
            if word.endswith("izer"):
                return word[:-1] if self._m(word, len(word)-5) > 0 else word
            else:
                return word
        elif ch == 'l':
            if word.endswith("bli"):
                return word[:-3] + "ble" if self._m(word, len(word)-4) > 0 else word # --DEPARTURE--
            # To match the published algorithm, replace "bli" with "abli" and "ble" with "able"
            elif word.endswith("alli"):
                # --NEW--
                if self._m(word, len(word)-5) > 0:
                    word = word[:-2]
                    return self._step2(word)
                else:
                    return word
            elif word.endswith("fulli"):
                return word[:-2] if self._m(word, len(word)-6) else word # --NEW--
            elif word.endswith("entli"):
                return word[:-2] if self._m(word, len(word)-6) else word
            elif word.endswith("eli"):
                return word[:-2] if self._m(word, len(word)-4) else word
            elif word.endswith("ousli"):
                return word[:-2] if self._m(word, len(word)-6) else word
            else:
                return word
        elif ch == 'o':
            if word.endswith("ization"):
                return word[:-7] + "ize" if self._m(word, len(word)-8) else word
            elif word.endswith("ation"):
                return word[:-5] + "ate" if self._m(word, len(word)-6) else word
            elif word.endswith("ator"):
                return word[:-4] + "ate" if self._m(word, len(word)-5) else word
            else:
                return word
        elif ch == 's':
            if word.endswith("alism"):
                return word[:-3] if self._m(word, len(word)-6) else word
            elif word.endswith("ness"):
                if word.endswith("iveness"):
                    return word[:-4] if self._m(word, len(word)-8) else word
                elif word.endswith("fulness"):
                    return word[:-4] if self._m(word, len(word)-8) else word
                elif word.endswith("ousness"):
                    return word[:-4] if self._m(word, len(word)-8) else word
                else:
                    return word
            else:
                return word
        elif ch == 't':
            if word.endswith("aliti"):
                return word[:-3] if self._m(word, len(word)-6) else word
            elif word.endswith("iviti"):
                return word[:-5] + "ive" if self._m(word, len(word)-6) else word
            elif word.endswith("biliti"):
                return word[:-6] + "ble" if self._m(word, len(word)-7) else word
            else:
                return word
        elif ch == 'g': # --DEPARTURE--
            if word.endswith("logi"):
                return word[:-1] if self._m(word, len(word) - 4) else word # --NEW-- (Barry Wilkins)
            # To match the published algorithm, pass len(word)-5 to _m instead of len(word)-4
            else:
                return word

        else:
            return word

    def _step3(self, word):
        """step3() deals with -ic-, -full, -ness etc. similar strategy to step2."""

        ch = word[-1]

        if ch == 'e':
            if word.endswith("icate"):
                return word[:-3] if self._m(word, len(word)-6) else word
            elif word.endswith("ative"):
                return word[:-5] if self._m(word, len(word)-6) else word
            elif word.endswith("alize"):
                return word[:-3] if self._m(word, len(word)-6) else word
            else:
                return word
        elif ch == 'i':
            if word.endswith("iciti"):
                return word[:-3] if self._m(word, len(word)-6) else word
            else:
                return word
        elif ch == 'l':
            if word.endswith("ical"):
                return word[:-2] if self._m(word, len(word)-5) else word
            elif word.endswith("ful"):
                return word[:-3] if self._m(word, len(word)-4) else word
            else:
                return word
        elif ch == 's':
            if word.endswith("ness"):
                return word[:-4] if self._m(word, len(word)-5) else word
            else:
                return word

        else:
            return word

    def _step4(self, word):
        """step4() takes off -ant, -ence etc., in context <c>vcvc<v>."""

        if len(word) <= 1: # Only possible at this stage given unusual inputs to stem_word like 'oed'
            return word

        ch = word[-2]

        if ch == 'a':
            if word.endswith("al"):
                return word[:-2] if self._m(word, len(word)-3) > 1 else word
            else:
                return word
        elif ch == 'c':
            if word.endswith("ance"):
                return word[:-4] if self._m(word, len(word)-5) > 1 else word
            elif word.endswith("ence"):
                return word[:-4] if self._m(word, len(word)-5) > 1 else word
            else:
                return word
        elif ch == 'e':
            if word.endswith("er"):
                return word[:-2] if self._m(word, len(word)-3) > 1 else word
            else:
                return word
        elif ch == 'i':
            if word.endswith("ic"):
                return word[:-2] if self._m(word, len(word)-3) > 1 else word
            else:
                return word
        elif ch == 'l':
            if word.endswith("able"):
                return word[:-4] if self._m(word, len(word)-5) > 1 else word
            elif word.endswith("ible"):
                return word[:-4] if self._m(word, len(word)-5) > 1 else word
            else:
                return word
        elif ch == 'n':
            if word.endswith("ant"):
                return word[:-3] if self._m(word, len(word)-4) > 1 else word
            elif word.endswith("ement"):
                return word[:-5] if self._m(word, len(word)-6) > 1 else word
            elif word.endswith("ment"):
                return word[:-4] if self._m(word, len(word)-5) > 1 else word
            elif word.endswith("ent"):
                return word[:-3] if self._m(word, len(word)-4) > 1 else word
            else:
                return word
        elif ch == 'o':
            if word.endswith("sion") or word.endswith("tion"): # slightly different logic to all the other cases
                return word[:-3] if self._m(word, len(word)-4) > 1 else word
            elif word.endswith("ou"):
                return word[:-2] if self._m(word, len(word)-3) > 1 else word
            else:
                return word
        elif ch == 's':
            if word.endswith("ism"):
                return word[:-3] if self._m(word, len(word)-4) > 1 else word
            else:
                return word
        elif ch == 't':
            if word.endswith("ate"):
                return word[:-3] if self._m(word, len(word)-4) > 1 else word
            elif word.endswith("iti"):
                return word[:-3] if self._m(word, len(word)-4) > 1 else word
            else:
                return word
        elif ch == 'u':
            if word.endswith("ous"):
                return word[:-3] if self._m(word, len(word)-4) > 1 else word
            else:
                return word
        elif ch == 'v':
            if word.endswith("ive"):
                return word[:-3] if self._m(word, len(word)-4) > 1 else word
            else:
                return word
        elif ch == 'z':
            if word.endswith("ize"):
                return word[:-3] if self._m(word, len(word)-4) > 1 else word
            else:
                return word
        else:
            return word

    def _step5(self, word):
        """step5() removes a final -e if m() > 1, and changes -ll to -l if
        m() > 1.
        """
        if word[-1] == 'e':
            a = self._m(word, len(word)-1)
            if a > 1 or (a == 1 and not self._cvc(word, len(word)-2)):
                word = word[:-1]
        if word.endswith('ll') and self._m(word, len(word)-1) > 1:
            word = word[:-1]

        return word

    def stem_word(self, p, i=0, j=None):
        """
        Returns the stem of p, or, if i and j are given, the stem of p[i:j+1].
        """
        ## --NLTK--
        if j is None and i == 0:
            word = p
        else:
            if j is None:
                j = len(p) - 1
            word = p[i:j+1]

        if word in self.pool:
            return self.pool[word]

        if len(word) <= 2:
            return word # --DEPARTURE--
        # With this line, strings of length 1 or 2 don't go through the
        # stemming process, although no mention is made of this in the
        # published algorithm. Remove the line to match the published
        # algorithm.

        word = self._step1ab(word)
        word = self._step1c(word)
        word = self._step2(word)
        word = self._step3(word)
        word = self._step4(word)
        word = self._step5(word)
        return word


