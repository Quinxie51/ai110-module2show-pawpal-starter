from dataclasses import dataclass, field
from enum import Enum


class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class Pet:
    name: str
    species: str
    special_needs: list[str] = field(default_factory=list)

    def get_species(self) -> str:
        pass


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: Priority

    def is_high_priority(self) -> bool:
        pass


@dataclass
class Owner:
    name: str
    available_minutes: int = 120
    preferences: dict = field(default_factory=dict)
    _tasks: list[Task] = field(default_factory=list, repr=False)

    def add_task(self, task: Task) -> None:
        pass

    def get_tasks(self) -> list[Task]:
        pass


@dataclass
class DailyPlan:
    scheduled_tasks: list[Task] = field(default_factory=list)
    skipped_tasks: list[Task] = field(default_factory=list)
    explanations: dict[str, str] = field(default_factory=dict)

    def total_duration(self) -> int:
        pass

    def summary(self) -> str:
        pass

    def explain(self, task: Task) -> str:
        pass


class Scheduler:
    def __init__(self, owner: Owner, pet: Pet, tasks: list[Task]):
        self.owner = owner
        self.pet = pet
        self.tasks = tasks

    def build_plan(self) -> DailyPlan:
        pass

    def _sort_by_priority(self) -> list[Task]:
        pass

    def _fits_in_time(self, task: Task, used_minutes: int) -> bool:
        pass
