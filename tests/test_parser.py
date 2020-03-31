from pangaea.parser import Parser

XML_FILE = 'pangaea/data/test/tp53_test.xml'

def test_parse_papers():
    parser = Parser(XML_FILE, model=None, output_file='', cores=4) 
    papers = list(parser.parse_papers())
    assert len(papers) == 5
