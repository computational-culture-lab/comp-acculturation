
import os
import re
import glob
import sys
import random
from operator import itemgetter
from collections import defaultdict, Counter
import numpy as np

from text.preprocessing import preprocess_text


############

def measure_js_distances(documents, segmentation_key,
                                    text_key='text',
                                    preprocessed=False,
                                    target_segment=None,
                                    liwc_map=True,
                                    vocabsize=1000,
                                    sampling=False, sampsize=10000, 
                                    min_segment_size=100,
                                    verbose=True):
    """
    Given iterator over individual documents, returns pairwise 
    Jensen-Shannon distances between segments.

    Input args:
        documents (list or iterable) - iterable over documents.
            documents are expected to be dictionary-like objects
            with a segmentation_key value and a text_key value.
        segmentation_key (string) - the document key through which
            to access a document's segment for the purposes of these 
            comparisons.
        text_key (string) - the document key through which to access
            a document's text (or a processed version thereof).

    Returns a dictionary of distances between each segment and every other segment.
    If target_segment is specified, only returns distances between that 
    and other segments.
    """

    # Put documents into buckets that we want to compare:
    segments2docs = defaultdict(list)
    for i, msg in enumerate(documents):
        if verbose:
            sys.stderr.write('\r') ; sys.stderr.write('msg %s' % i) ; sys.stderr.flush()
        doc_segment = msg[segmentation_key]
        # Check if document looks tokenized or not
        if not preprocessed:
            # msg[text_key] is now distribution of counts
            msg[text_key] = preprocess_text(msg[text_key], liwc_map=liwc_map)

        segments2docs[doc_segment].append(msg)
    if verbose:
        sys.stderr.write('\n')

    # Reduce size of buckets, if desired:
    if sampling:
        # First get rid of any buckets with insufficient docs
        segments = list(segments2docs.keys())
        for key in segments:
            if len(segments2docs[key]) < sampsize:
                if verbose:
                    print("Too few messages for ", key)
                del segments2docs[key]
        # Now randomly sample
        for key, messages in segments2docs.iteritems():
            random.shuffle(messages)
            segments2docs[key] = random.sample(messages, sampsize)   

    # Throw out segments with too few messages, if desired:
    if min_segment_size:
        segments = list(segments2docs.keys())
        for key in segments:
            if len(segments2docs[key]) < min_segment_size:
                if verbose:
                    print("Too few messages for ", key)
                del segments2docs[key]


    # For each segment, get count distribution over terms:
    dists = {}
    for key, docs in segments2docs.items():

        dists[key] = get_term_count_distribution(docs, vocabsize=vocabsize, toks_key=text_key)

    # Now measure pairwise distances:
    distances = {}
    segments = sorted(segments2docs.keys())

    if verbose and len(segments) > 1:
        if not target_segment:
            sys.stderr.write('Measuring pairwise distances for %d segments\n' % len(segments))
        else:
            sys.stderr.write('Measuring distances between "%s" and %d other segments\n' % (target_segment, len(segments)-1))
    
    for i, seg1 in enumerate(segments):
        if verbose:
            sys.stderr.write('\r') ; sys.stderr.write('seg %s' % i) ; sys.stderr.flush()
        for seg2 in segments[i+1:]:
            if target_segment and target_segment not in (seg1, seg2):
                continue
            js_dist = jensen_shannon(dists[seg1], dists[seg2])
            distances[(seg1, seg2)] = js_dist
            distances[(seg2, seg1)] = js_dist # Fill in symmetric distances
    
    if verbose:
        sys.stderr.write('\n')
    
    return distances



######################################################################
# General utilities        


def get_term_count_distribution(messages, vocabsize=1000, toks_key='toks'):
    # Flatten to a single list of words:
    words = [w for msg in messages for w in msg[toks_key]]
    # Create count dictionary:
    countdict = Counter(words)
    # Vocab size restriction based on frequency:
    countdict = dict(sorted(countdict.items(), key=itemgetter(1), reverse=True)[ : min(len(countdict), vocabsize)])
    # Distribution:
    dist = counts2dist(countdict)
    return dist

def counts2dist(countdict):
    total = float(sum(countdict.values()))
    return {key:val/total for key, val in countdict.items()}

def jensen_shannon(f, g):
    vocab = sorted(set(f.keys()) | set(g.keys()))
    p = np.zeros(len(vocab))
    q = np.zeros(len(vocab))
    for i, w in enumerate(vocab):
        p[i] = f.get(w, 0.0)
        q[i] = g.get(w, 0.0)
    pq = (p + q) / 2.0                
    a = 0.5 * kl(p, pq)
    b = 0.5 * kl(q, pq)
    return np.sqrt(a + b)

def kl(p, q):
    return np.sum(p * safelog2(p/q))

def safelog2(x):
    with np.errstate(divide='ignore'):
        x = np.log2(x)
        x[np.isinf(x)] = 0.0
        return x


######################################################################



