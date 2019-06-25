
import os
import re
import glob
import sys
import random
from operator import itemgetter
from collections import defaultdict, Counter
import numpy as np


############

def measure_js_distances(documents, grouping_key,
                                    terms_key='terms',
                                    target_group=None,
                                    target_comparison_fnc=None,
                                    vocabsize=1000,
                                    sampling=False, sampsize=10000, 
                                    min_group_size=100,
                                    verbose=True):
    """
    Given iterator over individual documents, returns 
    Jensen-Shannon distances between groups of documents.

    Input args:
        documents (list or iterable) - iterable over documents.
            Documents are expected to be dictionary-like objects
            with a grouping_key value and a terms_key value.
        grouping_key (string) - the document key through which
            to access a document's group (or groups if maps to a list).
        terms_key (string) - the document key through which to access
            preprocessed document text, assumed to be dict of term or
            lexicon category counts.

    Returns a dictionary of JS distances between groups.
    
    By default, all pairwise distances are measured.     
    If target_group is specified, only returns distances 
    between that and other groups.
    """

    # Put documents into buckets that we want to compare:
    groups2docs = defaultdict(list)
    for i, msg in enumerate(documents):
        if verbose:
            sys.stderr.write('\r') ; sys.stderr.write('msg %s' % i) ; sys.stderr.flush()
        
        # Get the groups the document belongs to
        # Documents can belong to one or multiple groups
        # so we accept both strings and a list of strings 
        # as the grouping_key value
        doc_group = msg[grouping_key]
        doc_groups = doc_group if isinstance(doc_group, list) else [doc_group]
        for gr in doc_groups:
            # Keep only bag-of-words (or bag-of-lexicon categories) from msg
            groups2docs[gr].append(msg[terms_key])

    if verbose:
        sys.stderr.write('\n')

    # Throw out groups with too few messages, if desired:
    if min_group_size:
        groups = list(groups2docs.keys())
        for key in groups:
            if len(groups2docs[key]) < min_group_size:
                if verbose:
                    print("Too few messages for ", key)
                del groups2docs[key]

    # Reduce size of buckets, if desired:
    if sampling:
        # First get rid of any buckets with insufficient docs
        groups = list(groups2docs.keys())
        for key in groups:
            if len(groups2docs[key]) < sampsize:
                if verbose:
                    print("Too few messages for ", key)
                del groups2docs[key]
        # Now randomly sample to bring each group to size
        for key, messages in groups2docs.iteritems():
            groups2docs[key] = random.sample(messages, sampsize)   

    # For each group, get count distribution over terms:
    dists = {}
    for key, docs in groups2docs.items():
        dists[key] = get_term_count_distribution(docs, vocabsize=vocabsize)

    # Now measure pairwise distances:
    distances = {}
    groups = sorted(groups2docs.keys())

    if verbose and len(groups) > 1:
        if not target_group:
            sys.stderr.write('Measuring pairwise distances for %d groups\n' % len(groups))
        else:
            sys.stderr.write('Measuring distances between "%s" and %d other groups\n' % (target_group, len(groups)-1))
    
    for i, g1 in enumerate(groups):
        if verbose:
            sys.stderr.write('\r') ; sys.stderr.write('group %s' % i) ; sys.stderr.flush()
        for g2 in groups[i+1:]:
            if target_group and target_group not in (g1, g2):
                # We only care about one group and it's not here
                continue
            if target_comparison_fnc and not target_comparison_fnc(g1, g2):
                # We asked the caller if they care about this 
                # pair of groups and it turns out they don't
                continue
            js_dist = jensen_shannon(dists[g1], dists[g2])
            distances[(g1, g2)] = js_dist
            distances[(g2, g1)] = js_dist # Fill in symmetric
    
    if verbose:
        sys.stderr.write('\n')
    
    return distances



######################################################################
# General utilities        


def get_term_count_distribution(messages, vocabsize=1000):
    # Flatten to a single list of words:
    words = [w for msg in messages for w in msg]
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



