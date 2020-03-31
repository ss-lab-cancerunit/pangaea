from unittest.mock import Mock, patch

from pangaea import download

DEFAULT_TERMS = ['tp53', 10, 'relevance']

def test_filename_parsing_different_extension():
    assert 'foutput.xml' == download.parse_filename('foutput.txt')

def test_filename_parsing_no_extension():
    assert 'foutput.xml' == download.parse_filename('foutput')

def test_filename_parsing_right_extension():
    assert 'foutput.xml' == download.parse_filename('foutput.xml')

def get_ids_result(ids_expected):
    return {
        'esearchresult': {
            'idlist': ids_expected
        }
    }

@patch('pangaea.download.requests.get')
def test_get_ids_simple(mock_get):
    ids_expected = [1, 2, 3]
    mock_get.return_value.json.return_value = get_ids_result(ids_expected)
    ids = download.get_ids(*DEFAULT_TERMS)
    assert ids == ids_expected

@patch('pangaea.download.requests.get')
def test_get_ids_no_ids(mock_get):
    ids_expected = []
    mock_get.return_value.json.return_value = get_ids_result(ids_expected)
    ids = download.get_ids(*DEFAULT_TERMS)
    assert ids == ids_expected
