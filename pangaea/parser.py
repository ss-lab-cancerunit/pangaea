"""Process PubMed papers stored in XML format for gene relations.

This module works from a path of an XML file
towards writing to a CSV file gene relations found
in the papers within the XML file.
"""

import os
import json
import string
import copy
import csv
import itertools
import functools
import multiprocessing as mp
import logging
import threading

from . import models, utils

from tqdm import tqdm
from lxml import etree

#logger = mp.log_to_stderr(logging.DEBUG)

class Parser:
    def __init__(self, xml_file, model, output_file, cores):
        self.model = model
        self.output_file = output_file
        self.manager = mp.Manager()
        self.queue = self.manager.Queue()
        self.cores = cores or mp.cpu_count()

        if not os.path.exists(xml_file):
            raise ValueError("File {} does not exist.".format(xml_file))
        self.xml_file = xml_file

    def parse_papers(self):
        """Parse papers from an XML file into chunks.

        Yields:
            dict: A dictionary containing the relevant information of a
                single article.
        """
        for event, elem in etree.iterparse(self.xml_file, events=('end',), tag='PubmedArticle', recover=True):
            current_article = {}
            medline_citation = elem.find('MedlineCitation')
            article = medline_citation.find('Article')

            current_article['PMID'] = medline_citation.find('PMID').text
            try:
                current_article['Year'] = article.find('ArticleDate').find('Year').text
            except AttributeError:
                current_article['Year'] = None
            current_article['Journal Title'] = article.find('Journal').find('Title').text
            current_article['Article Title'] = article.find('ArticleTitle').text
            abstract = article.find('Abstract')
            if abstract is not None:
                current_article['Abstract'] = ''.join(abstract.itertext())
                yield current_article
            elem.clear()


    def write_files(self):
        """Write processed data from the queue
        
        This function runs as an asynchronous process, and it is
        the only one that writes to disk. The function is looping
        waiting for the queue to have data before writing it to file.

        The buffer is flushed periodically to balance user feedback and I/O

        Args
            queue (Queue): 
        """
        json_output_file = utils.generate_filename(self.output_file, 'json')
        print('Outputting to {}...'.format(json_output_file))

        result = self.queue.get()
        if not result:
            print('No results.')
            return

        with open(json_output_file, 'w') as f:
            to_write = '[{}, '.format(json.dumps(result))
            counter = 0
            while True:
                result = self.queue.get()
                if not result:
                    to_write = to_write[:-2] + ']' # remove trailing comma
                    f.write(to_write)
                    break
                else:
                    to_write += '{}, '.format(json.dumps(result))
                if counter % 50 == 0:
                    f.write(to_write)
                    to_write = ''
                    f.flush()
                counter += 1


    def process_papers(self):
        """Spawn processes to parse the papers in an XML file.

        The XML file is expected to contain PubMed articles, and the
        expected format is the one provided by the Entrez API.

        The format of the genes set is expected to be a plain text file,
        and each gene should be written on a separate line.

        Args:
            xml_file (str): Path to the XML file
            output_file (str): Path to an output file to write to
            genes_set (str, optional): Path to a file containing a subset of genes
            relations (str, optional): Path to a file containing a new set of relations
            use_synonyms (bool, optional): Whether the synonyms dictionary should be used
        """
        papers = self.parse_papers()

        with mp.Pool(processes=self.cores) as pool:
            threading.Thread(target=self.write_files).start()
            try:
                list(tqdm(pool.imap(functools.partial(self.extract_features, model=self.model, queue=self.queue), papers, chunksize=5)))

            except etree.ParseError:
                print('Error parsing the file. Please check if the file has a valid format.')
                return
            
            self.queue.put(None)


    @staticmethod
    def extract_features(paper, model, queue):
        """Parse paper for gene relations and return them.

        The workflow of the parsing process is described in the project-wide
        README.md. The function parses only one article at a time, so it
        is parallelised for performance improvements (linear scaling with
        multiple CPU).

        To extend the functionality of the software, the parsing of the genes
        is performed by a GenesExtractor instance.

        Args:
            paper (dict): Dictionary containing the relevant article information.
            relation_stems (list): Stems of relation words.
            stopwords (list): Stopwords that are not also gene names
            genes_short (dict): Mapping from gene names (without punctuation)
                to gene name (with punctuation). Only genes with a length 
                <= `LENGTH_THRESHOLD`.
            genes_long (dict): Mapping from gene names (without punctuation)
                to gene name (with punctuation). Only genes with a length 
                > `LENGTH_THRESHOLD`.

        Returns:
            list: List containing relevant information, if any was found.
        """
        paper_info = {}
        abstract = paper['Abstract']
        paper['Article Title'] = paper['Article Title'] or " "
        relations = model.parse(abstract)

        if relations:
            paper_info['Article Title'] = paper['Article Title']
            paper_info['Journal Title'] = paper['Journal Title']
            paper_info['PMID'] = paper['PMID']
            paper_info['Year'] = paper['Year']
            paper_info['Relations'] = relations
            queue.put(paper_info)
