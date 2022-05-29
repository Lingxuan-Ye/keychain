"""
An object is valid if and only if its property 'valid' is True.
If an object is invalid, it has lower priority to be kept in a higher-level
container. In other words, if multiple objects from same class with same
name are passed to a higher-level container, only the LAST VALID one or
the LAST one (if no one is valid) will remain.
"""

import json
import re
from bisect import insort
from collections import Counter, UserDict, UserList
from copy import deepcopy
from dataclasses import dataclass, field
from typing import (Any, Callable, Dict, Hashable, Iterable, List, NamedTuple,
                    Optional, Union)

from keychain._datetime import *

NoneType = type(None)


class Pair(NamedTuple):
    key: Hashable
    value: Any


def _indent(lines: str, level: int = 1, firstline_indent: bool = False) -> str:
    list_: List[str] = lines.splitlines(keepends=True)
    for _index, _line in enumerate(list_):
        if _index == 0 and not firstline_indent:
            continue
        if level >= 0:
            list_[_index] = "\t" * level + _line
        else:
            for _ in range(abs(level)):
                if _line.startswith("\t"):
                    _line = _line[1:]
            list_[_index] = _line
    return "".join(list_)


@dataclass(order=True, repr=False)
class User:

    username: str
    password: str = field(compare=False)
    notes: Optional[str] = field(compare=False)
    __timestamp: int = field(compare=False)
    __deleted: bool = field(compare=False)

    def __setattr__(
        self,
        __name: str,
        __value: Union[str, bool, NoneType]
    ) -> None:
        if __name in ("username", "password"):
            if not isinstance(__value, str):
                raise TypeError
            super().__setattr__(
                f"_{self.__class__.__name__}__timestamp",
                timestamp()
            )
        elif __name == "notes":
            if not (isinstance(__value, str) or __value is None):
                raise TypeError
        elif __name == f"_{self.__class__.__name__}__timestamp":
            if not isinstance(__value, int):
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
        self.username: str = username
        self.password: str = password
        self.notes: Optional[str] = notes
        self.__timestamp: int = timestamp()
        self.__deleted: bool = False

    @property
    def valid(self) -> bool:
        return not self.__deleted

    @property
    def timestamp(self) -> int:
        return self.__timestamp

    def delete(self) -> "User":
        self.__deleted = True
        return self

    def recover(self) -> "User":
        self.__deleted = False
        return self

    def asdict(self, valid_only: bool = True) -> Optional[dict]:
        if self.__deleted and valid_only:
            return None
        else:
            dict_ = {
                "username": self.username,
                "password": self.password,
                "notes": self.notes,
                "timestamp": self.__timestamp
            }
            return dict_

    export: Callable = asdict

    def __repr__(self) -> str:
        if not self.__deleted:
            return f"{self.__class__.__name__}(__deleted__)"
        else:
            repr_ = (
                f"{self.__class__.__name__}"
                f"(username='{self.username}', password='{self.password}')"
            )
            return repr_


