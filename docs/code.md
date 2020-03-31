# Overview

Main code files:

 - `controller.py`

 Contains the `download_and_parse()` entry point that triggers all the subsequent processes. Here, the CLI flags are first parsed and processed. If the tool is launched in `download` mode, then the `download_pubmed` function is first called to obtain the XML file. Otherwise, it continues with the provided XML file, instantiates the model indicated by the `--model` flag, and it is passed to the Parser object after which it calls the `process_papers()` method. Thus, the file controls the workflow and brings together the separate parts of the tool.

 - `parser.py`

Defines the `Parser` class which reads the XML file in chunks, spawns processes for parsing articles in parallel, and handles writing the results  to disk.

 - `models.py`

Contains the models implemented for parsing abstracts. The ``RelationsExtractor` abstract class designates a template specifying the methods that should be implemented by models that inherit from it. Here `RulesExtractor` contains all functionality for parsing a piece of text (abstract, in this case) and return a dictionary that can be written to disk later.

 - `utils.py`

Contains several helper functions such as processing synonyms if required, fetching stopwords, and generate filenames.

