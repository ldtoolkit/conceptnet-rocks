from a_conceptnet import arangodb
from a_conceptnet.database import load_dump_into_database
from pathlib import Path
from typing import Optional
import typer

app = typer.Typer()


@app.command()
def install_arangodb(path: Path = arangodb.DEFAULT_INSTALL_PATH):
    arangodb.install(path)


@app.command()
def start_arangodb(exe_path: Path = arangodb.DEFAULT_INSTALL_PATH, data_path: Path = arangodb.DEFAULT_DATA_PATH):
    arangodb.start(exe_path=exe_path, data_path=data_path)


@app.command()
def stop_arangodb(exe_path: Path = arangodb.DEFAULT_INSTALL_PATH):
    pass


@app.command()
def load(dump_path: Path, edge_count: Optional[int] = None):
    load_dump_into_database(dump_path=dump_path, edge_count=edge_count)