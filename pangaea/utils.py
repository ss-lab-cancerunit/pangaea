import json
import string
import itertools

from . import STOPWORDS_FILE

def process_synonyms(genes, synonyms_file):
    """Process a list of genes into a dictionary with synonyms

    The user may select only a subset of genes to look for,
    rather than the entire dictionary. This function creates
    a new dictionary for the genes used by the user.

    Returns:
        dict: Dictionary containing the gene names provided as keys,
            and the synonyms as values.
    """

    with open(synonyms_file) as f:
        gene_to_syns = json.load(f)

    target_to_syns = {}
    targets_lower = [target.lower() for target in genes]

    for symbol, synonyms in gene_to_syns.items():
        if symbol in genes:
            target_to_syns[symbol] = synonyms
        else:
            for synonym in synonyms:
                if synonym.lower() in targets_lower:
                    target_to_syns[synonym] = synonyms
                    target_to_syns[synonym].append(symbol)
                    break

    return target_to_syns


def get_stopwords(stopwords_file=None):
    """Parse JSON file and returns each word stripped of punctuation.

    This uses a custom made stopwords list as the list was designed
    beforehand to exclude stopwords that are also gene names

    Args:
        stopwords_file (str, optional): Path for the stopwords file.
            Defaults to the module level constnat `STOPWORDS_FILE`.
    Returns:
        list: A list of stopwords with no punctuation
    """
    stopwords_file = STOPWORDS_FILE if not stopwords_file else stopwords_file
    with open(stopwords_file) as f:
        stopwords = json.load(f)
        stopwords_no_punct = [
                "".join(l for l in sw if l not in string.punctuation)
                for sw in stopwords]
        return stopwords_no_punct


def non_null_powerset(words):
    """Create the powerset of a list of words (without the empty set).

    Args:
        words (list): List of words that should be combined.

    Returns:
        list: List of all combinations.
    """
    return [combination for i in range(1, len(words) + 1)
            for combination in itertools.combinations(words,i)]


def generate_filename(filename, ext):
    """Generate a filename with extension
    
    The function tries to accommodate for multiple cases of filename
    ('filename', 'filename.ext', 'file.name.ext') and provide a
    "reasonable" filename back. If an extension already exists,
    it is removed, otherwise it is added. If a file contains
    periods already, the last part (as segmented by periods)
    is considered the extension and therefore removed.
    This would cause unexpected behaviour for filenames which
    contain periods, but no extension (e.g. `file.name` where
    'name' is not an extension)

    Args:
        filename (str): the filename to be worked with
        ext (str): extension to be applied to the string
    
    Returns:
        str: Filename with the applied extension
    """
    trimmed_filename = '.'.join(filename.split('.')[:-1]) or filename
    return '.'.join([trimmed_filename, ext])

def parse_file(filename):
    with open(filename) as f:
        data = f.read().splitlines()
    return data
