
import csv

from utils.datareaders import JsonDataReader
from lingdistance.jensen_shannon import measure_js_distances


def measure_distances(inputfn, outfn, comparison_type, group_key=None, min_segment_size=0):
    """
    This function assumes input documents are already preprocessed,
    json-serialized, and written line-by-line to inputfn (such as
    from the output of preprocess.py).
    Each document is assumed to be a python dictionary with a 'toks'
    key that maps to a count distribution of tokens or LIWC categories.
    
    This function supports a few different options for how to define 
    groups to measure distances between, as set by the 'type' parameter:
        - 'dyadic': for all senders a,b with significant correspondence,
            measures the distance between a's messages to b and b's messages to a. 
            This option requires that all documents have "to" and "from" keys.
        - 'individual-to-world': for all users with significant documents,
            measures the distance between all messages sent by user to all messages
            received by user. This option also requires that all documents have "to" and "from" keys.
        - 'group-to-group': this setting sorts documents into groups based on a user-submitted 'group_key'
            (e.g., in organizational contexts, a 'group' could be a business unit). 
            This option requires that the user specifies a group_key.
    
    Note on 'to' and 'from' keys: since messages are generally sent from
        a single individual but can be sent to multiple individuals, the
        'to' key is expected to map to a user string whereas the 'from' key
        is expected to map to a list of user strings.

    Distances between groups are written as a CSV file to outfn
    """
    docs = JsonDataReader(inputfn)
    if comparison_type == "dyadic":
        dists = measure_distances_dyadic(docs, min_segment_size)
    elif comparison_type == "individual-to-world":
        dists = measure_distances_individual_to_world(docs, min_segment_size)
    elif comparison_type == "group-to-group":
        if not group_key:
            print("error: group_key must be set for group-to-group comparisons")
            exit(1)
        dists = measure_js_distances(docs, group_key,
                                        text_key='toks',
                                        preprocessed=True,
                                        min_segment_size=min_segment_size,
                                        verbose=True)
    else:
        print("error: unsupported comparison type '%s'" % comparison_type)
        exit(1)

    # Write distances to CSV
    with open(outfn, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(["Group 1", "Group 2", "Distance"])
        for a,b in dists:
            writer.writerow([a, b, dists[(a,b)]])
        f.close()


def measure_distances_dyadic(docs, min_segment_size):

    # First, get set of users who sent messages
    users = set()
    for d in docs:
        if 'from' not in d:
            print("error: documents must have 'from' key for dyadic comparisons")
            exit(1)
        users.add(d['from'])

    # For each of these users, measure distances with interlocutors
    dists = {}
    for u in users:
        udocs = [d for d in docs if u in get_users_involved(d)]
        udists = measure_js_distances(udocs, 'from',
                                    text_key='toks',
                                    preprocessed=True,
                                    target_segment=u,
                                    min_segment_size=min_segment_size,
                                    verbose=True)
        dists.update(udists)

    return dists


def measure_distances_individual_to_world(docs, min_segment_size):

    # First, get set of users who sent messages
    users = set()
    for d in docs:
        if 'from' not in d:
            print("error: documents must have 'from' key for individual-to-world comparisons")
            exit(1)
        users.add(d['from'])

    # For each of these users, measure distance between sent and received msgs
    dists = {}
    for u in users:
        doc_grouping_fnc = get_individual_or_world_callback(u)
        udocs = [d for d in docs if u in get_users_involved(d)]
        udocs = [doc_grouping_fnc(d) for d in udocs]
        udists = measure_js_distances(udocs, 'group',
                                    text_key='toks',
                                    preprocessed=True,
                                    target_segment=u,
                                    min_segment_size=min_segment_size,
                                    verbose=True)
        dists.update(udists)

    return dists


def get_individual_or_world_callback(user):
    def individual_or_world_callback(d):
        d['group'] = user if d['from'] == user else "world"
        return d
    return individual_or_world_callback


def get_users_involved(d):
    to_users = d['to']
    if not isinstance(to_users, list):
        to_users = [to_users]
    users = set(to_users)
    users.add(d['from'])
    return users



if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--inputfn", type=str, action="store", dest="inputfn", help="Filepath to input data. Documents must be preprocessed and stored in a file of line-by-line json-serialized documents, such as from output of preprocess.py. If filepath is a directory, all .json files in directory will be loaded.", required=True)
    parser.add_argument("-o", "--outfn", type=str, action="store", dest="outfn", help="Output filename for pairwise distances. Output will be written as a CSV file.", required=True)
    parser.add_argument("-t", "--type", type=str, action="store", dest="type", help="Defines the grouping to use for measuring distances between groups. See readme for more detailed explanation.", choices=['dyadic', 'individual-to-world', 'group-to-group'], default="dyadic")
    parser.add_argument("-g", "--group_key", type=str, action="store", dest="group_key", help="Document key that sorts documents into groups. Only required for 'group-to-group' comparisons.")
    parser.add_argument("-n", "--n_min_group_size", type=int, action="store", dest="min_segment_size", help="Minimum number of documents a group must have to be included in measurements", default=0)
    args = parser.parse_args()

    measure_distances(args.inputfn, args.outfn, args.type, group_key=args.group_key, min_segment_size=args.min_segment_size)
