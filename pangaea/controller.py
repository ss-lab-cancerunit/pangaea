#!/usr/bin/env python3
"""Main module to parse papers for gene relations"""
import argparse
import os
import sys

from . import GENES_FILE, STEMS_FILE, SYNONYMS_FILE
from . import models
from .download import download_pubmed
from .parser import Parser
from .version import __version__

def get_args():
    """Parse shell arguments"""
    parser = argparse.ArgumentParser(
        description="Parse PubMed articles for gene interactions")
    parser.add_argument( '--version', '-v', action='version',
        version='%(prog)s {}'.format(__version__))
    subparsers = parser.add_subparsers(dest='mode',
        help='Download new articles, or parse local XML file')
    subparsers.required = True

    # Parent parser (shared arguments)
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        '--output', '-o', type=str, default='output',
        help='Output filename')
    parent_parser.add_argument(
        '--genes', '-g', type=str, default=GENES_FILE,
        help='Use a file which contains genes to filter by (separated by newline)')
    parent_parser.add_argument(
        '--relations', '-r', type=str, default=STEMS_FILE,
        help='Use a file which contains new relation words')
    parent_parser.add_argument(
        '--synonyms', '-s', type=str, dest='synonyms_file',
        help='Look up synonyms for the genes (use "default" for default synonyms database)')
    parent_parser.add_argument(
        '--model', '-m', action='store', dest='model', default='rules',
        choices=['simple', 'rules'],
        help='Select the model used for parsing the text'
    )
    parent_parser.add_argument(
        '--cores', '-c', type=int, dest='cores', default=0,
        help='Select the model used for parsing the text'
    )

    # Download parser
    parser_download = subparsers.add_parser('download',
            help='Download articles from PubMed based on keywords', parents=[parent_parser])
    parser_download.add_argument(
        'terms', type=str,
        help='Terms to be searched for and downloaded')
    parser_download.add_argument(
        '--number', '-n', type=int, default=10,
        help='Number of articles to be downloaded')

    # Local parser
    parser_local = subparsers.add_parser('local',
            help='Parse local XML file', parents=[parent_parser])
    parser_local.add_argument(
        'xml_file', type=str,
        help='XML file to be parsed')

    return parser.parse_args()

def download_and_parse():
    args = get_args()
    if args.synonyms_file == 'default':
        args.synonyms_file = SYNONYMS_FILE
    if args.mode == 'download':
        xml_file = download_pubmed(args.terms, args.number, output_filename=args.output)
    elif args.mode == 'local':
        xml_file = args.xml_file

    if args.model == 'simple':
        model = models.SimpleExtractor(args.genes, args.relations)
    elif args.model == 'rules':
        model = models.RulesExtractor(args.genes, args.relations, args.synonyms_file)

    try:
        parser = Parser(xml_file, model, args.output, args.cores)
        print('Processing papers from {}'.format(xml_file))
        parser.process_papers()
    except ValueError as e:
        sys.exit('\nERROR: {}'.format(e))
