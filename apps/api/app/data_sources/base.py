from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any


class DataSource(ABC):
    source_name: str

    @abstractmethod
    def rows(self) -> Iterable[dict[str, Any]]:
        raise NotImplementedError

