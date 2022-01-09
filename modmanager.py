#!/bin/python3
# Module manager for sonnet modules
# Ultrabear 2021

import sys
import os
import argparse
import shutil
import json

from typing import Optional, List, Tuple, Generator, Type, Dict, Any


class UserError(Exception):
    """
    Special exception that is catched and printed to stderr, exiting with 1
    """
    __slots__ = ()


def try_get_sonnet_dir() -> Tuple[Optional[str], Optional[str]]:

    module_dirname = "sonnet-modules"
    sonnet_dirname = "sonnet-py"

    base = os.listdir()

    sonnet_dir: Optional[str] = None
    module_dir: Optional[str] = None

    if sonnet_dirname in base:
        sonnet_dir = f"{sonnet_dirname}/"
    elif all(i in base for i in ("cmds", "dlibs", "libs")):
        sonnet_dir = "./"
    elif sonnet_dirname in os.listdir(".."):
        sonnet_dir = f"../{sonnet_dirname}/"

    if module_dirname in base:
        module_dir = f"{module_dirname}/"
    elif "mod" in base:
        module_dir = "./"
    elif module_dirname in os.listdir(".."):
        module_dir = f"../{module_dirname}/"

    return sonnet_dir, module_dir


potential_dirs = try_get_sonnet_dir()

SONNET_DIR = os.environ.get("SONNET_PATH") or potential_dirs[0]
SONNET_MOD_DIR = os.environ.get("SONNET_MOD_PATH") or potential_dirs[1]
VALID_INSTALL_NAMES = [("cmd_", "cmds"), ("dlib_", "dlibs"), ("lib_", "libs")]

if SONNET_DIR is None or SONNET_MOD_DIR is None:
    raise RuntimeError("Could not grab SONNET_PATH or SONNET_MOD_PATH (You may need to add paths to env vars)")


class BJsonConfig:
    __slots__ = "commands", "tables", "configs", "events", "caches", "files", "version"
    def __init__(self, data: Dict[str, Any]) -> None:
        self.commands: List[str] = data.get("commands", [])
        self.tables: List[str] = data.get("tables", [])
        self.configs: List[str] = data.get("configs", [])
        self.events: List[str] = data.get("events", [])
        self.caches: List[str] = data.get("caches", [])
        self.files: List[str] = data.get("files", [])
        self.version: str = data.get("version", "0.0.0")

class ModuleEntry:
    __slots__ = "author", "name", "version"
    def __init__(self, author: str, name: str, version: str) -> None:
        self.author = author
        self.name = name
        self.version = version

def bloat_json_to_obj(filename: str) -> BJsonConfig:
    with open(filename, "rb") as fp:
        return BJsonConfig(json.load(fp))


class ModuleDB:
    """ModuleDB stores the state of modules in a file for version control"""
    __slots__ = "_fp", "_modules"

    def __init__(self) -> None:
        try:
            self._fp = open(f"{SONNET_DIR}.modules.info", "r+", encoding="utf8")
        except FileNotFoundError:
            self._fp = open(f"{SONNET_DIR}.modules.info", "w+", encoding="utf8")

        preparsed = self._fp.read().split("\n")
        self._modules: List[ModuleEntry] = []

        for i in filter(lambda s: s, preparsed):
            author, name, version = i.split("/")
            self._modules.append(ModuleEntry(author, name, version))

    def __enter__(self) -> "ModuleDB":
        return self

    def install(self, author: str, modname: str) -> BJsonConfig:
        info = bloat_json_to_obj(f"{SONNET_MOD_DIR}mod/{author}/{modname}/bloat.json")

        if info.version == "0.0.0":
            print(f"Warning: Module {author}/{modname}: has no version specified, it will not be auto updated")

        self._modules.append(ModuleEntry(author, modname, info.version))

        return info


    def uninstall(self, author: str, modname: str) -> None:
        delidx: Optional[int] = None

        for idx, i in enumerate(self._modules):
            if i.author == author and i.name == modname:
                delidx = idx

        if delidx is not None:
            del self._modules[delidx]
        else:
            print(f"Warning: {author}/{modname}: This module is not in the install file")

    def save(self) -> None:
        self._fp.seek(0)
        for i in self._modules:
            self._fp.write(f"{i.author}/{i.name}/{i.version}\n")
        self._fp.truncate()

    def __exit__(self, e_type: Optional[Type[Exception]], ex: Optional[Exception], tb: Any) -> None:
        self.save()
        self._fp.close()
        if e_type:
            raise e_type(ex)


