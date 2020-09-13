from conceptnet_rocks import arangodb
from conceptnet_rocks.database import load_dump_into_database
from pathlib import Path
from typing import Optional
import sys
import typer


app = typer.Typer()


@app.command()
def install_arangodb(path: Path = arangodb.DEFAULT_INSTALL_PATH):
    arangodb.install(path)


@app.command()
def start_arangodb(
        exe_path: Path = arangodb.DEFAULT_INSTALL_PATH,
        data_path: Path = arangodb.DEFAULT_DATA_PATH,
        connection_uri: str = arangodb.DEFAULT_CONNECTION_URI,
        database: str = arangodb.SYSTEM_DATABASE,
        username: str = arangodb.DEFAULT_USERNAME,
        password: str = arangodb.DEFAULT_PASSWORD,
):
    arangodb.start(
        exe_path=exe_path,
        data_path=data_path,
        connection_uri=connection_uri,
        database=database,
        username=username,
        password=password,
    )


@app.command()
def stop_arangodb():
    arangodb.stop()


@app.command()
def is_arangodb_running(
        connection_uri: str = arangodb.DEFAULT_CONNECTION_URI,
        database: str = arangodb.SYSTEM_DATABASE,
        username: str = arangodb.DEFAULT_USERNAME,
        password: str = arangodb.DEFAULT_PASSWORD,
):
    status_code = (
        0
        if arangodb.is_running(
            connection_uri=connection_uri,
            database=database,
            username=username,
            password=password,
        ) else
        1
    )
    sys.exit(status_code)


@app.command()
def load(
        dump_path: Path,
        edge_count: Optional[int] = None,
        arangodb_exe_path: Path = arangodb.DEFAULT_INSTALL_PATH,
        data_path: Path = arangodb.DEFAULT_DATA_PATH
):
    load_dump_into_database(
        dump_path=dump_path,
        edge_count=edge_count,
        arangodb_exe_path=arangodb_exe_path,
        data_path=data_path,
    )
