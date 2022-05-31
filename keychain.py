"""
This module defines 'User', 'Key' 'Group' and "KeyChain'.

Conventions
-----------
valid
    An object is valid if and only if its property 'valid' is True.

    If an object is invalid, it will:
    -   Have lower priority to be kept in a higher-level container.
        In other words, if multiple instances of a class with SAME NAME
        are passed, only the LAST VALID one or the LAST one (if no one is
        valid) will remain.
    -   Not appear in container's string representation.
    -   Not appear in the result of container's 'export' method unless
        explicitly call method with 'valid_only' set to False.

temp_ | list_ | dict_
    Identifiers for temporary variables.
    'list_' means it is a Sequence and molst likely a list.
    'dict_' means it is a Mapping and molst likely a dict.

for-loop variable
    If the type of a for-loop variable is discussed in the loop, this variable
    should be named as 'i', 'j', etc.
    Otherwise, it should be named with a leading '_'.
    Sometimes there may be a confusing statement, for example:
        >   for i in self.values():
        >       _key: Key = i
    This kind of statement is of no use but a hint for 'mypy'.
"""

import csv
import json
import re
from bisect import insort
from collections import Counter, UserDict, UserList
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import *

from .utils import Char, indent, timestamp

NoneType = type(None)

TAB_: str = Char.NEWLINE.value + Char.INDENT.value
SEP_: str = Char.DELIMITER.value + TAB_
TAB__: str = Char.NEWLINE.value + Char.INDENT.value * 2
SEP__: str = Char.DELIMITER.value + TAB__


class Pair(NamedTuple):
    key: Hashable
    value: Any


