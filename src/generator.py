import secrets
from enum import Enum
from typing import Iterable, NamedTuple, Optional

from .utils import Char


class Mode(NamedTuple):

    lowercase: int
    uppercase: int
    digit: int
    punctuation: int

    @property
    def valid(self) -> bool:
        if all(isinstance(i, int) and i >= 0 for i in self) and sum(self) > 0:
            return True
        else:
            return False

    @classmethod
    def make(cls, mode: Optional[Iterable] = None) -> "Mode":
        if mode is None:
            return cls(8, 4, 4, 0)
        if isinstance(mode, bytes):
            mode = mode.decode("utf-8")
        if isinstance(mode, str):
            temp = [*mode]
            for index, char in enumerate(mode):
                if not char.isdecimal():
                    temp[index] = "-"
            mode = "".join(temp).strip("-").split("-")
        if isinstance(mode, Iterable):
            instance = cls._make(int(i) for i in mode)
            if instance.valid:
                return instance
            else:
                raise ValueError(
                    "values must be greater than or equal to 0, and "
                    "the sum must be greater than 0"
                )
        else:
            raise ValueError("invalid argument")


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


class PasswordGenerator:
    """
    Generate random password strings.

    Parameters
    ----------
    mode: Iterable | NoneType
        If 'mode' is Iterable, there must be 4 and only 4 values
        respectively representing the number of lowercase, uppercase, digit
        and punctuation characters. Values must be int or can be converted
        to int, which must be greater than or equal to 0, and the sum must be
        greater than 0.

        If 'mode' is None, the numbers of lowercase, uppercase, digit and
        punctuation characters are 8, 4, 4 and 0 respectively.
    """

    __char = (
        Char.LOWERCASE.value,
        Char.UPPERCASE.value,
        Char.DIGITS.value,
        Char.PUNCTUATION.value
    )

    def __init__(self, mode: Optional[Iterable] = None) -> None:
        self.__mode = Mode.make(mode)

    def __get_mode(self) -> Mode:
        return self.__mode

    def __set_mode(self, mode: Iterable) -> None:
        self.__mode = Mode.make(mode)

    mode = property(fget=__get_mode, fset=__set_mode)

    def set_mode(self, mode: Iterable) -> "PasswordGenerator":
        self.__set_mode(mode)
        return self

    @staticmethod
    def __shuffle(x: list, /) -> None:
        """
        The same algorithm as method 'random.Random.shuffle',
        with the function 'secrets.randbelow' instead.
        """
        for i in reversed(range(1, len(x))):
            # pick an element in x[:i+1] with which to exchange x[i]
            j = secrets.randbelow(i + 1)
            x[i], x[j] = x[j], x[i]

    def generate(
        self,
        mode: Optional[Iterable] = None,
        *,
        unique: bool = False
    ) -> str:
        """
        If 'unique' is True and a value in 'mode' exceeds the volume of
        the characters it represents, excess part will be omitted.
        """
        if mode is None:
            _mode = self.__mode
        else:
            _mode = Mode.make(mode)
        chosen = []
        for index, length in enumerate(_mode):
            if not unique:
                for _ in range(length):
                    chosen.append(secrets.choice(self.__char[index]))
            else:
                list_ = [*self.__char[index]]
                for _ in range(length):
                    try:
                        choice = secrets.choice(list_)
                    except IndexError:
                        break
                    chosen.append(choice)
                    list_.remove(choice)
        self.__shuffle(chosen)
        password = "".join(chosen)
        return password
