from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class Priority(Enum):
    """Priority levels for pet care tasks."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Frequency(Enum):
    """How often a task repeats."""
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"


_PRIORITY_ORDER = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}
_FREQ_DAYS = {Frequency.DAILY: 1, Frequency.WEEKLY: 7}


def _parse_time(t: str) -> datetime:
    """Parse a 'HH:MM' string into a datetime for comparison."""
    return datetime.strptime(t, "%H:%M")


@dataclass
class Task:
    """A single pet care activity.

    Attributes:
        title:            Short description of the activity.
        duration_minutes: How long the task takes.
        priority:         Scheduling priority (HIGH > MEDIUM > LOW).
        start_time:       Optional wall-clock start in 'HH:MM' format.
        frequency:        ONCE, DAILY, or WEEKLY.
        completed:        True once mark_complete() has been called.
    """

    title: str
    duration_minutes: int
    priority: Priority
    start_time: str | None = None    # "HH:MM"
    frequency: Frequency = Frequency.ONCE
    completed: bool = False

    def mark_complete(self) -> Task | None:
        """Mark this task done and return the next occurrence for recurring tasks.

        Returns a fresh Task scheduled for tomorrow (DAILY) or next week
        (WEEKLY). Returns None for one-off tasks.
        """
        self.completed = True
        if self.frequency in _FREQ_DAYS:
            next_time = self.start_time
            if next_time:
                delta = timedelta(days=_FREQ_DAYS[self.frequency])
                next_dt = _parse_time(next_time) + delta
                next_time = next_dt.strftime("%H:%M")
            return Task(
                title=self.title,
                duration_minutes=self.duration_minutes,
                priority=self.priority,
                start_time=next_time,
                frequency=self.frequency,
            )
        return None

    def is_high_priority(self) -> bool:
        """Return True when priority is HIGH."""
        return self.priority == Priority.HIGH

    def __str__(self) -> str:
        """One-line human-readable summary."""
        status = "done" if self.completed else "todo"
        time_tag = f" @ {self.start_time}" if self.start_time else ""
        freq_tag = f" [{self.frequency.value}]" if self.frequency != Frequency.ONCE else ""
        return (
            f"[{status}] {self.title}{time_tag}"
            f" ({self.duration_minutes} min, {self.priority.value}){freq_tag}"
        )


@dataclass
class Pet:
    """A pet with a name, species, and list of care tasks."""

    name: str
    species: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Append a care task to this pet's list."""
        self.tasks.append(task)

    def get_tasks(self) -> list[Task]:
        """Return all tasks assigned to this pet."""
        return self.tasks

    def __str__(self) -> str:
        """Short label for display."""
        return f"{self.name} ({self.species})"


@dataclass
class Owner:
    """A pet owner who manages one or more pets."""

    name: str
    available_minutes: int = 120
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a new pet under this owner."""
        self.pets.append(pet)

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return every (pet, task) pair across all owned pets."""
        return [(pet, task) for pet in self.pets for task in pet.get_tasks()]


class Scheduler:
    """Retrieves, organises, and manages tasks across all of an owner's pets."""

    def __init__(self, owner: Owner) -> None:
        """Initialise the scheduler with a given owner."""
        self.owner = owner

    # ------------------------------------------------------------------
    # Core scheduling
    # ------------------------------------------------------------------

    def build_schedule(self) -> list[tuple[Pet, Task]]:
        """Build a greedy daily schedule ordered by priority within the time budget.

        Skips already-completed tasks and tasks that would exceed the remaining
        available time.
        """
        budget = self.owner.available_minutes
        scheduled: list[tuple[Pet, Task]] = []
        for pet, task in self._all_tasks_by_priority():
            if task.completed:
                continue
            if task.duration_minutes <= budget:
                scheduled.append((pet, task))
                budget -= task.duration_minutes
        return scheduled

    # ------------------------------------------------------------------
    # Sorting
    # ------------------------------------------------------------------

    def sort_by_time(
        self, pairs: list[tuple[Pet, Task]]
    ) -> list[tuple[Pet, Task]]:
        """Sort (pet, task) pairs by start_time ascending; untimed tasks go last.

        Uses a lambda with datetime.strptime so that string comparison does not
        give wrong results (e.g. '9:00' > '10:00' lexicographically).
        """
        return sorted(
            pairs,
            key=lambda pt: (
                _parse_time(pt[1].start_time)
                if pt[1].start_time
                else datetime.max
            ),
        )

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    def filter_tasks(
        self,
        *,
        pet_name: str | None = None,
        completed: bool | None = None,
    ) -> list[tuple[Pet, Task]]:
        """Filter all tasks by pet name and/or completion status.

        Args:
            pet_name:  Keep only tasks belonging to this pet (exact match).
            completed: Keep only tasks matching this completion flag.
        Returns:
            Filtered list of (pet, task) pairs.
        """
        pairs = self.owner.get_all_tasks()
        if pet_name is not None:
            pairs = [(p, t) for p, t in pairs if p.name == pet_name]
        if completed is not None:
            pairs = [(p, t) for p, t in pairs if t.completed == completed]
        return pairs

    # ------------------------------------------------------------------
    # Conflict detection
    # ------------------------------------------------------------------

    def detect_conflicts(self) -> list[str]:
        """Return warning messages for every pair of overlapping timed tasks.

        Two tasks conflict when their time windows intersect:
            start_A < end_B  AND  start_B < end_A

        Only tasks with an explicit start_time are checked; untimed tasks are
        ignored to avoid false positives. Returns an empty list when no
        conflicts exist.
        """
        timed = [
            (p, t)
            for p, t in self.owner.get_all_tasks()
            if t.start_time and not t.completed
        ]
        warnings: list[str] = []
        for i in range(len(timed)):
            for j in range(i + 1, len(timed)):
                pa, ta = timed[i]
                pb, tb = timed[j]
                a_start = _parse_time(ta.start_time)  # type: ignore[arg-type]
                a_end = a_start + timedelta(minutes=ta.duration_minutes)
                b_start = _parse_time(tb.start_time)  # type: ignore[arg-type]
                b_end = b_start + timedelta(minutes=tb.duration_minutes)
                if a_start < b_end and b_start < a_end:
                    warnings.append(
                        f"WARNING: [{pa.name}] '{ta.title}' "
                        f"({ta.start_time}, {ta.duration_minutes} min) "
                        f"overlaps with [{pb.name}] '{tb.title}' "
                        f"({tb.start_time}, {tb.duration_minutes} min)"
                    )
        return warnings

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def print_schedule(self) -> None:
        """Print a formatted today's schedule to the terminal."""
        schedule = self.sort_by_time(self.build_schedule())
        total = sum(t.duration_minutes for _, t in schedule)

        print(f"\n{'='*50}")
        print(f"  Today's Schedule for {self.owner.name}")
        print(f"  Budget: {self.owner.available_minutes} min  |  Scheduled: {total} min")
        print(f"{'='*50}")
        if not schedule:
            print("  No tasks to schedule.")
        else:
            for i, (pet, task) in enumerate(schedule, 1):
                print(f"  {i}. [{pet.name}] {task}")
        print(f"{'='*50}\n")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _all_tasks_by_priority(self) -> list[tuple[Pet, Task]]:
        """Return all (pet, task) pairs sorted HIGH > MEDIUM > LOW, then by duration."""
        return sorted(
            self.owner.get_all_tasks(),
            key=lambda pt: (_PRIORITY_ORDER[pt[1].priority], pt[1].duration_minutes),
        )
