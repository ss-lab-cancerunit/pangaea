import string
import itertools
import re
import json
from abc import ABC, abstractmethod

import nltk
from tqdm import tqdm

from . import utils

class RelationsExtractor(ABC):
    @abstractmethod
    def get_relation_words(self, relation_words_file):
        ...

    @abstractmethod
    def parse(self, text):
        ...

    @abstractmethod
    def process_genes(self, filename):
        ...


class NERTagger:
    def parse(self, text):
        "https://academic.oup.com/bioinformatics/article/33/14/i37/3953940"
        import subprocess
        sentences = nltk.sent_tokenize(text)
        input_filename = 'input.txt'
        output_filename = 'output.txt'
        root_dir = '/home/lp488/projects/misc/tagger/'

        with open(input_filename, 'w') as f:
            f.writelines(sentences)

        subprocess.run([os.path.join(root_dir, ".env/bin/python"),
                       os.path.join(root_dir, "tagger.py"),
                       '--model', os.path.join(root_dir, "models/english"),
                       '--input', input_filename,
                       '--output', output_filename])

        with open(output_filename, 'r') as f:
            lines = f.readlines()
        
        genes = []
        for line in lines:
            for group in line.split():
                word, category = group.split('__')
                if category == 'B-MISC':
                    genes.append(word)
        return set(genes)


class RulesExtractor(RelationsExtractor):
    N = 4 # Number of words in n-grams
    TARGET_TAGS = ['NNP', 'NN','JJ', 'VBP'] # Tags that are considered as candidates for genes
    LENGTH_THRESHOLD = 5 # Length at which to split gene names to apply different rules

    def __init__(self, genes_file, relation_words_file,  synonyms_file=None, *args, **kwargs):
        self.relation_words = self.get_relation_words(relation_words_file)
        self.genes_short, self.genes_long = self.process_genes(genes_file, synonyms_file)

    def parse(self, text):
        relations = []
        remove = string.punctuation
        remove = remove.replace("/", "") # don't remove slashes
        pattern = r"[{}]".format(remove) # create the pattern
        sentences = nltk.sent_tokenize(text)

        for sentence in sentences:
            detected_genes = set()
            # Skip sentences which do not containg a relation stem
            relevant_stems = [stem for stem in self.relation_words if stem in sentence]
            if not any(relevant_stems):
                continue

            # Remove punctuation
            sentence_no_punct = re.sub(pattern, '', sentence)
            sentence_no_punct = sentence_no_punct.replace('/', ' / ')
            # Tokenize words and convert sentence to lowercase
            words = nltk.word_tokenize(sentence_no_punct.lower())
            # Remove stopwords
            words_cleaned = [word for word in words if word not in utils.get_stopwords()]
            # POS tag
            tagged_content = nltk.pos_tag(words_cleaned)

            # Examine n-gram
            for ngram in nltk.ngrams(tagged_content, self.N):
                # Skip ngram if it does not contain target tags
                if not any(tag for word, tag in ngram if tag in self.TARGET_TAGS):
                    continue

                for combination in utils.non_null_powerset(ngram):
                    # Skip combination if it does not contain target tags
                    if not any(tag for word, tag in combination if tag in self.TARGET_TAGS):
                        continue
                    new_word = ''.join(word for word, tag in combination)
                    for gene in self.genes_short.keys():
                        if gene == new_word:
                            detected_genes.add(self.genes_short[gene])
                    for gene in self.genes_long.keys():
                        if gene in new_word:
                            detected_genes.add(self.genes_long[gene])

            relations.append({'Genes': list(detected_genes), 'Stems': relevant_stems, 'Sentence': sentence})
        return relations

    def process_genes(self, genes_file, synonyms_file):
        """Parse a JSON file containing genes into 2 dictionaries divided by gene length.

        The function uses the following workflow:
            - Flatten dictionary into a list of both keys and values
            - Transform to lowercase
            - Remove items of 1 letter
            - Create 2 dictionaries based on string length:
                - The key of the dictionary is the gene name without punctuation
                - The value is the original gene name

        The dictionaries are created to detect genes with different punctuation, but still
        be able to retrieve the original name; and the split by length is added to aid the
        gene detection step where different rules are applied depending on the gene length;
        and computing the length at that point is very computationally expensive (i.e. it
        must compute the length of each gene for every word in the abstract, and there may
        be 200,000+ genes). This step speeds up the processing a great deal.

        Returns:
            dict: gene_with_no_punctuation: original_gene_name (only genes 
                with names *shorter or equal* with `length_threshold`)
            dict: gene_with_no_punctuation: original_gene_name (only genes 
                with names *longer* than `length_threshold`)
        """
        
        genes = utils.parse_file(genes_file)
        if synonyms_file:
            gene_to_syns = utils.process_synonyms(genes, synonyms_file)
            genes.extend(list(itertools.chain.from_iterable(gene_to_syns.values())))

        genes = [gene.lower() for gene in genes if len(gene) > 1]
        genes_no_punct = {"".join(l for l in gene if l not in string.punctuation):gene for gene in genes}

        genes_no_punct_short = {
                k:v for k, v in genes_no_punct.items() if len(k) <= self.LENGTH_THRESHOLD}
        genes_no_punct_long = {
                k:v for k, v in genes_no_punct.items() if len(k) > self.LENGTH_THRESHOLD}

        return genes_no_punct_short, genes_no_punct_long

    def get_relation_words(self, filename):
        return utils.parse_file(filename)

class SimpleExtractor(RelationsExtractor):
    def __init__(self, genes_file, relation_words_file):
        self.relation_words = self.get_relation_words(relation_words_file)
        self.genes = self.process_genes(genes_file)

    def parse(self, text):
        sentences = nltk.sent_tokenize(text)
        results = []
        for sentence in sentences:
            sentence = sentence.lower()
            relations = [rel_stem for rel_stem in self.relation_words if rel_stem in sentence]
            if not relations:
                continue
            genes = [gene for gene in self.genes if gene in set(sentence.split())]
            if len(genes) < 2:
                continue
            results.append({'Genes': genes, 'Stems': relations, 'Sentence': sentence})
        return results
            
    def process_genes(self, filename):
        return [gene.lower() for gene in utils.parse_file(filename)]


    def get_relation_words(self, filename):
        return utils.parse_file(filename)
