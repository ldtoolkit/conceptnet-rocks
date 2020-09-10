import os

from circus import get_arbiter
from circus.arbiter import Arbiter
from pathlib import Path
from pySmartDL import SmartDL
from sys import platform
import stat
import tarfile


DEFAULT_INSTALL_PATH = Path("~/.arangodb").expanduser()
DEFAULT_DATA_PATH = DEFAULT_INSTALL_PATH / "data"


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


def start(exe_path: Path = DEFAULT_INSTALL_PATH, data_path: Path = DEFAULT_DATA_PATH) -> Arbiter:
    if exe_path.name != "arangodb":
        exe_path = get_exe_path(exe_path)
    working_dir_path = exe_path.parent

    env_path = f"{os.environ['PATH']}:{working_dir_path}"

    arbiter = get_arbiter([{
        "cmd": f"{exe_path} --starter.mode single --starter.data-dir {data_path}",
        "working_dir": working_dir_path,
        "env": {"PATH": env_path}
    }], background=True)

    arbiter.start()

    return arbiter
