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
from typing import Dict, Iterable, List, Optional, Union


@dataclass(order=True, unsafe_hash=True)
class User:
    """
    Will NOT check whether the arguments are valid when initiate.
    """
    username: str
    password: str = field(compare=False)
    notes: List[str] = field(compare=False)

    def __init__(self, username: str, password: str, *notes: str) -> None:
        self.username = username
        self.password = password
        self.notes = [*notes]
        self.__conflict: List[str] = []  # for conflict passwords

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}('{self.username}')"

    @property
    def valid(self) -> bool:
        if all((
            isinstance(self.username, str),
            isinstance(self.password, str),
            isinstance(self.notes, list),
            *(isinstance(i, str) for i in self.notes),
            isinstance(self.__conflict, list),
            *(isinstance(i, str) for i in self.__conflict)
        )):
            return True
        else:
            return False

    def add_note(self, *notes: str) -> "User":
        for note in notes:
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

    @property
    def conflict(self) -> List[str]:
        return self.__conflict

    def add_conflict(self, *passwords: str) -> "User":
        for password in passwords:
            insort(self.__conflict, password)
        return self

    def solve_conflicts(self, index) -> None:
        self.password = self.__conflict[index]
        self.__conflict.clear()

    def asdict(self) -> dict:
        return deepcopy(self.__dict__)


@dataclass(order=True, unsafe_hash=True)
class Key:
    """
    Will NOT check whether the arguments are valid when initiate.
    """
    keyname: str
    description: Optional[str] = field(repr=False, compare=False)
    url_list: List[str] = field(repr=False, compare=False)
    user_list: List[User] = field(compare=False)

    def __init__(
        self,
        keyname: str,
        user: Union[User, Iterable],
        *,
        description: Optional[str] = None,
        url: Optional[str] = None,
        url_list: Optional[List[str]] = None,
        user_list: Optional[List[User]] = None,
    ) -> None:
        self.keyname = keyname
        self.description = description
        self.url_list = []
        self.user_list = []
        if url is not None:
            self.url_list.append(url)
        if url_list is not None:
            self.url_list.extend(url_list)
        if isinstance(user, User):
            self.user_list.append(user)
        else:
            self.user_list.append(User(*user))
        if user_list is not None:
            self.user_list.extend(user_list)
        self.__deleted = False

    @property
    def valid(self) -> bool:
        if all((
            isinstance(self.keyname, str),
            isinstance(self.description, str) or self.description is None,
            isinstance(self.url_list, list),
            isinstance(self.__deleted, bool),
            *(isinstance(i, str) for i in self.url_list),
            *(isinstance(i, User) for i in self.user_list),
        )) and all(i.valid for i in self.user_list):
            return True
        else:
            return False
        # for statement:
        #   'a and b'
        # if
        #   'bool(a) is False'
        # then the statement is equal to 'a' (not 'bool(a)')
        # even if 'b' will raise exception.
        #
        # statement 'all(i.valid for i in self.user_list)'
        # may raise exception if 'i' is not a 'User' instance.

    def sort(self) -> "Key":
        self.url_list.sort()
        self.user_list.sort()
        return self

    def add_url(self, *urls: str) -> "Key":
        for url in urls:
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

    def get_user(
        self,
        pattern: str,
        *,
        username_only: bool = True,
        regex_on: bool = False,
        fullmatch: bool = False
    ) -> List[User]:
        """
        pattern should be r-string.
        """
        result: List[User] = []
        if fullmatch:
            func = re.fullmatch
        else:
            func = re.search
        if not regex_on:
            pattern = re.escape(pattern)
        for user in self.user_list:
            if func(pattern, user.username) is not None:
                result.append(user)
                continue
            if username_only:
                continue
            if func(pattern, user.password) is not None:
                result.append(user)
                continue
            for note in user.notes:
                if func(pattern, note) is not None:
                    result.append(user)
                    break
        return result

    def add_user(self, username: str, password: str, *notes: str) -> "Key":
        user = User(username, password, *notes)
        insort(self.user_list, user)
        return self

    def _merge(self) -> None:
        temp = []
        user_counter = Counter(self.user_list)
        for user in user_counter:
            if user_counter[user] > 1:
                temp.append(user.username)
        for username in temp:
            _users = self.get_user(username, fullmatch=True)
            _kept = _users[0]
            _password_list = []
            _notes = []
            for _user in _users:
                _notes.extend(_user.notes)
                _password_list.append(_user.password)
                self.user_list.remove(_user)
            _password_counter = Counter(_password_list)
            if len(_password_counter) > 1:
                _kept.add_conflict(*_password_counter)
            _kept.notes = list(dict.fromkeys(_notes))
            self.user_list.append(_kept)
            self.user_list.sort()

    def del_user(self, index: int = -1, *, del_all: bool = False) -> "Key":
        if del_all:
            self.user_list.clear()
        try:
            self.user_list.pop(index)
        except IndexError:
            pass
        return self

    def delete(self):
        if not self.__deleted:
            self.__deleted = True
            def recover():
                self.__deleted = False
            return recover

    def _asdict(self) -> dict:
        """
        May raise exception if there is some member in 'self.user_list' that
        is not a 'User' instance.
        """
        dict_ = deepcopy(self.__dict__)
        dict_.pop("keyname")
        dict_["userlist"] = [i.asdict() for i in self.user_list]
        return dict_

    def asdict(self) -> dict:
        return {self.keyname: self._asdict()}


