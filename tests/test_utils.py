from pangaea import utils

GENES_FILE = 'pangaea/data/test/genes_test.txt'
SYNONYMS_FILE = 'pangaea/data/test/gene_to_synonyms_test.json'

def test_parse_file():
    genes = utils.parse_file(GENES_FILE)
    assert len(genes) == 4

def test_process_synonyms():
    genes = utils.parse_file(GENES_FILE)
    syns = utils.process_synonyms(genes, SYNONYMS_FILE)
    assert {'tp53':['p53']} == syns

def test_generate_filename_no_ext():
    assert utils.generate_filename('output', 'json') == 'output.json'

def test_generate_filename_json_ext():
    assert utils.generate_filename('output.json', 'json') == 'output.json'

def test_generate_filename_other_ext():
    assert utils.generate_filename('output.csv', 'json') == 'output.json'
