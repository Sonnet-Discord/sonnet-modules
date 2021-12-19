#!/bin/python3
# Module manager for sonnet modules
# Ultrabear 2021

import sys
import os
import argparse
import shutil

from typing import Optional, List, Tuple, Generator


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

    meta_parser = parser.add_subparsers()

    meta_parser.add_parser("install").add_argument("install", help="Install the module to the sonnet install directory")
    meta_parser.add_parser("uninstall").add_argument("uninstall", help="Uninstall a module from the sonnet install directory")

    parsed = parser.parse_args()

    if "install" in parsed:
        install_module(*validate_modulename(parsed.install))
    elif "uninstall" in parsed:
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
