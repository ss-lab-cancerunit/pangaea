#!/usr/bin/env python3
import argparse
import time
import re
import os
import sys
import json
import subprocess
from urllib3.exceptions import ProtocolError

import requests

SEARCH_URL = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'
FETCH_URL = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'
POST_URL = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/epost.fcgi'

MAX_POST_LIMIT = 1000
MAX_IDS_LIMIT = 100000
BATCH_IDS = 1000000
OUTPUT_EXT = 'xml'
SLEEP_TIME = 1
LARGER_SLEEP_TIME = 60

END_TAG = '</PubmedArticleSet>'

def fix_format(output_file):
    """Fix the XML file

    Because the data is downloaded in batches of `MAX_POST_LIMIT`,
    there are multiple XML files concatenated together.
    However, parsers typically expect a single continuous
    XML document within an XML file, so the printing process
    will filter tags introduced due to the merge of XML documents.

    This function calls external tools such as the shell and `sed`
    to make the process quick.
    """
    subprocess.call([
        'sed', # Call `sed`
        '-i',  # Replace the file being processed (instead of outputting to `stdout` for instance)
        '-r',  # Allow advanced regular expressions
        # Skip first four lines, and delete all matches of:
        # <?xml vers, <!DOCTYPE, </PubmedArticleSet>, or <PubmedArticleSet>
        # if they appear at the beginning of a line.
        r'4,${/(^<\?xml vers)|(^<!DOCTYPE)|(^<\/?PubmedArticleSet>)/d}',
        output_file])
    # Because the final </PubmedArticleSet> was deleted as well above,
    # add the closing tag at the end of the file
    with open(output_file, 'a') as text_file:
        text_file.write(END_TAG)

    return output_file


def get_xml(query_key, web_env, count, output_file):
    """Get XML files from the Entrez queue

    This downloads in batches of `MAX_POST_LIMIT` to adhere
    to the rules imposed by Entrez API
    """
    print("Downloading {:,} results to {}".format(count, output_file))
    with open(output_file, "ab") as text_file:
        for retstart in range(0, count, MAX_POST_LIMIT):
            print("Downloading from ID {:,}...".format(retstart))
            time.sleep(SLEEP_TIME)
            payload = {
                'db': 'pubmed',
                'retmode': 'xml',
                'WebEnv': web_env,
                'query_key': query_key,
                'retstart': retstart,
                'retmax': min(MAX_POST_LIMIT, count - retstart),
            }
            try:
                r = requests.get(FETCH_URL, params=payload)
            except requests.exceptions.ChunkedEncodingError:
                print("Request failed")
                continue
            except requests.exceptions.SSLError:
                print("Request failed. Waiting {} seconds".format(LARGER_SLEEP_TIME))
                time.sleep(LARGER_SLEEP_TIME)
                continue
            text_file.write(r.text.encode('utf-8'))
    fix_format(output_file)



def post_ids(ids):
    """Post IDs to the Entrez server

    Entrez recommend to post the IDs to their servers
    and then retrieve them in batches via a get request
    at `FETCH_URL`. Uses `query_key` and `WebEnv` for
    identification.
    """
    payload = {
        'db': 'pubmed',
        'id': ','.join(ids),
    }
    r = requests.post(POST_URL, data=payload)
    if r.status_code != 200:
        sys.exit('Response {}: {}'.format(r.status_code, r.reason))
    try:
        query_key = re.findall(r'<QueryKey>(\d)+', r.text)[0]
    except IndexError:
        sys.exit("Keyword(s) returned no results")
    web_env = re.findall(r'<WebEnv>([\w.]+)', r.text)[0]
    return query_key, web_env, len(ids)


def get_ids(terms, number, sort, ids_list=[], debug=False):
    """Return IDs of articles to be downloaded

    To honour the requirements of the API, each request asks for at most
    MAX_IDS_LIMIT
    """
    print("Fetching {:,} IDs...".format(number))
    results = []
    for retstart in range(0, number, MAX_IDS_LIMIT):
        payload = {
            'db': 'pubmed',
            'retmode': 'json',
            'retstart': retstart,
            'retmax':  min(MAX_IDS_LIMIT, number - retstart),
            'sort': sort,
            'term': terms,
            'usehistory': 'y'
        }
        
        print("Fetching from ID {:,}...".format(retstart))
        r = requests.get(SEARCH_URL, params=payload)
        time.sleep(SLEEP_TIME)
        try:
            results.extend(r.json()['esearchresult']['idlist'])
        except KeyError:
            sys.exit('The API did not return a list of IDs')
        except json.JSONDecodeError as e:
            if debug:
                raise e
            else:
                sys.exit('There was a problem decoding the JSON response while fetching IDs.')
    return results


def get_args():
    parser = argparse.ArgumentParser(
        description="Download XML from Pubmed database")
    parser.add_argument(
            "terms", type=str,
            help="Keywords to search for")
    parser.add_argument(
        '--sort', '-s', type=str, default='relevance',
        help='Sorting method (relevance or date)')
    parser.add_argument(
        '--number', '-n', type=int,
        default=10, help='Number of files to fetch')
    parser.add_argument(
        '--output', '-o', type=str, default='output.xml',
        help='Output filename')
    parser.add_argument(
        '--ids', '-i', action="store_true",
        help='Save IDs')
    parser.add_argument(
        '--debug', '-d', action="store_true",
        help='Show debug messages')
    parser.set_defaults(ids=False, debug=False)
    return parser.parse_args()


def save_ids(ids, output_filename):
    with open(output_filename, 'a') as f:
        json.dump(ids, f)


def parse_filename(filename):
    return '{}.{}'.format(os.path.splitext(filename)[0], 'xml')


def download_pubmed(terms, number, output_filename, sort='relevance', ids_flag=False, debug=False):
    output_filename = parse_filename(output_filename)
    if os.path.isfile(output_filename):
        sys.exit('ERROR: Output file already exists.')
    ids = get_ids(terms, number, sort, debug=debug)
    if not ids:
        sys.exit('No articles were found.')
    if ids_flag:
        save_ids(ids, output_filename)
        return output_filename
    for index in range(0, len(ids), BATCH_IDS):
        ids_slice = ids[index: index + BATCH_IDS]
        web_env, query_key, count = post_ids(ids_slice)
        get_xml(web_env, query_key, count, output_filename)
    return output_filename


def download():
    args = get_args()
    output_filename = download_pubmed(args.terms, args.number, args.output, args.sort, args.ids, args.debug)
    print('Output appended to {}.'.format(output_filename))

if __name__ == '__main__':
    download()
