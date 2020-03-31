from pkg_resources import resource_filename

# This is meant to maintain functionality when distributing as a package
STOPWORDS_FILE = resource_filename(__name__, 'data/stopwords.json')
SYNONYMS_FILE = resource_filename(__name__, 'data/gene_to_synonyms.json')
GENES_FILE = resource_filename(__name__, 'data/genes.txt')
STEMS_FILE = resource_filename(__name__, 'data/stems.csv')
MODELS = ['simple', 'rules', 'ml']
