"""
Methods in 'User', 'Key' and 'Group' assume all instances are valid
for performance concern. They are NOT recommended to use ouside the
module level. Please pass arguments carefully or exceptions may occur.
"""

import re
from bisect import insort
from collections import Counter, UserDict, UserList
from copy import deepcopy
from dataclasses import dataclass, field
from typing import (Any, Dict, Hashable, Iterable, List, Mapping, NamedTuple,
                    Optional, Union)


class Pair(NamedTuple):
    key: Hashable
    value: Any


@dataclass(order=True, repr=False)
class User:

    username: str
    password: str = field(compare=False)
    notes: Optional[str] = field(compare=False)
    __deleted: bool = field(compare=False)

    def __setattr__(self, __name, __value) -> None:
        if __name in ("username", "password"):
            if not isinstance(__value, str):
                raise TypeError
        elif __name == "notes":
            if not (isinstance(__value, str) or __value is None):
                raise TypeError
        elif __name == f"_{self.__class__.__name__}__deleted":
            if not isinstance(__value, bool):
                raise TypeError
        else:
            raise AttributeError
        return super().__setattr__(__name, __value)

    def __init__(
        self,
        username: str,
        password: str,
        notes: Optional[str] = None
    ) -> None:
        self.username = username
        self.password = password
        self.notes = notes
        self.__deleted = False

    @property
    def valid(self) -> bool:
        return not self.__deleted

    def delete(self) -> "User":
        self.__deleted = True
        return self

    def recover(self) -> "User":
        self.__deleted = False
        return self

    def asdict(self) -> Optional[dict]:
        if self.__deleted:
            return None
        else:
            dict_ = {
                "username": self.username,
                "password": self.password,
                "notes": self.notes
            }
            return dict_

    export = asdict

    def __repr__(self) -> str:
        if not self.__deleted:
            return f"{self.__class__.__name__}(__deleted__)"
        else:
            repr_ = (
                f"{self.__class__.__name__}"
                f"(username='{self.username}', password='{self.password}')"
            )
            return repr_


class _UrlList(UserList):
    """
    Filter arguments but not raise exception when initiate or call
    method 'insort'.
    """
    def __setattr__(self, __name: str, __value: List[str]) -> None:
        if __name == "data":
            if not isinstance(__value, list):
                raise TypeError
            for i, j in enumerate(__value):
                if not isinstance(j, str):
                    raise TypeError
                __value[i] = j.rstrip("/")
            __value.sort()
        else:
            raise AttributeError
        return super().__setattr__(__name, __value)

    def insort(self, url: str) -> None:
        if isinstance(url, str):
            insort(self.data, url.rstrip("/"))

    def __init__(self, *urls: str) -> None:
        self.data: List[str] = []
        for i in urls:
            self.insort(i)


class _UserDict(UserDict):
    """
    Filter arguments but not raise exception when initiate.

    If multiple 'User' instances with same username are passed when initiate,
    only the LAST VALID one will remain. If none of them is valid, the last
    one will remain.

    Note:
        A 'User' instance is valid if its property 'valid' is True.
    """
    def __setattr__(self, __name: str, __value: Dict[str, User]) -> None:
        if __name == "data":
            if not isinstance(__value, dict):
                raise TypeError
            for i, j in __value.items():
                if not isinstance(j, User):
                    raise TypeError
                if i != j.username:
                    raise ValueError
        else:
            raise AttributeError
        return super().__setattr__(__name, __value)

    def __init__(self, *users: User) -> None:
        self.data: Dict[str, User] = {}
        for i in users:
            if isinstance(i, User):
                if i.username not in self.data or i.valid:
                    self.data[i.username] = i

    def __setitem__(self, key: str, item: User) -> None:
        if not isinstance(item, User):
            raise TypeError
        if key != item.username:
            raise ValueError
        if key not in self.data or item.valid:
            return super().__setitem__(key, item)


@dataclass(order=True, repr=False)
class Key:

    keyname: str
    description: Optional[str] = field(compare=False)
    url_list: _UrlList = field(compare=False)
    user_dict: _UserDict = field(compare=False)
    __deleted: bool = field(compare=False)

    def __setattr__(self, __name, __value) -> None:
        if __name == "keyname":
            if not isinstance(__value, str):
                raise TypeError
        elif __name == "description":
            if not (isinstance(__value, str) or __value is None):
                raise TypeError
        elif __name == "url_list":
            if not isinstance(__value, _UrlList):
                raise TypeError
        elif __name == "user_dict":
            if not isinstance(__value, _UserDict):
                raise TypeError
        elif __name == f"_{self.__class__.__name__}__deleted":
            if not isinstance(__value, bool):
                raise TypeError
        else:
            raise AttributeError
        return super().__setattr__(__name, __value)

    def __init__(
        self,
        keyname: str,
        user: User,
        *,
        description: Optional[str] = None,
        url: Optional[str] = None,
        url_list: Optional[Iterable[str]] = None,
        user_list: Optional[Iterable[User]] = None,
    ) -> None:
        self.keyname = keyname
        self.description = description
        _temp: list = []
        if url is not None:
            _temp.append(url)
        if url_list is not None:
            _temp.extend(url_list)
        self.url_list = _UrlList(*_temp)
        _temp.clear()
        _temp.append(user)
        if user_list is not None:
            _temp.extend(user_list)
        self.user_dict = _UserDict(*_temp)
        self.__deleted = False

    @property
    def valid(self) -> bool:
        return not self.__deleted

    @property
    def valid_users(self) -> List[User]:
        list_: List[User] = []
        for i in self.user_dict.values():
            if isinstance(i, User) and i.valid:
                list_.append(i)
        return list_

    def delete(self) -> "Key":
        self.__deleted = True
        return self

    def recover(self) -> "Key":
        self.__deleted = False
        return self

    def aspair(self) -> Optional[Pair]:
        if self.__deleted:
            return None
        else:
            value = {
                "description": self.description,
                "url": deepcopy(self.url_list),
                "userlist": self.valid_users
            }
            return Pair(self.keyname, value)

    export = aspair

    def __repr__(self) -> str:
        if self.__deleted:
            return f"{self.__class__.__name__}(__deleted__)"
        else:
            sep = "\n\t"
            valid_users = self.valid_users
            if len(valid_users) <= 4:
                repr_ = (
                    f"{self.__class__.__name__}"
                    f"(keyname='{self.keyname}', userlist=[{sep}"
                    f"{sep.join(repr(i) for i in valid_users)}\n])"
                )
            else:
                repr_ = (
                    f"{self.__class__.__name__}"
                    f"(keyname='{self.keyname}', userlist=[{sep}"
                    f"{repr(valid_users[0])}{sep}"
                    f"{repr(valid_users[1])}{sep}"
                    f"...{sep}"
                    f"{repr(valid_users[-1])}\n]"
                )
            return repr_