class Group(UserList):

    def __init__(self, groupname: str, *keys: Key) -> None:
        self.groupname = groupname
        super().__init__(keys)
        self.sort()

    def __repr__(self) -> str:
        self.sort()
        sep = ",\n\t"
        if len(self) <= 4:
            repr_ = (
                f"{self.groupname}(\n"
                f"\t{sep.join(repr(i) for i in self)}\n)"
            )
        else:
            repr_ = (
                f"{self.groupname}(\n"
                f"\t{repr(self[0])},\n"
                f"\t{repr(self[1])},\n\t...,\n"
                f"\t{repr(self[-1])}\n)"
            )
        return(repr_)

    @property
    def valid(self) -> bool:
        if all(i.valid for i in self):
            return True
        else:
            return False

    def sort_r(self) -> "Group":
        for key in self:
            key.sort()
        self.sort()
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
        pattern should be r-string.
        """
        result: List[Key] = []
        if fullmatch:
            func = re.fullmatch
        else:
            func = re.search
        if not regex_on:
            pattern = re.escape(pattern)
        for key in self:
            if func(pattern, key.keyname) is not None:
                result.append(key)
                continue
            if keyname_only:
                continue
            if key.description is not None:
                if func(pattern, key.description) is not None:
                    result.append(key)
                    continue
            flag = False
            for url in key.url_list:
                if func(pattern, url) is not None:
                    result.append(key)
                    flag = True
                    break
            if flag:
                continue
            for user in key.user_list:
                if func(pattern, user.username) is not None:
                    result.append(key)
                    break
                if func(pattern, user.password) is not None:
                    result.append(key)
                    break
                for note in user.notes:
                    if func(pattern, note) is not None:
                        result.append(key)
                        break
        return result

    def add_key(self, *keys: Key) -> "Group":
        for key in keys:
            insort(self, key)
        return self

    def _merge(self) -> None:
        temp = []
        counter = Counter(self)
        for key in counter:
            if counter[key] > 1:
                temp.append(key.keyname)
        for keyname in temp:
            _keys = self.get_key(keyname, fullmatch=True)
            _kept = _keys[0]
            _url_list = []
            _user_list = []
            for _key in _keys:
                _url_list.extend(_key.url_list)
                _user_list.extend(_key.user_list)
                self.remove(_key)
            _kept.url_list = list(dict.fromkeys(_url_list))
            _kept.user_list = list(dict.fromkeys(_user_list))
            _kept._merge()
            self.add_key(_kept)

    def del_key(self, keyname: str, *, hard: bool = False):
        self._merge()
        temp = self.get_key(keyname, fullmatch=True)
        if hard:
            for key in temp:
                self.remove(key)
        else:
            for key in temp:
                key.delete()

    def aslist(self):
        return deepcopy([*self])


class _BaseKeyChain(UserDict):

    def __init__(self, *groups: Group) -> None:
        temp: Dict[str, Group] = {}
        for index, group in enumerate(groups):
            if isinstance(group, Group):
                if not group.valid:
                    raise ValueError(
                        f"invalid 'Group' instance in position {index}"
                    )
            else:
                raise TypeError(
                    f"argument in position {index} is not a 'Group' instance"
                )
            temp[group.groupname] = group
        super().__init__(temp)

    def __repr__(self) -> str:
        repr_list: List(str) = []
        self.sort_r()
        for group in self.keys():
            repr_list.append(repr(group))


    def sort_r(self) -> "_BaseKeyChain":
        for group in self.keys():
            group.sort_r()
        return self

    def asdict(self) -> dict:
        dict_: Dict[str, list]= {}
        self.sort_r()
        for groupname, group in self.items():
            dict_[groupname] = group.aslist()
        return dict_
