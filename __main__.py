import argparse
from typing import Callable, Iterable, Optional

import pyperclip

from src import (IO, Group, Help, Key, KeyChain, ModePreset, PasswordGenerator,
                 Printer, Status, User)

print: Callable = Printer()


def password_generate(mode: Optional[Iterable], unique: bool):
    try:
        generator = PasswordGenerator(mode)
    except ValueError:
        print(Status.VALUE_ERROR.value)
    else:
        password = generator.generate(unique=unique)
        pyperclip.copy(password)
        print(Status.GENERATE_SUCCESS.value.format(password=password))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f", "--file",
        help=Help.FILE.value,
        metavar=""
    )


main()
