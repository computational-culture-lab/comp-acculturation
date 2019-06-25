
import os
import csv
import json
import re

try:
    import mailparser
except:
    print("Warning: failed to load mail-parser module. This will be an issue if you want to process .eml files.")

try:
    import unidecode
except:
    print("Warning: failed to load unidecode module. This will be an issue if you want to process .eml files.")



###########################################

def _get_fns_from_dir(dir_fn, ext):
    """
    Search dir and subdirs for all files with given extension
    """
    if not os.path.isdir(dir_fn):
        # Input is a filename not a dir
        return [dir_fn]
    fns = []
    for root, dirs, files in os.walk(dir_fn, topdown=False):
        fns += [os.path.join(root, fn) for fn in files if fn.split(".")[-1] == ext]
    return fns

###########################################


class CsvDataReader:

    def __init__(self, csv_fn):
        self.fns = _get_fns_from_dir(csv_fn, "csv")

    def __iter__(self):
        for fn in self.fns:
            with open(fn) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    yield row
                f.close()


###########################################


class JsonDataReader:

    """
    Expectation for these files is that 
    each individual line in the file is a
    json-serialized document
    """

    def __init__(self, json_fn):
        self.fns = _get_fns_from_dir(json_fn, "json")


    def __iter__(self):
        for fn in self.fns:
            with open(fn) as f:
                for i,line in enumerate(f):
                    d = json.loads(line)
                    yield d
                f.close()

    @staticmethod
    def write(docs, out_fn):
        with open(out_fn, 'w') as outf:
            for d in docs:
                outf.write(json.dumps(d) + "\n")
            outf.close()



###########################################




