from pangaea import parser
from pangaea import models

GENES_FILE = 'pangaea/data/test/genes_test.txt'
STEMS_FILE = 'pangaea/data/test/stems_test.csv'
SYNONYMS_FILE = 'pangaea/data/test/gene_to_synonyms_test.json'

def test_one_interaction():
    model = models.RulesExtractor(GENES_FILE, STEMS_FILE)
    results = model.parse('It appears that elf3 regulates tsku')
    assert len(results) == 1

def test_two_interactions():
    model = models.RulesExtractor(GENES_FILE, STEMS_FILE)
    results = model.parse('It appears that elf3 regulates tsku. Also we conclude that tp53 associates with MYC.')
    assert len(results) == 2

def test_synonyms_interaction():
    """p53 is a synonym for tp53"""
    model = models.RulesExtractor(GENES_FILE, STEMS_FILE, synonyms_file=SYNONYMS_FILE)
    results = model.parse('We conclude that p53 associates with MYC.')
    assert len(results) == 1

def test_no_synonyms_interaction():
    """p53 is a synonym for tp53"""
    model = models.RulesExtractor(GENES_FILE, STEMS_FILE)
    results = model.parse('We conclude that p53 associates with MYC.')
    assert len(results) == 0
