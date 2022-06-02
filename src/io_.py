from enum import Enum
from hashlib import sha256
from pathlib import Path
from typing import Union

from .model import KeyChain

try:
    from random import randbytes
    from random import seed as set_seed
except ImportError:
    from random import Random

    class _Random(Random):

        def randbytes(self, n: int) -> bytes:
            return self.getrandbits(n * 8).to_bytes(n, "little")

    _inst = _Random()
    randbytes = _inst.randbytes
    set_seed = _inst.seed


class Status(Enum):

    FORMAT_ERROR = "error: unknown format."
    PASSWORD_ERROR = "error: incorrect username or password."


class IO:

    def __init__(
        self,
        path: Union[Path, str],
        username: str,
        password: str
    ) -> None:
        self.path = path if isinstance(path, Path) else Path(path)
        self.seed = username + password

    def __setattr__(self, __name: str, __value: Union[Path, str]) -> None:
        if __name == "path":
            if isinstance(__value, str):
                __value = Path(__value)
            elif not isinstance(__value, Path):
                raise TypeError
            if not __value.is_file():
                __value = __value / ".keychain"
        if __name == "seed":
            if not isinstance(__value, str):
                raise TypeError
        return super().__setattr__(__name, __value)

    def read(self) -> Union[Status, KeyChain]:
        with open(self.path, "rb") as f:
            lines = f.readlines()
        format = lines[0].strip().upper()
        if format != b"KEYCHAIN":
            return Status.FORMAT_ERROR
        seed_digest = lines[1].strip().decode("utf-8")
        if seed_digest != sha256(self.seed.encode("utf-8")).hexdigest():
            return Status.PASSWORD_ERROR
        raw = b"".join(lines[2:])[:-1]
        length = len(raw)
        set_seed(self.seed, version=2)
        key = randbytes(length)
        xor = int.from_bytes(raw, "big") ^ int.from_bytes(key, "big")
        decrypted = xor.to_bytes(length, "big")
        return KeyChain.from_json(decrypted.decode("utf-8"))

    def write(self, keychain: KeyChain) -> None:
        raw = keychain.to_json().encode("utf-8")
        length = len(raw)
        set_seed(self.seed, version=2)
        key = randbytes(length)
        xor = int.from_bytes(raw, "big") ^ int.from_bytes(key, "big")
        encrypted = xor.to_bytes(length, "big")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "wb") as f:
            seed_digest = sha256(self.seed.encode("utf-8")).hexdigest()
            f.write(b"KEYCHAIN\n")
            f.write(seed_digest.encode("utf-8") + b"\n")
            f.write(encrypted + b"\n")
