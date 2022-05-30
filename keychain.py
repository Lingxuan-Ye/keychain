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
"""

import json
import re
from bisect import insort
from collections import Counter, UserDict, UserList
from copy import deepcopy
from dataclasses import dataclass, field
from typing import *

from .utils import Char, indent, timestamp

NoneType = type(None)

TAB_: str = Char.NEWLINE.value + Char.INDENT.value
SEP_: str = Char.DELIMITER.value + TAB_
TAB__: str = Char.NEWLINE.value + Char.INDENT.value * 2
SEP__: str = Char.DELIMITER.value + TAB__

PRIMARY = "Primary"
SECONDARY = "Secondary"


class Pair(NamedTuple):
    key: Hashable
    value: Any


@dataclass(order=True, repr=False)
class User:

    username: str
    password: str = field(compare=False)
    notes: Optional[str] = field(compare=False)
    __timestamp: Union[float, int] = field(compare=False)
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
        self.__timestamp: Union[float, int] = timestamp()
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
            super().__setattr__(f"_{CLASSNAME}__timestamp", timestamp())
        elif __name == "notes":
            if __value is not None and not isinstance(__value, str):
                raise TypeError
        elif __name == f"_{CLASSNAME}__timestamp":
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

    @property
    def timestamp(self) -> Union[float, int]:
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
        CLASSNAME = self.__class__.__name__
        if self.__deleted:
            return f"{CLASSNAME}(__deleted__)"
        else:
            repr_ = (
                f"{CLASSNAME}("
                f"{TAB_}username: '{self.username}'"
                f"{SEP_}password: '{self.password}'"
                f"{SEP_}timestamp: {self.__timestamp}\n)"
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
        if isinstance(url, str):
            insort(self.data, url.rstrip("/"))

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

    insert: Callable = insort


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
            list_: List[dict] = []
            for i in self.user_dict.values():
                _user: User = i  # Of no use but a type hint for 'mypy'.
                _export = _user.asdict(valid_only)
                if _export is not None:
                    insort(list_, _export)
            dict_ = {
                "description": self.description,
                "url": deepcopy(self.url_list),
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

    Only 'Key' instances with attribute 'group' being None or
    equal to 'self.groupname' will be accepted.

    Warning:
        - attribute 'data' of 'Group' instance is not recommended to
          access from outer scope.
    """
    def __init__(self, groupname: str, *keys: Key) -> None:
        self.data: Dict[str, Key] = {}
        self.groupname: str = groupname
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
                    j.group = self.groupname
                if j.group != self.groupname:
                    raise ValueError
        elif __name == "groupname":
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
            list_: List[Key] = []
            for _key in self.data.values():
                insort(list_, _key)
            for _key in list_:
                _pair = _key.aspair(valid_only)
                if _pair is not None:
                    dict_[_pair.key] = _pair.value
            return Pair(self.groupname, dict_)

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


class _BaseKeyChain(UserDict):
    """
    Filter arguments but not raise exception when initiate.

    Warning:
        - attribute 'data' of '_BaseKeyChain' instance is not recommended to
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
        if not isinstance(__name, str):
            raise TypeError
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
                list_.append(_group)
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

    def add_key(
        self,
        keyname: str,
        username: str,
        password: str,
        *,
        group: str,
        description: Optional[str] = None,
        url: Optional[str] = None
    ) -> "_BaseKeyChain":
        if not isinstance(group, str):
            raise TypeError
        user = User(username, password)
        key = Key(keyname, user, group=group, description=description, url=url)
        if group in self.data:
            self.data[group][keyname] = key
        else:
            self.data[group] = Group(group, key)
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
        return json.dumps(dict_, ensure_ascii=False, indent=4)

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


class KeyChain(_BaseKeyChain):

    __inst: Optional["KeyChain"] = None

    def __new__(cls, *args, **kwargs) -> "KeyChain":
        if cls.__inst is None:
            cls.__inst = super().__new__(cls)
        return cls.__inst

    def __init__(
        self,
        *,
        primary: Optional[Group] = None,
        secondary: Optional[Group] = None
    ) -> None:
        groups: List[Union[str, Group]] = []
        if primary is None:
            groups.append(PRIMARY)
        elif isinstance(primary, Group):
            primary.groupname = PRIMARY
            for i in primary.values():
                _primary_key: Key = i  # Of no use but a type hint for 'mypy'.
                _primary_key.group = PRIMARY
            groups.append(primary)
        else:
            raise TypeError
        if secondary is None:
            groups.append(SECONDARY)
        elif isinstance(secondary, Group):
            secondary.groupname = SECONDARY
            for i in secondary.values():
                _secondary_key: Key = i  # Of no use but a type hint for 'mypy'.
                _secondary_key.group = SECONDARY
            groups.append(secondary)
        else:
            raise TypeError
        super().__init__(*groups)

    def __setattr__(self, __name: str, __value: Any) -> None:
        if __name == "data":
            for i in __value:
                if i not in (PRIMARY, SECONDARY):
                    raise ValueError
        else:
            raise AttributeError
        return super().__setattr__(__name, __value)

    @property
    def primary(self):
        return self.data[PRIMARY]

    @property
    def secondary(self):
        return self.data[SECONDARY]

    def add_key(
        self,
        keyname: str,
        username: str,
        password: str,
        *,
        group: Union[str, int, NoneType] = None,
        description: Optional[str] = None,
        url: Optional[str] = None
    ) -> "KeyChain":
        if group is None:
            group = SECONDARY
        elif isinstance(group, int):
            group = PRIMARY if group == 0 else SECONDARY
        elif isinstance(group, str):
            group = group.capitalize()
        if group not in (PRIMARY, SECONDARY):
            raise ValueError
        super().add_key(
            keyname,
            username,
            password,
            group=group,
            description=description,
            url=url
        )
        return self