@dataclass(order=True, repr=False)
class User:

    username: str
    password: str = field(compare=False)
    notes: Optional[str] = field(compare=False)
    timestamp: Union[float, int] = field(compare=False)
    __deleted: bool = field(compare=False)

    def __init__(
        self,
        username: str,
        password: str,
        notes: Optional[str] = None
    ) -> None:
        self.username: str = username
        self.password: str = password
        self.notes: Optional[str] = notes
        self.timestamp: Union[float, int] = timestamp()
        self.__deleted: bool = False

    def __setattr__(
        self,
        __name: str,
        __value: Union[str, float, int, bool, NoneType]
    ) -> None:
        CLASSNAME = self.__class__.__name__
        if __name in ("username", "password"):
            if not isinstance(__value, str):
                raise TypeError
            super().__setattr__("timestamp", timestamp())
        elif __name == "notes":
            if __value is not None and not isinstance(__value, str):
                raise TypeError
        elif __name == "timestamp":
            if not isinstance(__value, (float, int)):
                raise TypeError
        elif __name == f"_{CLASSNAME}__deleted":
            if not isinstance(__value, bool):
                raise TypeError
        else:
            raise AttributeError
        return super().__setattr__(__name, __value)

    @property
    def valid(self) -> bool:
        return not self.__deleted

    def delete(self) -> "User":
        self.__deleted = True
        return self

    def recover(self) -> "User":
        self.__deleted = False
        return self

    def asdict(self, *, valid_only: bool = True) -> Optional[dict]:
        if self.__deleted and valid_only:
            return None
        else:
            dict_ = {
                "username": self.username,
                "password": self.password,
                "notes": self.notes,
                "timestamp": self.timestamp
            }
            return dict_

    export: Callable = asdict

    def __repr__(self) -> str:
        CLASSNAME = self.__class__.__name__
        if self.__deleted:
            return f"{CLASSNAME}(__deleted__)"
        else:
            repr_ = (
                f"{CLASSNAME}("
                f"{TAB_}username: '{self.username}'"
                f"{SEP_}password: '{self.password}'"
                f"{SEP_}timestamp: {self.timestamp}\n)"
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
    def __init__(self, *urls: str) -> None:
        self.data: List[str] = []
        for i in urls:
            if isinstance(i, str):
                insort(self.data, i.rstrip("/"))

    def __setattr__(self, __name: str, __value: List[str]) -> None:
        if __name == "data":
            list_: List[str] = []
            if not isinstance(__value, list):
                raise TypeError
            for i in __value:
                if not isinstance(i, str):
                    raise TypeError
                insort(list_, i.rstrip("/"))
        else:
            raise AttributeError
        return super().__setattr__(__name, list_)

    def insort(self, url: str) -> None:
        if isinstance(url, str) and url not in self:
            insort(self.data, url.rstrip("/"))

    insert: Callable = insort

    def append(self, url: str) -> None:
        """Drprecated."""
        if not isinstance(url, str):
            raise TypeError
        url = url.rstrip("/")
        return super().append(url)

    def extend(self, other: Iterable[str]) -> None:
        """Drprecated."""
        list_: List[str] = []
        for i in other:
            if not isinstance(i, str):
                raise ValueError
            list_.append(i.rstrip("/"))
        return super().extend(list_)


class _UserDict(UserDict):
    """
    Filter arguments but not raise exception when initiate.

    Warning:
        - attribute 'data' of '_UserDict' instance is not recommended to
          access from outer scope.
    """
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

    def __init__(
        self,
        keyname: str,
        user: Optional[User] = None,
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
        if user is not None:
            list_.append(user)
        if user_list is not None:
            list_.extend(user_list)
        self.user_dict: _UserDict = _UserDict(*list_)
        self.__deleted: bool = False

    def __setattr__(
        self,
        __name: str,
        __value: Union[str, _URLList, _UserDict, bool, NoneType]
    ) -> None:
        CLASSNAME = self.__class__.__name__
        if __name == "keyname":
            if not isinstance(__value, str):
                raise TypeError
        elif __name in ("group", "description"):
            if __value is not None and not isinstance(__value, str):
                raise TypeError
        elif __name == "url_list":
            if not isinstance(__value, _URLList):
                raise TypeError
        elif __name == "user_dict":
            if not isinstance(__value, _UserDict):
                raise TypeError
        elif __name == f"_{CLASSNAME}__deleted":
            if not isinstance(__value, bool):
                raise TypeError
        else:
            raise AttributeError
        return super().__setattr__(__name, __value)

    @property
    def valid(self) -> bool:
        return not self.__deleted

    @property
    def valid_users(self) -> List[User]:
        list_: List[User] = []
        for i in self.user_dict.values():
            _user: User = i
            if _user.valid:
                insort(list_, _user)
        return list_

    def add_user(self, *users: User) -> "Key":
        for _user in users:
            self.user_dict[_user.username] = _user
        return self

    def sort(self) -> None:
        self.url_list.sort()

    def delete(self) -> "Key":
        self.__deleted = True
        return self

    def recover(self) -> "Key":
        self.__deleted = False
        return self

    def aspair(self, *, valid_only: bool = True) -> Optional[Pair]:
        if self.__deleted and valid_only:
            return None
        else:
            self.sort()
            list_: List[dict] = []
            for i in self.user_dict.values():
                _user: User = i
                _export = _user.asdict(valid_only=valid_only)
                if _export is not None:
                    insort(list_, _export)
            dict_ = {
                "description": self.description,
                "url": [*self.url_list],
                "userlist": list_
            }
            return Pair(self.keyname, dict_)

    export: Callable = aspair

    def __repr__(self) -> str:
        CLASSNAME = self.__class__.__name__
        if self.__deleted:
            return f"{CLASSNAME}(__deleted__)"
        else:
            valid_users = self.valid_users
            if not valid_users:
                repr_ = (
                    f"{CLASSNAME}("
                    f"{TAB_}keyname: '{self.keyname}'"
                    f"{SEP_}userlist: []\n)"
                )
            elif len(valid_users) <= 4:
                repr_ = (
                    f"{CLASSNAME}("
                    f"{TAB_}keyname: '{self.keyname}'"
                    f"{SEP_}userlist: ["
                    f"{TAB__}"
                    f"{SEP__.join(indent(repr(i), 2) for i in valid_users)}"
                    f"{TAB_}]\n)"
                )
            else:
                repr_ = (
                    f"{CLASSNAME}("
                    f"{TAB_}keyname: '{self.keyname}'"
                    f"{SEP_}userlist: ["
                    f"{TAB__}{indent(repr(valid_users[0]), 2)}"
                    f"{SEP__}{indent(repr(valid_users[1]), 2)}"
                    f"{SEP__}..."
                    f"{SEP__}{indent(repr(valid_users[-1]), 2)}"
                    f"{TAB_}]\n)"
                )
            return repr_


class Group(UserDict):
    """
    Filter arguments but not raise exception when initiate.

    If 'force' is False, only 'Key' instances with attribute 'group'
    being None or equal to 'self.groupname' will be accepted, otherwise
    attribute 'group' of 'Key' instances will be set to 'self.groupname'.

    Warning:
        - attribute 'data' of 'Group' instance is not recommended to
          access from outer scope.
    """
    def __init__(self, groupname: str, *keys: Key, force: bool = False) -> None:
        self.data: Dict[str, Key] = {}
        self.__groupname: str = groupname
        for i in keys:
            if isinstance(i, Key):
                if i.group is None:
                    i.group = self.__groupname
                if i.group != self.__groupname:
                    if force:
                        i.group = self.__groupname
                    else:
                        continue
                if i.valid:
                    pass
                elif i.keyname not in self.data:
                    pass
                elif self.data[i.keyname].valid:
                    continue
                self.data[i.keyname] = i
        self.__deleted: bool = False

    def __setattr__(
        self,
        __name: str,
        __value: Union[Dict[str, Key], str, bool]
    ) -> None:
        CLASSNAME = self.__class__.__name__
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
                    j.group = self.__groupname
                if j.group != self.__groupname:
                    raise ValueError
        elif __name == f"_{CLASSNAME}__groupname":
            if not isinstance(__value, str):
                raise TypeError
        elif __name == f"_{CLASSNAME}__deleted":
            if not isinstance(__value, bool):
                raise TypeError
        else:
            raise AttributeError
        return super().__setattr__(__name, __value)

    def __setitem__(self, __key: str, __item: Key) -> None:
        if not isinstance(__key, str):
            raise TypeError
        if not isinstance(__item, Key):
            raise TypeError
        if __key != __item.keyname:
            raise ValueError
        if __item.group is None:
            __item.group = self.__groupname
        if __item.group != self.__groupname:
            raise ValueError
        if __item.valid:
            pass
        elif __key not in self.data:
            pass
        elif self.data[__key].valid:
            return
        return super().__setitem__(__key, __item)

    def __get_groupname(self):
        return self.__groupname

    def __set_groupname(self, groupname: str):
        self.__groupname = groupname
        for i in self.values():
            _key: Key = i
            _key.group = groupname

    groupname = property(fget=__get_groupname, fset=__set_groupname)

    @property
    def valid(self) -> bool:
        return not self.__deleted

    @property
    def valid_keys(self) -> List[Key]:
        list_: List[Key] = []
        for i in self.values():
            _key: Key = i
            if _key.valid:
                insort(list_, _key)
        return list_

    def add_key(self, *keys: Key, force: bool = False) -> "Group":
        for _key in keys:
            if force:
                _key.group = self.groupname
            self[_key.keyname] = _key
        return self

    def delete(self) -> "Group":
        self.__deleted = True
        return self

    def recover(self) -> "Group":
        self.__deleted = False
        return self

    def outcast(self) -> List[Key]:
        list_: List[Key] = []
        for i, j in deepcopy(self).items():
            _keyname: str = i
            _key: Key = j
            if _key.group is None:
                _key.group = self.__groupname
                continue
            if _key.group != self.__groupname:
                list_.append(self.data.pop(_keyname))
                # 'UserDict' does not have method 'pop'.
        return list_

    def aspair(self, *, valid_only: bool = True) -> Optional[Pair]:
        if self.__deleted and valid_only:
            return None
        else:
            dict_ = {}
            list_: List[Key] = []
            for i in self.values():
                _key: Key = i
                insort(list_, _key)
            for _key in list_:
                _pair = _key.aspair(valid_only=valid_only)
                if _pair is not None:
                    dict_[_pair.key] = _pair.value
            return Pair(self.__groupname, dict_)

    export: Callable = aspair

    def __repr__(self) -> str:
        if self.__deleted:
            return f"{self.groupname}(__deleted__)"
        else:
            valid_keys = self.valid_keys
            if not valid_keys:
                repr_ = (f"{self.groupname}()")
            elif len(valid_keys) <= 4:
                repr_ = (
                    f"{self.groupname}("
                    f"{TAB_}"
                    f"{SEP_.join(indent(repr(i)) for i in valid_keys)}\n)"
                )
            else:
                repr_ = (
                    f"{self.groupname}("
                    f"{TAB_}{indent(repr(valid_keys[0]))}"
                    f"{SEP_}{indent(repr(valid_keys[1]))}"
                    f"{SEP_}..."
                    f"{SEP_}{indent(repr(valid_keys[-1]))}\n)"
                )
            return repr_


class KeyChain(UserDict):
    """
    Filter arguments but not raise exception when initiate.

    Warning:
        - attribute 'data' of 'KeyChain' instance is not recommended to
          access from outer scope.
    """
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

    def __getattribute__(self, __name: str) -> Any:
        if __name in self.data:
            return self.data[__name]
        return super().__getattribute__(__name)

    def __setitem__(self, __key: str, __item: Group) -> None:
        if not isinstance(__key, str):
            raise TypeError
        if not isinstance(__item, Group):
            raise TypeError
        if __item.groupname != __key:
            __item.groupname = __key
        if __item.valid:
            pass
        elif __key not in self.data:
            pass
        elif self.data[__key].valid:
            return
        return super().__setitem__(__key, __item)

    def __getitem__(self, key: str):
        if key in self.data:
            return self.data
        return super().__getitem__(key)

    @property
    def valid_groups(self) -> List[Group]:
        list_: List[Group] = []
        for i in self.values():
            _group: Group = i
            if _group.valid:
                list_.append(_group)
        return list_

    def add_key(self, *keys: Key) -> "KeyChain":
        for _key in keys:
            if _key.group is not None:  # Always True.
                if _key.group in self:
                    self[_key.group][_key.keyname] = _key
                else:
                    self[_key.group] = Group(_key.group, _key)
        return self

    def add_new_key(
        self,
        keyname: str,
        username: str,
        password: str,
        *,
        group: str,
        description: Optional[str] = None,
        url: Optional[str] = None
    ) -> "KeyChain":
        if not isinstance(group, str):
            raise TypeError
        user = User(username, password)
        key = Key(keyname, user, group=group, description=description, url=url)
        return self.add_key(key)

    def get_all_keys(self, *, valid_only: bool = True) -> List[Key]:
        list_: List[Key] = []
        for i in self.values():
            _group: Group = i
            if valid_only and not _group.valid:
                continue
            for i in _group.values():
                _key: Key = i
                if valid_only and not _key.valid:
                    continue
                list_.append(_key)
        return list_

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
        for _key in self.get_all_keys():
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
            for i in _key.user_dict.values():
                _user: User = i
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

    def regrouping(self) -> "KeyChain":
        outcasts: List[Key] = []
        for i in self.values():
            _group: Group = i
            outcasts.extend(_group.outcast())
        return self.add_key(*outcasts)

    @property
    def register(self) -> Counter:
        list_: List[str] = []
        for i in self.values():
            _group: Group = i
            list_.extend(_group)
        return Counter(list_)

    @property
    def doppelganger(self) -> Dict[str, List[Key]]:
        dict_: Dict[str, List[Key]] = {}
        for _keyname, _count in self.register.items():
            if _count > 1:
                dict_[_keyname] = self.get_key(_keyname, keyname_only=True)
        return dict_

    def asdict(self, *, valid_only: bool = True) -> dict:
        dict_ = {}
        grouplist: List[Group] = []
        for i in self.values():
            _group: Group = i
            grouplist.append(_group)
        grouplist.sort(key=lambda x: x.groupname)
        for _group in grouplist:
            _pair = _group.aspair(valid_only=valid_only)
            if _pair is not None:
                dict_[_pair.key] = _pair.value
        return dict_

    export: Callable = asdict

    def dump_csv(
        self,
        path: Union[Path, str],
        *,
        valid_only: bool = True
    ) -> None:
        """
        Only for Google Password Manerger.
        Should delete .csv file immediately after importing to
        Google account.
        """
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(("name", "url", "username", "password"))
            for _key in self.get_all_keys(valid_only=valid_only):
                if _key.url_list[0] is not None:
                    _url = _key.url_list[0]  # Discard the rest.
                else:
                    _url = _key.keyname  # May not be recognized.
                for i in _key.user_dict.values():
                    _user: User = i
                    row = (_key.keyname, _url, _user.username, _user.password)
                    writer.writerow(row)

    @classmethod
    def load_csv(
        cls,
        path: Union[Path, str],
        group: str
    ) -> "KeyChain":
        """
        Only for Google Password Manerger.
        Should delete .csv file immediately after importing.
        """
        dict_: Dict[str, Key] = {}
        with open(path, encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            next(reader)
            for _keyname, _url, _username, _password in reader:
                _user = User(_username, _password)
                if _keyname not in dict_:
                    dict_[_keyname] = Key(_keyname, _user, url=_url)
                else:
                    _key = dict_[_keyname]
                    _key.url_list.insort(_url)
                    _key.add_user(_user)
        return cls(Group(group, *dict_.values()))

    def to_json(self, *, valid_only: bool = True) -> str:
        """
        Should never save a json string before encrypted.
        """
        dict_ = self.asdict(valid_only=valid_only)
        return json.dumps(dict_, ensure_ascii=False, indent=4)

    @classmethod
    def from_json(cls, string_: str) -> "KeyChain":
        keychain_dict: dict = json.loads(string_)
        instance = cls()
        for i, j in keychain_dict.items():
            _groupname: str = i
            _group_dict: dict = j
            _group = Group(_groupname)
            for i, j in _group_dict.items():
                _keyname: str = i
                _key_dict: dict = j
                _key = Key(
                    _keyname,
                    description=_key_dict["description"],
                    url_list=_key_dict["url"],
                )
                for i in _key_dict["userlist"]:
                    _user_dict: dict = i
                    _user = User(
                        _user_dict["username"],
                        _user_dict["password"],
                        _user_dict["notes"]
                    )
                    _user.timestamp = _user_dict["timestamp"]
                    _key.add_user(_user)
                _group.add_key(_key)
            instance[_groupname] = _group
        return instance

    def __repr__(self) -> str:
        CLASSNAME = self.__class__.__name__
        valid_groups = self.valid_groups
        if not valid_groups:
            repr_ = (f"{CLASSNAME}()")
        elif len(valid_groups) <= 4:
            repr_ = (
                f"{CLASSNAME}("
                f"{TAB_}"
                f"{SEP_.join(indent(repr(i)) for i in valid_groups)}\n)"
            )
        else:
            repr_ = (
                f"{CLASSNAME}("
                f"{TAB_}{indent(repr(valid_groups[0]))}"
                f"{SEP_}{indent(repr(valid_groups[1]))}"
                f"{SEP_}..."
                f"{SEP_}{indent(repr(valid_groups[-1]))}\n)"
            )
        return repr_
