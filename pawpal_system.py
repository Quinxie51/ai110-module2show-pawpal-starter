from dataclasses import dataclass, field
from enum import Enum


class Priority(Enum):
    """Priority levels for pet care tasks."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


_PRIORITY_ORDER = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}


@dataclass
class Task:
    """A single pet care activity with a description, duration, priority, and completion status."""

    title: str
    duration_minutes: int
    priority: Priority
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def is_high_priority(self) -> bool:
        """Return True if the task priority is HIGH."""
        return self.priority == Priority.HIGH

    def __str__(self) -> str:
        """Return a readable one-line summary of the task."""
        status = "done" if self.completed else "todo"
        return f"[{status}] {self.title} ({self.duration_minutes} min, {self.priority.value})"


@dataclass
class Pet:
    """A pet with a name, species, and list of care tasks."""

    name: str
    species: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet."""
        self.tasks.append(task)

    def get_tasks(self) -> list[Task]:
        """Return all tasks assigned to this pet."""
        return self.tasks

    def __str__(self) -> str:
        """Return a readable summary of the pet."""
        return f"{self.name} ({self.species})"


@dataclass
class Owner:
    """A pet owner who manages one or more pets."""

    name: str
    available_minutes: int = 120
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's care."""
        self.pets.append(pet)

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return all (pet, task) pairs across every pet this owner manages."""
        return [(pet, task) for pet in self.pets for task in pet.get_tasks()]


class Scheduler:
    """Retrieves, organizes, and manages tasks across all of an owner's pets."""

    def __init__(self, owner: Owner):
        """Initialize the scheduler with a given owner."""
        self.owner = owner

    def _all_tasks_sorted(self) -> list[tuple[Pet, Task]]:
        """Return all (pet, task) pairs sorted HIGH → MEDIUM → LOW, then by duration."""
        pairs = self.owner.get_all_tasks()
        return sorted(pairs, key=lambda pt: (_PRIORITY_ORDER[pt[1].priority], pt[1].duration_minutes))

    def build_schedule(self) -> list[tuple[Pet, Task]]:
        """
        Build a greedy daily schedule that fits within the owner's available time.

        Tasks are selected in priority order (HIGH first). Tasks that exceed the
        remaining time budget are skipped. Already-completed tasks are excluded.
        """
        budget = self.owner.available_minutes
        scheduled = []
        for pet, task in self._all_tasks_sorted():
            if task.completed:
                continue
            if task.duration_minutes <= budget:
                scheduled.append((pet, task))
                budget -= task.duration_minutes
        return scheduled

    def print_schedule(self) -> None:
        """Print today's schedule to the terminal in a readable format."""
        schedule = self.build_schedule()
        total = sum(t.duration_minutes for _, t in schedule)

        print(f"\n{'='*44}")
        print(f"  Today's Schedule for {self.owner.name}")
        print(f"  Available time: {self.owner.available_minutes} min  |  Scheduled: {total} min")
        print(f"{'='*44}")

        if not schedule:
            print("  No tasks to schedule.")
        else:
            for i, (pet, task) in enumerate(schedule, 1):
                print(f"  {i}. [{pet.name}] {task}")

        print(f"{'='*44}\n")
