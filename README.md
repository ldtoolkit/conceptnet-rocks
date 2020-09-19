# ConceptNet Rocks!

[![License](https://img.shields.io/pypi/l/conceptnet-rocks.svg)](https://www.apache.org/licenses/LICENSE-2.0)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/conceptnet-rocks.svg)
[![PyPI](https://img.shields.io/pypi/v/conceptnet-rocks.svg)](https://pypi.org/project/conceptnet-rocks/)

Work is in progress.

The library comes with Apache License 2.0, and is separate from ConceptNet itself, although it uses some parts of its code. The ConceptNet is available under [CC-BY-SA-4.0](https://creativecommons.org/licenses/by-sa/4.0/) license. See [here](https://github.com/commonsense/conceptnet5/wiki/Copying-and-sharing-ConceptNet) for the list of conditions for using ConceptNet data.

This is the official citation for ConceptNet if you use it in research:

> Robyn Speer, Joshua Chin, and Catherine Havasi. 2017. "ConceptNet 5.5: An Open Multilingual Graph of General Knowledge." In proceedings of AAAI 31.

## Installation

```bash
pip install conceptnet-rocks
```

## Usage

### Install ArangoDB

ConceptNet Rocks uses [ArangoDB](https://www.arangodb.com/) for storage, managed by a companion Python [Graph Garden library](https://github.com/ldtoolkit/graph-garden/)  that is automatically installed with ConceptNet Rocks.

Graph Garden can manage the ArangoDB installation for you. To download the latest version of ArangoDB from official website and install it to `~/.arangodb` folder, simply run:

```bash
graph-garden arangodb install
```

For more options execute:

```bash
graph-garden arangodb install --help
```

### Load CSV dump into database

Then you need to load the ConceptNet CSV dump into database. The dump can be downloaded from https://github.com/commonsense/conceptnet5/wiki/Downloads

Let's assume you've downloaded the dump to `~/conceptnet-data/assertions.csv`.

To load the dump, execute:
```bash
conceptnet-rocks-load ~/conceptnet-data/assertions.csv
```

This command will create database in `~/.arangodb/data`. For more options execute:

```bash
conceptnet-rocks-load --help
```

### Run queries

Now you can query ConceptNet. ConceptNet Rocks uses the same simple API as ConceptNet5 for querying:

```python
from conceptnet_rocks import AssertionFinder

af = AssertionFinder()
print(af.lookup("/c/en/test"))
print(af.lookup("/r/Antonym"))
print(af.lookup("/s/process/wikiparsec/2"))
print(af.lookup("/d/wiktionary/en"))
print(af.lookup("/a/[/r/Antonym/,/c/ang/gecyndelic/a/,/c/ang/ungecynde/]"))
```

ConceptNet Rocks uses the same JSON-LD format as the original ConceptNet5:
```python
from conceptnet_rocks import AssertionFinder
from pprint import pprint

af = AssertionFinder()
pprint(af.lookup("/c/en/blow_dryer"))
# [
# ...
#  {'@id': '/a/[/r/AtLocation/,/c/en/blow_dryer/,/c/en/beauty_salon/]',
#   '@type': 'Edge',
#   'dataset': '/d/conceptnet/4/en',
#   'end': {'@id': '/c/en/beauty_salon',
#           '@type': 'Node',
#           'label': 'a beauty salon',
#           'language': 'en',
#           'term': '/c/en/beauty_salon'},
#   'license': 'cc:by/4.0',
#   'rel': {'@id': '/r/AtLocation', '@type': 'Relation', 'label': 'AtLocation'},
#   'sources': [{'@id': '/and/[/s/activity/omcs/omcs1_possibly_free_text/,/s/contributor/omcs/bedume/]',
#                '@type': 'Source',
#                'activity': '/s/activity/omcs/omcs1_possibly_free_text',
#                'contributor': '/s/contributor/omcs/bedume'}],
#   'start': {'@id': '/c/en/blow_dryer',
#             '@type': 'Node',
#             'label': 'a blow dryer',
#             'language': 'en',
#             'term': '/c/en/blow_dryer'},
#   'surfaceText': 'You are likely to find [[a blow dryer]] in [[a beauty salon]]',
#   'weight': 1.0}
# ...
# ]
```

## FAQ

### Why did you create yet another library if original ConceptNet5 exists?

1. Performance. Our benchmark (https://github.com/ldtoolkit/conceptnet-benchmark) has shown that ConceptNet Rocks is
almost 5 times faster than ConceptNet5 for querying assertions by concepts.
2. The original ConceptNet5 library requires PostgreSQL. PostgreSQL does not support the graph databases as a primary model, while ArangoDB is a multi-model database for graph.
3. PostgreSQL generally requires either root permissions to install it using a package manager, or the compilation step. Not anyone have root permissions on their machine or have the compiler installed. ConceptNet Rocks library uses ArangoDB, which can be installed without root permissions using simple command.

### Why is the library called ConceptNet Rocks?

1. Under the hood ArangoDB uses key-value storage called RocksDB.
2. Performance-wise, it does rock!
