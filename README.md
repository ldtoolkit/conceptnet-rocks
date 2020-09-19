# ConceptNet Rocks!

Work is in progress.

The library comes with Apache License 2.0, and is separate from ConceptNet itself, yet it uses some parts of its code. The ConceptNet is available under [CC-BY-SA-4.0](https://creativecommons.org/licenses/by-sa/4.0/) license. See [here](https://github.com/commonsense/conceptnet5/wiki/Copying-and-sharing-ConceptNet) for the list of conditions for using ConceptNet data.

This is the official citation for ConceptNet if you use it in research:

> Robyn Speer, Joshua Chin, and Catherine Havasi. 2017. "ConceptNet 5.5: An Open Multilingual Graph of General Knowledge." In proceedings of AAAI 31.

## Installation

```bash
pip install conceptnet-rocks
```

## Usage

### Install ArangoDB

ConceptNet Rocks uses ArangoDB as a storage. If you do not have it installed, simply execute the following command:

```bash
graph-garden arangodb install
```

This command will download the latest version of ArangoDB from official website and install it to `~/.arangodb` folder.
For more options execute:

```bash
graph-garden arangodb install --help
```

### Load CSV dump into database

Then you need to load CSV dump into database. The dump can be downloaded from:
https://github.com/commonsense/conceptnet5/wiki/Downloads

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

## FAQ

### Why did you create yet another library if original ConceptNet5 exists?

1. Original ConceptNet5 library requires PostgreSQL. In general, this requires either root permissions to install it
using package manager or compilation step. Not anyone have root permissions on their machine or have the compiler
installed. ConceptNet Rocks library uses ArangoDB, which can be installed without root permissions using simple command.
2. PostgreSQL does not support the graph databases as a primary model, while ArangoDB is a multi-model database for
graph.
3. Performance. Our benchmark (https://github.com/ldtoolkit/conceptnet-benchmark) has shown that ConceptNet Rocks is
almost 5 times faster than ConceptNet5 for querying assertions by concepts.

### Why is the library called ConceptNet Rocks?

1. Under the hood ArangoDB uses key-value storage called RocksDB.
2. In my opinion ConceptNet knowledge base really rocks!