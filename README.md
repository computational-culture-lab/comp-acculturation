# comp-acculturation
Reference implementation for measuring cultural distances between individuals and groups.

## Background

This code is meant as a reference implementation for measuring cultural distances between groups of people based on text (such as in [this paper](https://www.gsb.stanford.edu/faculty-research/working-papers/fitting-or-standing-out-tradeoffs-structural-cultural-embeddedness))

The code can be used out-of-the-box for simple applications or easily modified, cannibalized, or extended for more custom applications. 

We hope this code will help kickstart your own experiments, but we provide no guarantees that it's bug-free (if you stumble upon any... let us know!). 

## How to run

This code requires Python 3 and numpy to run.

Additionally, you must download the LIWC 2007 csv file "LIWC2007dictionary poster.csv" and place it in the "text/" directory. (We cannot distribute this file.)

This code operates in two stages:

#### Preprocesing

Preprocessing takes as input raw messages and outputs LIWC category distributions for those messages. Input data can come in multiple formats: as .eml files (e.g., from an exported email inbox), as .csv files, or as line-by-line json-serialized documents. Preprocessed documents are written to disk as line-by-line json-serialized documents that can be loaded again using the provided `JsonDataReader`. 

We have included sample .eml and .csv datasets derived from the Enron corpus that can be used to test. 

To preprocess the directory of .eml files, navigate to the code directory and type:

`python preprocess.py -i sample-data/enron -o tmp/enron.json -f eml`

Preprocessed documents will be written to "tmp/enron.json."

To preprocess a single .csv file, type:

`python preprocess.py -i sample-data/enron.gender.csv -o tmp/enron.gender.json -f csv -t body`

For more details on the command-line options for this script, simply type:

`python preprocess.py -h`

#### Measurement

Once documents have been preprocessed, we can compute distances between groups. The key here is to define the "groups" that we are interested in measuring distances between. 

This code supports several kinds of grouping and can be easily extended to support more:

1. `dyadic`: for all senders `a`,`b` with significant correspondence, we measure the distance between `a`'s messages to `b` and `b`'s messages to `a`. This option requires that all documents have `to` and `from` keys.
2. `individual-to-world`: for all users `a` with significant documents, measures the distance between all messages sent by user `a` to all messages received by user `a`. This option also requires that all documents have `to` and `from` keys.
3. `group-to-group`: this setting sorts documents into groups based on a user-submitted `group_key` (e.g., in organizational contexts, a `group` could be the business unit a message originated in). This option requires that the user specifies a `group_key`.

To take the preprocessed data from step 1 and measure dyadic distances, type:

`python measure.py -i tmp/enron.json -o tmp/enron.dyadic.distances.csv -t dyadic`

Or to measure distances between genders, type:

`python measure.py -i tmp/enron.gender.json -o tmp/enron.gender.distances.csv -t group-to-group -g gender`

For more details on the command-line options for this script, simply type:

`python measure.py -h`

