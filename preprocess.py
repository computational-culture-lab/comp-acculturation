
from utils.datareaders import JsonDataReader, EmlDataReader, CsvDataReader
from text.preprocessing import preprocess_docs

# Different data readers for different
# kinds of input data files
FORMAT_2_READER = {
    'eml': EmlDataReader,
    'json': JsonDataReader,
    'csv': CsvDataReader
}

def preprocess_data(inputfn, outfn, dformat, text_key="text"):
    Constructor = FORMAT_2_READER[dformat]
    if dformat == 'eml':
        text_key = 'body'
    docs = Constructor(inputfn)
    preprocess_docs(docs, outfn, text_key=text_key)



if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--inputfn", type=str, action="store", dest="inputfn", help="Filepath to input data. If filepath is a directory, all files with matching data format will be loaded", required=True)
    parser.add_argument("-o", "--outfn", type=str, action="store", dest="outfn", help="Output filename for preprocessed data", required=True)
    parser.add_argument("-f", "--format", choices=['eml', 'csv', 'json'], action="store", dest="format", help="Input data format (supported: eml, csv, json)", required=True)
    parser.add_argument("-t", "--textkey", type=str, action="store", dest="text_key", help="Key to access text of document (only necessary for csv and json data formats, set to 'body' for eml data)", default="text")
    args = parser.parse_args()

    if args.outfn.split(".")[-1] != "json":
        print("error: outfn must end in '.json'")
        exit(1)

    preprocess_data(args.inputfn, args.outfn, args.format, text_key=args.text_key)