class _URLList(UserList):
    """
    Filter arguments but not raise exception when initiate or call
    method 'insort'.

    Warning:
        - attribute 'data' of '_URLList' instance is not recommended to
          access from outer scope.
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
            if isinstance(i, str):
                insort(self.data, i.rstrip("/"))

    def append(self, url: str) -> None:
        if not isinstance(url, str):
            raise TypeError
        url = url.rstrip("/")
        return super().append(url)

    def extend(self, other: Iterable[str]) -> None:
        list_: List[str] = []
        for i in other:
            if not isinstance(i, str):
                raise ValueError
            list_.append(i.rstrip("/"))
        return super().extend(list_)

    insert: Callable = insort


class _UserDict(UserDict):
    """
    Filter arguments but not raise exception when initiate.

    Warning:
        - attribute 'data' of '_UserDict' instance is not recommended to
          access from outer scope.
    """
    def __setattr__(self, __name: str, __value: Dict[str, User]) -> None:
        if __name == "data":
            if not isinstance(__value, dict):
                raise TypeError
            for i, j in __value.items():
                if not isinstance(i, str):
                    raise TypeError
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
                if i.valid:
                    pass
                elif i.username not in self.data:
                    pass
                elif self.data[i.username].valid:
                    continue
                self.data[i.username] = i

    def __setitem__(self, __key: str, __item: User) -> None:
        if not isinstance(__key, str):
            raise TypeError
        if not isinstance(__item, User):
            raise TypeError
        if __key != __item.username:
            raise ValueError
        if __item.valid:
            pass
        elif __key not in self.data:
            pass
        elif self.data[__key].valid:
            return
        return super().__setitem__(__key, __item)


@dataclass(order=True, repr=False)
class Key:

    keyname: str
    group: Optional[str] = field(compare=False)
    description: Optional[str] = field(compare=False)
    url_list: _URLList = field(compare=False)
    user_dict: _UserDict = field(compare=False)
    __deleted: bool = field(compare=False)

    def __setattr__(
        self,
        __name: str,
        __value: Union[str, _URLList, _UserDict, bool, NoneType]
    ) -> None:
        if __name == "keyname":
            if not isinstance(__value, str):
                raise TypeError
        elif __name == "group":
            if not (isinstance(__value, str) or __value is None):
                raise TypeError
        elif __name == "description":
            if not (isinstance(__value, str) or __value is None):
                raise TypeError
        elif __name == "url_list":
            if not isinstance(__value, _URLList):
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
        group: Optional[str] = None,
        description: Optional[str] = None,
        url: Optional[str] = None,
        url_list: Optional[Iterable[str]] = None,
        user_list: Optional[Iterable[User]] = None
    ) -> None:
        self.keyname: str = keyname
        self.group: Optional[str] = group
        self.description: Optional[str] = description
        list_: list = []
        if url is not None:
            list_.append(url)
        if url_list is not None:
            list_.extend(url_list)
        self.url_list: _URLList = _URLList(*list_)
        list_.clear()
        list_.append(user)
        if user_list is not None:
            list_.extend(user_list)
        self.user_dict: _UserDict = _UserDict(*list_)
        self.__deleted: bool = False

    @property
    def valid(self) -> bool:
        return not self.__deleted

    @property
    def valid_users(self) -> List[User]:
        list_: List[User] = []
        for i in self.user_dict.values():
            _user: User = i  # Of no use but a type hint for 'mypy'.
            if _user.valid:
                insort(list_, _user)
        return list_

    def sort(self) -> None:
        self.url_list.sort()

    def delete(self) -> "Key":
        self.__deleted = True
        return self

    def recover(self) -> "Key":
        self.__deleted = False
        return self

    def aspair(self, valid_only: bool = True) -> Optional[Pair]:
        if self.__deleted and valid_only:
            return None
        else:
            self.sort()
            userlist: List[dict] = []
            for i in self.user_dict.values():
                _user: User = i  # Of no use but a type hint for 'mypy'.
                _export = _user.asdict(valid_only)
                if _export is not None:
                    insort(userlist, _export)
            dict_ = {
                "description": self.description,
                "url": deepcopy(self.url_list),
                "userlist": userlist
            }
            return Pair(self.keyname, dict_)

    export: Callable = aspair

    def __repr__(self) -> str:
        if self.__deleted:
            return f"{self.__class__.__name__}(__deleted__)"
        else:
            _tab, __tab, __sep = "\n\t", "\n\t\t", ",\n\t\t"
            valid_users = self.valid_users
            if len(valid_users) <= 4:
                repr_ = (
                    f"{self.__class__.__name__}("
                    f"{_tab}keyname='{self.keyname}',"
                    f"{_tab}group='{self.group}',"
                    f"{_tab}userlist=["
                    f"{__tab}{__sep.join(repr(i) for i in valid_users)}"
                    f"{_tab}]\n)"
                )
            else:
                repr_ = (
                    f"{self.__class__.__name__}("
                    f"{_tab}keyname='{self.keyname}',"
                    f"{_tab}group='{self.group}',"
                    f"{_tab}userlist=["
                    f"{__tab}{repr(valid_users[0])}"
                    f"{__sep}{repr(valid_users[1])}"
                    f"{__sep}..."
                    f"{__sep}{repr(valid_users[-1])}"
                    f"{_tab}]\n)"
                )
            return repr_


class Group(UserDict):
    """
    Filter arguments but not raise exception when initiate.

    Only 'Key' instances with attribute 'group' being 'None' or equal to
    'self.groupname' will be accepted.

    Warning:
        - attribute 'data' of 'Group' instance is not recommended to
          access from outer scope.
    """
    def __setattr__(
        self,
        __name: str,
        __value: Union[Dict[str, Key], str, bool]
    ) -> None:
        if __name == "data":
            if not isinstance(__value, dict):
                raise TypeError
            for i, j in __value.items():
                if not isinstance(i, str):
                    raise TypeError
                if not isinstance(j, Key):
                    raise TypeError
                if i != j.keyname:
                    raise ValueError
                if j.group is None:
                    j.group = self.groupname
                if j.group != self.groupname:
                    raise ValueError
        elif __name == "groupname":
            if not isinstance(__value, str):
                raise TypeError
        elif __name == f"_{self.__class__.__name__}__deleted":
            if not isinstance(__value, bool):
                raise TypeError
        else:
            raise AttributeError
        return super().__setattr__(__name, __value)

    def __init__(self, groupname: str, *keys: Key) -> None:
        self.data: Dict[str, Key] = {}
        for i in keys:
            if isinstance(i, Key):
                if i.group is None:
                    i.group = self.groupname
                if i.group != self.groupname:
                    continue
                if i.valid:
                    pass
                elif i.keyname not in self.data:
                    pass
                elif self.data[i.keyname].valid:
                    continue
                self.data[i.keyname] = i
        if not isinstance(groupname, str):
            raise TypeError
        self.groupname: str = groupname
        self.__deleted: bool = False

    def __setitem__(self, __key: str, __item: Key) -> None:
        if not isinstance(__key, str):
            raise TypeError
        if not isinstance(__item, Key):
            raise TypeError
        if __key != __item.keyname:
            raise ValueError
        if __item.group is None:
            __item.group = self.groupname
        if __item.group != self.groupname:
            raise ValueError
        if __item.valid:
            pass
        elif __key not in self.data:
            pass
        elif self.data[__key].valid:
            return
        return super().__setitem__(__key, __item)

    @property
    def valid(self) -> bool:
        return not self.__deleted

    @property
    def valid_keys(self) -> List[Key]:
        list_: List[Key] = []
        for i in self.data.values():
            if i.valid:
                insort(list_, i)
        return list_

    def delete(self) -> "Group":
        self.__deleted = True
        return self

    def recover(self) -> "Group":
        self.__deleted = False
        return self

    def outcast(self) -> List[Key]:
        list_: List[Key] = []
        for _keyname, _key in deepcopy(self.data).items():
            if _key.group is None:
                _key.group = self.groupname
                continue
            if _key.group != self.groupname:
                list_.append(self.data.pop(_keyname))
        return list_

    def aspair(self, valid_only: bool = True) -> Optional[Pair]:
        if self.__deleted and valid_only:
            return None
        else:
            dict_ = {}
            keylist: List[Key] = []
            for _key in self.data.values():
                insort(keylist, _key)
            for _key in keylist:
                _pair = _key.aspair(valid_only)
                if _pair is not None:
                    dict_[_pair.key] = _pair.value
            return Pair(self.groupname, dict_)

    export: Callable = aspair

    def __repr__(self) -> str:
        if self.__deleted:
            return f"{self.groupname}(__deleted__)"
        else:
            _tab, _sep = "\n\t", ",\n\t"
            valid_keys = self.valid_keys
            if len(valid_keys) <= 4:
                repr_ = (
                    f"{self.groupname}("
                    f"{_tab}"
                    f"{_sep.join(_indent(repr(i)) for i in valid_keys)}\n)"
                )
            else:
                repr_ = (
                    f"{self.groupname}("
                    f"{_tab}{_indent(repr(valid_keys[0]))}"
                    f"{_sep}{_indent(repr(valid_keys[1]))}"
                    f"{_sep}..."
                    f"{_sep}{_indent(repr(valid_keys[-1]))}\n)"
                )
            return repr_


class _BaseKeyChain(UserDict):
    """
    Filter arguments but not raise exception when initiate.

    Warning:
        - attribute 'data' of '_BaseKeyChain' instance is not recommended to
          access from outer scope.
    """
    def __setattr__(self, __name: str, __value: Any) -> None:
        if __name == "data":
            if not isinstance(__value, dict):
                raise TypeError
            for i, j in __value.items():
                if not isinstance(i, str):
                    raise TypeError
                if not isinstance(j, Group):
                    raise TypeError
                if i != j.groupname:
                    raise ValueError
        return super().__setattr__(__name, __value)

    def __init__(self, *groups: Union[str, Group]) -> None:
        self.data: Dict[str, Group] = {}
        for i in groups:
            if isinstance(i, str):
                self.data[i] = Group(i)
            elif isinstance(i, Group):
                if i.valid:
                    pass
                elif i.groupname not in self.data:
                    pass
                elif self.data[i.groupname].valid:
                    continue
                self.data[i.groupname] = i

    def __setitem__(self, __key: str, __item: Group) -> None:
        if not isinstance(__key, str):
            raise TypeError
        if not isinstance(__item, Group):
            raise TypeError
        if __key != __item.groupname:
            raise ValueError
        if __item.valid:
            pass
        elif __key not in self.data:
            pass
        elif self.data[__key].valid:
            return
        return super().__setitem__(__key, __item)

    @property
    def valid_groups(self) -> List[Group]:
        list_: List[Group] = []
        for _group in self.data.values():
            if _group.valid:
                insort(list_, _group)
        return list_

    def regrouping(self) -> "_BaseKeyChain":
        outcasts: List[Key] = []
        for _group in self.data.values():
            outcasts.extend(_group.outcast())
        for _key in outcasts:
            if _key.group is not None:  # Of no use but a type hint for 'mypy'.
                if _key.group in self.data:
                    self.data[_key.group][_key.keyname] = _key
                else:
                    self.data[_key.group] = Group(_key.group, _key)
        return self

    def get_key(
        self,
        pattern: str,
        *,
        keyname_only: bool = True,
        regex_on: bool = False,
        fullmatch: bool = False
    ) -> List[Key]:
        """
        Argument 'pattern' should be r-string.
        """
        list_: List[Key] = []
        if fullmatch:
            func = re.fullmatch
        else:
            func = re.search
        if not regex_on:
            pattern = re.escape(pattern)
        for _group in self.data.values():
            for i in _group.values():
                _key: Key = i  # Of no use a type hint but for mypy.
                if func(pattern, _key.keyname) is not None:
                    list_.append(_key)
                    continue
                if keyname_only:
                    continue
                if _key.description is not None:
                    if func(pattern, _key.description) is not None:
                        list_.append(_key)
                        continue
                _flag = False
                for _url in _key.url_list:
                    if func(pattern, _url) is not None:
                        list_.append(_key)
                        _flag = True
                        break
                if _flag:
                    continue
                for j in _key.user_dict.values():
                    _user: User = j  # Of no use a type hint but for mypy.
                    if func(pattern, _user.username) is not None:
                        list_.append(_key)
                        break
                    if func(pattern, _user.password) is not None:
                        list_.append(_key)
                        break
                    if _user.notes is not None:
                        if func(pattern, _user.notes) is not None:
                            list_.append(_key)
                            break
        return list_

    @property
    def register(self) -> Counter:
        list_: List[str] = []
        for _group in self.data.values():
            list_.extend(_group)
        return Counter(list_)

    @property
    def doppelganger(self) -> Dict[str, List[Key]]:
        dict_: Dict[str, List[Key]] = {}
        for _keyname, _count in self.register.items():
            if _count > 1:
                dict_[_keyname] = self.get_key(_keyname, keyname_only=True)
        return dict_

    def asdict(self, valid_only: bool = True) -> dict:
        dict_ = {}
        grouplist: List[Group] = []
        for _group in self.data.values():
            insort(grouplist, _group)
        for _group in grouplist:
            _pair = _group.aspair(valid_only)
            if _pair is not None:
                dict_[_pair.key] = _pair.value
        return dict_

    export: Callable = asdict

    def asjson(self, valid_only: bool = True) -> str:
        """
        Should never save a json string before encrypted.
        """
        dict_ = self.asdict(valid_only)
        return json.dumps(dict_ , ensure_ascii=False, indent=4)

    def __repr__(self) -> str:
        _tab, _sep = "\n\t", ",\n\t"
        valid_groups = self.valid_groups
        if len(valid_groups) <= 4:
            repr_ = (
                f"{self.__class__.__name__}("
                f"{_tab}"
                f"{_sep.join(_indent(repr(i)) for i in valid_groups)}\n)"
            )
        else:
            repr_ = (
                f"{self.__class__.__name__}("
                f"{_tab}{_indent(repr(valid_groups[0]))}"
                f"{_sep}{_indent(repr(valid_groups[1]))}"
                f"{_sep}..."
                f"{_sep}{_indent(repr(valid_groups[-1]))}\n)"
            )
        return repr_


class KeyChain(_BaseKeyChain):

    PRIMARY: str = "Primary"
    SECONDARY: str = "Secondary"
    __inst: Optional["KeyChain"] = None

    def __new__(cls, *args, **kwargs) -> "KeyChain":
        if cls.__inst is None:
            cls.__inst = super().__new__(cls)
        return cls.__inst

    def __setattr__(self, __name: str, __value: Any) -> None:
        if __name == "data":
            if not isinstance(__value, dict):
                raise TypeError
            for i, j in __value.items():
                if not isinstance(j, Group):
                    raise TypeError
                if i not in ("Core", "Trivial"):
                    raise ValueError
                if i != j.groupname:
                    raise ValueError
        return super().__setattr__(__name, __value)

    def __init__(
        self,
        primary: Optional[Group] = None,
        secondary: Optional[Group] = None
    ) -> None:
        if self.__class__.__inst is not None:
            return
        self.data: Dict[str, Group] = {}
        PRIMARY: str = self.__class__.PRIMARY
        SECONDARY: str = self.__class__.SECONDARY
        if primary is None:
            self.data[PRIMARY] = Group(PRIMARY)
        elif isinstance(primary, Group):
            primary.groupname = PRIMARY
            for i in primary.values():
                _primary_key: Key = i  # Of no use but a type hint for 'mypy'.
                _primary_key.group = PRIMARY
            self.data[PRIMARY] = primary
        else:
            raise TypeError
        if secondary is None:
            self.data[SECONDARY] = Group(SECONDARY)
        elif isinstance(secondary, Group):
            secondary.groupname = SECONDARY
            for i in secondary.values():
                _secondary_key: Key = i  # Of no use but a type hint for 'mypy'.
                _secondary_key.group = SECONDARY
            self.data[SECONDARY] = secondary
        else:
            raise TypeError
