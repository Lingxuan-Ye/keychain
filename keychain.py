from bisect import insort
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Union


@dataclass(order=True)
class User:
    """
    Will NOT check whether the arguments are valid when initiating.
    """
    username: str
    password: str = field(compare=False)
    notes: List[str] = field(compare=False)

    def __init__(self, username: str, password: str, *notes: str) -> None:
        self.username = username
        self.password = password
        self.notes = list(notes)

    @property
    def valid(self) -> bool:
        if all((
            isinstance(self.username, str),
            isinstance(self.password, str),
            isinstance(self.notes, list),
            *(isinstance(i, str) for i in self.notes)
        )):
            return True
        else:
            return False

    def add_note(self, note: str) -> "User":
        insort(self.notes, note)
        return self

    def del_note(self, index: int = -1, *, del_all: bool = False) -> "User":
        if del_all:
            self.notes.clear()
        try:
            self.notes.pop(index)
        except IndexError:
            pass
        return self

    def asdict(self) -> dict:
        return deepcopy(self.__dict__)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}('{self.username}')"


@dataclass(order=True)
class Key:
    """
    Will NOT check whether the arguments are valid when initiating.
    """
    website: str
    description: Optional[str] = field(repr=False, compare=False)
    url_list: List[str] = field(repr=False, compare=False)
    user_list: List[User] = field(compare=False)

    def __init__(
        self,
        *,
        website: str,
        description: Optional[str] = None,
        url: Optional[str] = None,
        user: Union[User, Iterable]
    ) -> None:
        self.website = website
        self.description = description
        if url is None:
            self.url_list = []
        else:
            self.url_list = [url]
        if isinstance(user, User):
            self.user_list = [user]
        else:
            self.user_list = [User(*user)]

    @property
    def valid(self) -> bool:
        if all((
            isinstance(self.website, str),
            isinstance(self.description, str),
            isinstance(self.url_list, list),
            *(isinstance(i, str) for i in self.url_list),
            *(isinstance(i, User) for i in self.user_list),
        )) and all(i.valid for i in self.user_list):
        # for statement:
        #   'a and b'
        # if
        #   'bool(a) is False'
        # then the statement is equal to 'a' (not 'bool(a)')
        # even if 'b' will raise exception
        #
        # statement 'all(i.valid for i in self.user_list)'
        # may raise exception if 'i' is not an instance of 'User'
            return True
        else:
            return False

    def add_url(self, url: str) -> "Key":
        insort(self.url_list, url)
        return self

    def del_url(self, index: int = -1, *, del_all: bool = False) -> "Key":
        if del_all:
            self.url_list.clear()
        try:
            self.url_list.pop(index)
        except IndexError:
            pass
        return self

    def add_user(self, username: str, password: str, *notes: str) -> "Key":
        user = User(username, password, *notes)
        insort(self.user_list, user)
        return self

    def del_user(self, index: int = -1, *, del_all: bool = False) -> "Key":
        if del_all:
            self.user_list.clear()
        try:
            self.user_list.pop(index)
        except IndexError:
            pass
        return self

    def asdict(self) -> dict:
        """
        May raise exception if some member in 'self.user_list' is not
        an instance of 'User'.
        """
        dict_ = deepcopy(self.__dict__)
        dict_["userlist"] = [i.asdict() for i in self.user_list]
        dict_.pop("website")
        return {self.website: dict_}

    def sort(self) -> "Key":
        self.url_list.sort()
        self.user_list.sort()
        return self


class KeyChain:

    def __init__(
        self,
        core: Optional[Iterable[Key]] = None,
        others: Optional[Iterable[Key]] = None
    ) -> None:
        if core is None:
            self.__core = []
        elif isinstance(core, Iterable) and all(i.valid for i in core):
            self.__core = list(core)
        else:
            raise TypeError(
                "argument 'core' must be 'Iterable' or 'NoneType', "
                "if an Iterable is given, every iteration must yeild an "
                "VALID instance of 'Key'"
            )
        if others is None:
            self.__others = []
        elif isinstance(others, Iterable) and all(i.valid for i in others):
            self.__others = list(others)
        else:
            raise TypeError(
                "argument 'others' must be 'Iterable' or 'NoneType', "
                "if an Iterable is given, every iteration must yeild an "
                "VALID instance of 'Key'"
            )

    @property
    def core(self) -> List[Key]:
        return self.__core

    def add_to_core(self, key_: Key) -> "KeyChain":
        insort(self.__core, key_)
        return self

    def del_from_core(
        self,
        index: int = -1,
        *,
        del_all: bool = False
    ) -> "KeyChain":
        if del_all:
            self.__core.clear()
        try:
            self.__core.pop(index)
        except IndexError:
            pass
        return self

    @property
    def others(self) -> List[Key]:
        return self.__others

    def add_to_others(self, key_: Key) -> "KeyChain":
        insort(self.__others, key_)
        return self

    def del_from_others(
        self,
        index: int = -1,
        *,
        del_all: bool = False
    ) -> "KeyChain":
        if del_all:
            self.__others.clear()
        try:
            self.__others.pop(index)
        except IndexError:
            pass
        return self

    def sort(self) -> "KeyChain":
        self.__core.sort()
        for i in self.__core:
            i.sort()
        self.__others.sort()
        for j in self.__others:
            j.sort()
        return self

    def asdict(self) -> dict:
        self.sort()
        core_: List[dict] = [i.asdict() for i in self.__core]
        others_: List[dict] = [j.asdict() for j in self.__others]
        return {"core": core_, "others": others_}

    def __repr__(self) -> str:
        self.sort()
        if len(self.__core) <= 5:
            core_repr = f"Core({', '.join(repr(i) for i in self.__core)})"
        else:
            core_repr = f"Core({repr(self.__core[0])}, " \
                      + f"{repr(self.__core[1])}, ..., " \
                      + f"{repr(self.__core[-1])})"
        if len(self.__others) <= 5:
            others_repr = f"Core({', '.join(repr(i) for i in self.__others)})"
        else:
            others_repr = f"Others({repr(self.__others[0])}, " \
                        + f"{repr(self.__others[1])}, ..., " \
                        + f"{repr(self.__others[-1])})"
        return f"{self.__class__.__name__}({core_repr}, {others_repr})"