class EmlDataReader:

    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.fns = _get_fns_from_dir(base_dir, "eml")

    def __iter__(self):
        """
        Finds all .eml files in self.base_dir
        and subdirectories of self.base_dir.
        Does its best to parse each email before
        releasing.
        """

        # Eml exports often include duplicate emails.
        # We will try to limit the duplicates we release
        msg_ids = set()
        for fn in self.fns:
            msg = mailparser.parse_from_file(fn)
            if msg.message_id in msg_ids:
                continue
            msg_ids.add(msg.message_id)
            # Do our best to clean the msg body
            body = self._clean_body(msg.body)
            e = {
                "message_id": msg.message_id,
                # Keep only email addrs, not attempted parsed names
                "from": msg.from_[0][1],
                # Combine to and cc fields (i.e., no distinction made
                #   between direct messages and group messages)
                "to": [a[1] for a in msg.to] + [a[1] for a in msg.cc],
                "date": str(msg.date),
                "subject": msg.subject,
                "body": body,
                "attachments": [a['filename'] for a in msg.attachments]
            }
            if not e['from'] or not e['to']:
                continue
            yield e

    # Regexes for some common quoted text beginnings
    QUOTED_TXT_RES = [
        ## With names & email addresses
        re.compile(r"On (Mon|Tue|Wed|Thu|Fri|Sat|Sun|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday), (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December) [0-9]+, 201[0-9][,]? (at )?[0-9]+:[0-9][0-9][ ]?(A|P)M[,]? [ a-zA-Z\.\-\"]+[\s]<[\n]?(?:[\w._%+-]+@[\w._%+-]+\.\w{2,})(\n?)>[\s]?wrote:"),
        re.compile(r"On (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December) [0-9]+, 201[0-9](,)? (at )?[0-9]+:[0-9][0-9] (AM|PM)?[ ]?[,]? [ a-zA-Z\.\-\"]+[\s]<[\n]?(?:[\w._%+-]+@[\w._%+-]+\.\w{2,})(\n?)>[\s]?wrote:"),
        re.compile(r"On 201[0-9]-[0-9][0-9]-[0-9][0-9](,)? (at )?[0-2]?[0-9]:[0-9][0-9][ ]?, [ a-zA-Z\.\-\"]+[\s]<[\n]?(?:[\w._%+-]+@[\w._%+-]+\.\w{2,})[\n]?>[\s]wrote:"),
        re.compile(r"On [0-9]?[0-9] (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December) 201[0-9](,)? (at )?[0-9]+:[0-9][0-9][ ]?(AM|PM)?[ ]?[,]? [ a-zA-Z\.\-\"]+[\s]<[\n]?(?:[\w._%+-]+@[\w._%+-]+\.\w{2,})(\n?)>[\s]?wrote:"),
        ## With names but no email addresses
        re.compile(r"On (Mon|Tue|Wed|Thu|Fri|Sat|Sun|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday), (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December) [0-9]+, 201[0-9](,)? (at )?[0-9]+:[0-9][0-9] (A|P)M[ ]?[,]? [ a-zA-Z\.\-\"]+[\s]*wrote:"),
        re.compile(r"On (Mon|Tue|Wed|Thu|Fri|Sat|Sun|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday), (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December) [0-9]+, 201[0-9][,]? [ a-zA-Z\.\-\"]+[\s]<[\n]?(?:[\w._%+-]+@[\w._%+-]+\.\w{2,})(\n?)>[\s]?wrote:"),
        re.compile(r"On (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December) [0-9]+, 201[0-9](,)? (at )?[0-9]+:[0-9][0-9][ ]?(AM|PM)?[ ]?[,]?[ ]?[ a-zA-Z\.\-\"]+[\s]*wrote:"),
        re.compile(r"On 201[0-9]-[0-9][0-9]-[0-9][0-9](,)? (at )?[0-2]?[0-9]:[0-9][0-9][ ]?,[ ]?[ a-zA-Z\.\-\"]+[\s]<[\n]?(?:[\w._%+-]+@[\w._%+-]+\.\w{2,})[\n]?>[\s]wrote:"),
        re.compile(r"On [0-9]?[0-9] (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December) 201[0-9](,)? (at )?[0-9]+:[0-9][0-9][ ]?(AM|PM)?[ ]?[,]? [ a-zA-Z\.\-\"]+[\s]wrote:"),
        ## Different date format
        re.compile(r"On [0-9]?[0-9]/[0-9]?[0-9]/201[0-9] (at )?[0-2]?[0-9]:[0-9][0-9][ ]?(AM|PM)?, [ a-zA-Z\.\-\"]+[\s]<[\n]?(?:[\w._%+-]+@[\w._%+-]+\.\w{2,})[\n]?>[\s]wrote:"),
        re.compile(r"On [0-9]?[0-9]/[0-9]?[0-9]/201[0-9] (at )?[0-2]?[0-9]:[0-9][0-9][ ]?(AM|PM)?, [ a-zA-Z\.\-\"]+[\s]wrote:"),
        ## Other boundary markers
        re.compile(r"----- Original [Mm]essage -----"),
        re.compile(r"--- mail_boundary ---"),
        re.compile(r"[Ss]ent from my (iPhone|Windows|Android|mobile)"),
        re.compile(r"[Ss]ent: (Mon|Tue|Wed|Thu|Fri|Sat|Sun|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)[,]? (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December) [0-9]+, 201[0-9](,)? (at )?[0-9]+:[0-9][0-9]"),
    ]

    def _clean_body(self, body):
        """
        This function attempts to strip quoted text 
        from an email body so that only the text actually 
        written by the email sender remains.

        Email formats are messy and heterogeneous, 
        and this function does not catch all quoted text 
        or all signatures and should not be considered a 
        "complete" (and certainly not an elegant ha!) solution. 
        We recommend testing and expanding this functionality 
        using your own data. (For example, you may also want to
        catch and remove automated messages, etc.)
        """

        body = unidecode.unidecode(body)
        # Strip quoted text
        for quot_re in self.QUOTED_TXT_RES:
            body = quot_re.split(body)[0]
        # Try to remove inserted newlines
        # to recover intended paragraph splits--
        # rough and dirty style
        lines = body.split("\n")
        chunks = []
        active_chunk = lines[0]
        for i in range(1, len(lines)):
            prev_line = lines[i-1]
            curr_line = lines[i]
            if len(prev_line) >= 65 and len(prev_line) <= 75:
                # curr_line probably used to be part of prev_line
                active_chunk += " " + curr_line
            else:
                chunks.append(active_chunk)
                active_chunk = curr_line
        chunks.append(active_chunk)
        body = "\n".join(chunks)
        body = body.replace("    ", " ")
        return body