def get_module_filenames(user: str, modulename: str) -> List[str]:

    moduledir = os.listdir(f"{SONNET_MOD_DIR}mod/{user}/{modulename}")

    return [i for i in moduledir if i.endswith(".py")]


def file_yielder(user: str, modulename: str) -> Generator[Tuple[str, str], None, None]:

    filtered = get_module_filenames(user, modulename)

    for i in filtered:
        for fprefix, folder in VALID_INSTALL_NAMES:
            if i.startswith(fprefix):
                yield i, folder
                break


def install_module(user: str, modulename: str) -> None:
    print(f"Installing {user}/{modulename}")

    # Validation pass
    for i, folder in file_yielder(user, modulename):
        if os.path.isfile(f"{SONNET_DIR}{folder}/{i}"):
            raise UserError(f"ERROR: File {SONNET_DIR}{folder}/{i} already exists")

    # Writing pass
    for i, folder in file_yielder(user, modulename):
        print(f"Installing {i} to {SONNET_DIR}{folder}/{i}")
        shutil.copy(f"{SONNET_MOD_DIR}mod/{user}/{modulename}/{i}", f"{SONNET_DIR}{folder}/{i}")

    with ModuleDB() as db:
        db.install(user, modulename)

def uninstall_module(user: str, modulename: str) -> None:
    print(f"Uninstalling {user}/{modulename}")

    # Validation pass
    for fname, folder in file_yielder(user, modulename):
        if not os.path.isfile(f"{SONNET_DIR}{folder}/{fname}"):
            raise UserError(f"ERROR: File {SONNET_DIR}{folder}/{fname} does not exist")

    # Writing pass
    for fname, folder in file_yielder(user, modulename):
        print(f"Deleting {SONNET_DIR}{folder}/{fname}")
        os.remove(f"{SONNET_DIR}{folder}/{fname}")

    with ModuleDB() as db:
        db.uninstall(user, modulename)

def validate_modulename(modname: str) -> Tuple[str, str]:

    split = modname.split("/")

    if len(split) != 2 or any("." in i for i in split):
        raise UserError(f"ERROR: Module name: {modname}, invalid schema")

    if not os.path.isdir(f"{SONNET_MOD_DIR}mod/{split[0]}/{split[1]}"):
        raise UserError(f"ERROR: Module {modname} is not a path")

    # TODO(ultrabear) add validation for bloat.json stuff

    return split[0], split[1]


def main(args: List[str]) -> int:

    parser = argparse.ArgumentParser()

    parser.add_argument("-S", help="Install the module to the sonnet install directory", dest="install")
    parser.add_argument("-R", help="Uninstall a module from the sonnet install directory", dest="uninstall")
    #TODO(ultrabear): add this
    #parser.add_argument("-U", action="store_true", help="Update all installed packages", dest="update")

    parsed = parser.parse_args()

    if parsed.install is not None:
        install_module(*validate_modulename(parsed.install))
    elif parsed.uninstall is not None:
        uninstall_module(*validate_modulename(parsed.uninstall))
    else:
        raise UserError("Neither install nor uninstall specified, try --help")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except UserError as e:
        sys.stderr.write("\033[91m")
        print(e, file=sys.stderr, flush=True)
        sys.stderr.write("\033[0m")
        sys.exit(1)
