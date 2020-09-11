from arango import ArangoClient, ArangoError
from circus import get_arbiter
from circus.arbiter import Arbiter
from pathlib import Path
from pySmartDL import SmartDL
from sys import platform
from typing import Optional
import os
import psutil
import stat
import tarfile
import time


ARANGODB_DEMON_PROCESS_NAME = "arangod"
CONCEPTNET_ROCKS_PROCESS_NAME = "conceptnet-rocks"
DEFAULT_INSTALL_PATH = Path("~/.arangodb").expanduser()
DEFAULT_DATA_PATH = DEFAULT_INSTALL_PATH / "data"
DEFAULT_PORT = 8529
DEFAULT_CONNECTION_URI = f"http://localhost:{DEFAULT_PORT}"
SYSTEM_DATABASE = "_system"
DEFAULT_USERNAME = "root"
DEFAULT_PASSWORD = ""
DEFAULT_ROOT_PASSWORD = ""
START_SLEEP_DELAY = 0.1
STOP_SLEEP_DELAY = 0.1


def get_exe_path(path: Path = DEFAULT_INSTALL_PATH) -> Path:
    return path / "bin" / "arangodb" if path.name != "arangodb" else path


def install(path: Path = DEFAULT_INSTALL_PATH) -> None:
    if platform != "linux":
        raise RuntimeError("Only GNU/Linux is supported!")

    path = path.expanduser()

    if path.exists():
        raise FileExistsError(f"File exists: {path}")

    path.mkdir(parents=True)

    url = "https://download.arangodb.com/arangodb37/Community/Linux/arangodb3-linux-3.7.2.tar.gz"
    downloader = SmartDL(url, str(path))
    downloader.start()
    archive_path_str = downloader.get_dest()
    tar = tarfile.open(archive_path_str, "r:gz")
    tar.extractall(path)
    tar.close()
    Path(archive_path_str).unlink()
    arangodb_dir_path = next(path.glob("arangodb3*"))
    for p in arangodb_dir_path.iterdir():
        p.rename(path / p.name)
    arangodb_dir_path.rmdir()
    for p in (path / "bin").iterdir():
        p.chmod(p.stat().st_mode | stat.S_IEXEC)


def get_arangodb_demon_process(port: int = DEFAULT_PORT) -> Optional[psutil.Process]:
    try:
        result = next(proc for proc in psutil.process_iter() if proc.name() == ARANGODB_DEMON_PROCESS_NAME)
        if next(True for connection in result.connections() if connection.laddr.port == port):
            return result
    except StopIteration:
        return None


def is_running(
        connection_uri: str = DEFAULT_CONNECTION_URI,
        database: str = SYSTEM_DATABASE,
        username: str = DEFAULT_USERNAME,
        password: str = DEFAULT_PASSWORD,
) -> bool:
    if not bool(get_arangodb_demon_process()):
        return False
    client = ArangoClient(hosts=connection_uri)
    db = client.db(name=database, username=username, password=password)
    try:
        db.version()
        return True
    except ArangoError:
        return False


def start(
        exe_path: Path = DEFAULT_INSTALL_PATH,
        data_path: Path = DEFAULT_DATA_PATH,
        connection_uri: str = DEFAULT_CONNECTION_URI,
        database: str = SYSTEM_DATABASE,
        username: str = DEFAULT_USERNAME,
        password: str = DEFAULT_PASSWORD,
) -> Arbiter:
    if exe_path.name != "arangodb":
        exe_path = get_exe_path(exe_path)
    working_dir_path = exe_path.parent

    env_path = f"{os.environ['PATH']}:{working_dir_path}"

    arbiter = get_arbiter([{
        "cmd": f"{exe_path} --starter.mode single --starter.data-dir {data_path}",
        "working_dir": working_dir_path,
        "env": {"PATH": env_path},
    }], background=True)

    arbiter.start()

    while not is_running(connection_uri=connection_uri, database=database, username=username, password=password):
        time.sleep(START_SLEEP_DELAY)

    return arbiter


def stop():
    arangodb_demon_process = get_arangodb_demon_process()
    if arangodb_demon_process is not None:
        arangodb_launch_script_process = arangodb_demon_process.parent()
        arangodb_launch_script_parent_process = arangodb_launch_script_process.parent()
        if arangodb_launch_script_parent_process.name() == CONCEPTNET_ROCKS_PROCESS_NAME:
            arangodb_launch_script_parent_process.terminate()
        else:
            arangodb_launch_script_process.terminate()


def stop_arbiter(arbiter: Optional[Arbiter]):
    if arbiter is None:
        return

    arbiter.stop()
    # noinspection PyUnresolvedReferences
    while arbiter.is_alive():
        time.sleep(STOP_SLEEP_DELAY)
