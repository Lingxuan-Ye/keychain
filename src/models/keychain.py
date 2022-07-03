import csv
import json
import re
from bisect import insort
from collections import Counter, UserDict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from ..utils import SEP_, TAB_, indent
from .group import Group
from .key import Key
from .user import User


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
            if isinstance(i, str) and i not in self.data:
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

    def __getitem__(self, key: str) -> Group:
        return super().__getitem__(key)

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

    @property
    def valid_groups(self) -> List[Group]:
        list_: List[Group] = []
        for _group in self.data.values():
            if _group.valid:
                insort(list_, _group)
        return list_

    def add_key(self, *keys: Key) -> "KeyChain":
        for _key in keys:
            if _key.group is None:
                _key.group = "Default"
            if _key.group in self:
                self.data[_key.group][_key.keyname] = _key
            else:
                self.data[_key.group] = Group(_key.group, _key)
        return self

    def add_new_key(
        self,
        keyname: str,
        username: str,
        password: str,
        *,
        group: str = "Default",
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
        for _group in self.data.values():
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
        fullmatch: bool = False,
        valid_only: bool = True
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
        for _key in self.get_all_keys(valid_only=valid_only):
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
        for _group in self.data.values():
            outcasts.extend(_group.outcast())
        return self.add_key(*outcasts)

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

    def asdict(self, *, valid_only: bool = True) -> dict:
        dict_ = {}
        list_: List[Group] = []
        for _group in self.data.values():
            insort(list_, _group)
        for _group in list_:
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
        *,
        group: str = "Default"
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
            instance.data[_groupname] = _group
        return instance

    def __repr__(self) -> str:
        CLASSNAME = self.__class__.__name__
        valid_groups = self.valid_groups
        if not valid_groups:
            repr_ = (f"{CLASSNAME}(__empty__)")
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
