
import json
import hashlib
from collections import Counter

from acculturation.lexicon import CSVLexicon
from acculturation.tokenizer import Tokenizer

tokenizer = Tokenizer()


def preprocess_docs(documents, lexicon_csv_fn, out_json_fn,
                        text_key="text",
                        cats_key="terms",
                        custom_doc_fnc=None):
    """
    Given iterator over individual documents,
    performs basic text preprocessing and saves
    preprocessed documents to disk via line-by-line JSON

    Input args:
        documents (list or iterable) - iterable over documents,
            expected to be dictionary-like
        lexicon_csv_fn (string) - filename of lexicon CSV.
            For formatting requirements, see comments in lexicon.py
        out_json_fn (string) - filename of output file
        text_key (string) - document key where text is stored
        cats_key (string) - document key where lexicon category
            counts will be stored
        custom_doc_fnc (bool or fnc) - optional custom 
            document manipulation function. Eg, for pruning
            documents before they're written to disk or
            adding grouping values

    Returns: None
    """
    lex = CSVLexicon(lexicon_csv_fn)
    with open(out_json_fn, 'w') as outf:
        for d in documents:
            d[cats_key] = text_to_lexicon_categories(d[text_key], lex)
            if custom_doc_fnc:
                d = custom_doc_fnc(d)
            outf.write(json.dumps(d) + "\n")
        outf.close()


def text_to_lexicon_categories(txt, lex):
    toks = tokenizer.tokenize(txt)
    cats = lex.get_categories_from_words(toks)
    cats = dict(Counter(cats))
    return cats

