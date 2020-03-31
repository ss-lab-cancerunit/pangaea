# Pangaea

Process academic articles stored in PubMed to extract interaction relations between genes.

There are two stages:
- `downloading`: For this stage, the tool requires **lookup terms** to determine what papers should be parsed. After downloading the specified number of papers that match the lookup terms, the XML file can be parsed for gene interactions.
- `parsing`: For the second stage, the tool requires an **XML file** as well as what genes should look for and the type of interactions. If no arguments are provided, it will use its own gene list and interactions from `pangaea/data/genes.txt` and `pangaea/data/stems.csv`, respectively.

The output of the tool is a JSON file containing the interactions found. Unless the `--output` flag is used to indicate a filename and path for the output file, the output file will be created in the curreent directory using the default name `output.json`.


## Quickstart

### Requirements

- Linux 
- `python3.4` or newer

If you are not using Fedora or CentOS, you may have to separately install `libxml2-devel` (or `libxml2-dev`), `libxslt-devel` (or `libxslt-dev`), and `python-lxml`.

### Install

    $ pip3 install pangaea


### Usage

    $ pangaea download "tp53" --number=5000 

More details [here](usage.md).

