import xml.etree.ElementTree as elementTree
import subprocess
import pathlib
import stat
import json
import os

from typing import Union


def create_dir(file_path: Union[str, pathlib.Path]):
    file_path = pathlib.Path(file_path)

    if file_path.suffix:  # If a suffix exists it's a file
        file_path.parent.resolve().mkdir(parents=True, exist_ok=True)

    else:
        file_path.mkdir(parents=True, exist_ok=True)


def create_file(file_path: Union[str, pathlib.Path]):
    file_path = pathlib.Path(file_path)

    if not file_path.parent.exists():
        create_dir(file_path.parent)

    with open(file_path.resolve().__str__(), "w") as file:
        file.write("")


def save_json(file_path: Union[str, pathlib.Path], data_dict: dict, suffix: str = "json", compress=False):
    file_path = pathlib.Path(file_path)
    file_path = file_path if file_path.suffix == f".{suffix}" else file_path.parent.joinpath(f"{file_path.stem}.{suffix}")

    if not file_path.parent.exists():
        create_dir(file_path)

    if compress:
        with open(file_path, "w") as open_file:
            json.dump(data_dict, open_file, indent=None, separators=(',', ':'))

    else:
        with open(file_path, "w") as open_file:
            json.dump(data_dict, open_file, indent=4)


def load_json(file_path: Union[str, pathlib.Path]) -> dict:
    file_path = pathlib.Path(file_path)

    if not file_path.exists():
        print(f"{file_path} does not exist")

        return dict()

    with open(file_path, "r") as open_file:
        data_dict = json.load(open_file)

    return data_dict


def load_txt(file_path: Union[str, pathlib.Path]) -> str:
    file_path = pathlib.Path(file_path)

    if not file_path.exists():
        print(f"{file_path} does not exist")

        return str()

    with open(file_path, "r") as file:
        text = file.read()

    return text


def load_xml_tree_root(file_path: Union[str, pathlib.Path]) -> elementTree.ElementTree:
    tree = elementTree.parse(file_path)

    return tree.getroot()


def file_path_read_only(file_path: Union[str, pathlib.Path]) -> bool:
    file_path = pathlib.Path(file_path)

    try:
        with file_path.open('a'):  # Open in append mode to check if writable
            is_read_only = False

    except IOError:
        is_read_only = True

    return is_read_only


def set_file_path_read_only(file_path: Union[str, pathlib.Path], read_only: bool):
    file_path = pathlib.Path(file_path)

    if read_only:
        file_path.chmod(file_path.stat().st_mode & ~stat.S_IWUSR)

    else:
        file_path.chmod(file_path.stat().st_mode | stat.S_IWUSR)


def get_files_in_directory(directory: str, file_type: Union[str, list[str]] = None) -> list[pathlib.Path]:
    directory = pathlib.Path(directory)

    all_files = [each_file for each_file in directory.iterdir() if each_file.is_file()]

    if file_type:
        file_type = file_type if isinstance(file_type, list) else [file_type]

        all_files = [each_file for each_file in all_files if each_file.suffix[1:] in file_type]

    return all_files


def open_dir(file_path: Union[str, pathlib.Path], highlight_file: bool = False):
    file_path = pathlib.Path(file_path)
    
    if highlight_file:
        # This is slow and makes me sad
        subprocess.Popen(fr'explorer /select,"{str(file_path)}')
    else:
        os.startfile(file_path.parent)
