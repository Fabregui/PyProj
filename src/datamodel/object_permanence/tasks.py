from dataclasses import dataclass, field
from itertools import count
from typing import List, Optional, Dict, Any


class TechnicalIdGen:
    counter = count()

    @staticmethod
    def reset_to(num: int):
        TechnicalIdGen.counter = count(num)

    @staticmethod
    def set_minimum(num: int):
        current = next(TechnicalIdGen.counter)
        TechnicalIdGen.reset_to(max(current, num))

    @staticmethod
    def next_num():
        return next(TechnicalIdGen.counter)


class OnlyOneParent(Exception):
    pass


class NoChildOfItself(Exception):
    pass


@dataclass
class Task:
    name: str
    children: List[int] = field(default_factory=list)
    parent: Optional[int] = None
    technical_id: int = field(default_factory=TechnicalIdGen.next_num)

    def __post_init__(self):
        ID_TO_RESOURCE[self.technical_id] = self

    def serialize(self) -> Dict[str, Any]:
        return vars(self)

    @classmethod
    def deserialize(cls, dct: Dict[str, Any]) -> "Task":
        TechnicalIdGen.set_minimum(dct["technical_id"] + 1)
        return cls(**dct)

    def children_of(self, other_task: "Task") -> None:
        if self.parent is not None:
            raise OnlyOneParent("dummy")
        if self is other_task:
            raise NoChildOfItself("baka")
        self.parent = other_task.technical_id
        other_task.children.append(self.technical_id)

    def remove_child(self, other_task: "Task") -> None:
        self.children.remove(other_task.technical_id)
        other_task.parent = None

    def parent_of(self, other_task: "Task") -> None:
        other_task.children_of(self)

    def remove_parent(self, other_task: "Task"):
        other_task.remove_child(self)


ID_TO_RESOURCE: Dict[int, Task] = {}
