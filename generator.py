import secrets
import string
from enum import Enum
from typing import Iterable, NamedTuple, Optional, Union


class Mode(NamedTuple):

    lowercase: int
    uppercase: int
    digit: int
    punctuation: int

    @property
    def validity(self):
        if all(i >= 0 for i in self) and sum(self) > 0:
            return True
        else:
            return False

    @classmethod
    def initiate(cls, mode: Optional[Iterable] = None):
        if mode is None:
            return cls(8, 4, 4, 0)
        if isinstance(mode, bytes):
            mode = mode.decode("utf-8")
        if isinstance(mode, str):
            temp = list(mode)
            for index, char in enumerate(mode):
                if not char.isascii() or not char.isdecimal():
                    temp[index] = "-"
            mode = "".join(temp).strip("-").split("-")
        if isinstance(mode, Iterable):
            instance = cls._make(int(i) for i in mode)
            if instance.validity:
                return instance
            else:
                raise ValueError(
                    "elements must be greater than or equal to 0, and "
                    "the sum must be greater than 0"
                )
        else:
            raise ValueError("cannot initiate from given argument")


class ModePreset(Enum):
    DEFAULT = Mode(8, 4, 4, 0)
    UNIFORM = Mode(4, 4, 4, 4)
    ALL_LOWER = Mode(16, 0, 0, 0)
    ALL_UPPER = Mode(0, 16, 0, 0)
    ALL_DIGIT = Mode(0, 0, 16, 0)
    ALL_PUNCTUATION = Mode(0, 0, 0, 16)
    ALL_DIGIT_4 = Mode(0, 0, 4, 0)
    ALL_DIGIT_6 = Mode(0, 0, 6, 0)
    DEFAULT_8 = Mode(4, 2, 2, 0)
    UNIFORM_8 = Mode(2, 2, 2, 2)
    DEFAULT_12 = Mode(8, 2, 2, 0)
    UNIFORM_12 = Mode(3, 3, 3, 3)
    DEFAULT_16 = Mode(8, 4, 4, 0)
    UNIFORM_16 = Mode(4, 4, 4, 4)


class Char(Enum):
    LOWERCASE = string.ascii_lowercase
    UPPERCASE = string.ascii_uppercase
    DIGITS = string.digits
    PUNCTUATION = string.punctuation


class PasswordGenerator:
    """
    Generate random password strings.

    Parameters
    ----------
    mode: Iterable | NoneType
        If 'mode' is an iterable, there must be 4 and only 4 elements
        respectively representing the number of lowercase, uppercase, digit
        and punctuation characters. Elements must be int or can be converted
        to int, which must be greater than or equal to 0, and the sum must be
        greater than 0.

        If 'mode' is None, the numbers of lowercase, uppercase, digit and
        punctuation characters are 8, 4, 4 and 0 respectively.
    """

    __char = tuple([i.value for i in Char])

    def __init__(self, mode: Optional[Iterable] = None):
        self.__mode = Mode.initiate(mode)

    def __get_mode(self):
        return self.__mode

    def set_mode(self, mode):
        self.__mode = Mode.initiate(mode)

    mode = property(fget=__get_mode, fset=set_mode)

    @staticmethod
    def __shuffle(x: list):
        """
        The same algorithm as method 'random.Random.shuffle',
        with the function 'secrets.randbelow' instead.
        """
        for i in reversed(range(1, len(x))):
            # pick an element in x[:i+1] with which to exchange x[i]
            j = secrets.randbelow(i + 1)
            x[i], x[j] = x[j], x[i]

    def generate(self):
        chosen = []
        for index, length in enumerate(self.__mode):
            for _ in range(length):
                chosen.append(secrets.choice(self.__char[index]))
        self.__shuffle(chosen)
        password: str = "".join(chosen)
        return password
