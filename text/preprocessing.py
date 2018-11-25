
import ujson
import hashlib
from collections import Counter

from text import liwc 
from text.tokenizer import Tokenizer

tokenizer = Tokenizer()


def preprocess_docs(documents, out_json_fn,
                        text_key="text",
                        toks_key="toks",
                        liwc_map=True,
                        tok_hashing=False,
                        custom_doc_fnc=None):
    """
    Given iterator over individual documents,
    performs basic text preprocessing and saves
    preprocessed documents to disk via line-by-line JSON

    Input args:
        documents (list or iterable) - iterable over documents,
            expected to be dictionary-like
        out_json_fn (string) - filename of output file
        text_key (string) - document key where document text is stored
        tokenization (bool) - whether or not to tokenize text
        liwc_map (bool) - whether or not to map tokens to liwc categories
        tok_hashing (bool) - whether or not to hash (anonymize) tokens
        custom_doc_fnc (bool or fnc) - optional custom 
            document manipulation function. Eg, for pruning
            documents before they're written to disk or
            adding segmentation values

    Returns: None
    """
    with open(out_json_fn, 'w') as outf:
        for d in documents:
            d[toks_key] = preprocess_text(d[text_key], liwc_map=liwc_map, tok_hashing=tok_hashing)
            if custom_doc_fnc:
                d = custom_doc_fnc(d)
            outf.write(ujson.dumps(d) + "\n")
        outf.close()


def preprocess_text(txt, liwc_map=True, tok_hashing=False):
    toks = tokenizer.tokenize(txt)
    if liwc_map:
        toks = liwc.get_cats_from_words(toks)
    if tok_hashing:
        toks = [tokhash(t) for t in toks]
    toks = dict(Counter(toks))
    return toks


def tokhash(tok):
    """
    Note! Although this makes tokens "unreadable"
    to humans, original text can still theoretically 
    be recovered by building a reverse mapping
    by applying the same hash function to
    all tokens in the English language
    """
    hash_obj = hashlib.sha1(tok)
    hex_dig = hash_obj.hexdigest()
    return hex_dig



