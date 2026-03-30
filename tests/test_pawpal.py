import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from pawpal_system import Task, Pet, Owner, Scheduler, Priority, Frequency


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_owner(minutes: int = 120) -> Owner:
    owner = Owner(name="Jordan", available_minutes=minutes)
    return owner


def make_pet(name: str = "Mochi", species: str = "dog") -> Pet:
    return Pet(name=name, species=species)


# ===========================================================================
# Task — basic behaviour
# ===========================================================================

def test_mark_complete_changes_status():
    """mark_complete() flips completed from False to True."""
    task = Task("Bath time", duration_minutes=20, priority=Priority.MEDIUM)
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_once_task_returns_none_on_complete():
    """A ONCE task returns None (no next occurrence) when completed."""
    task = Task("Vet visit", duration_minutes=60, priority=Priority.HIGH)
    result = task.mark_complete()
    assert result is None


def test_adding_task_increases_pet_task_count():
    """add_task() increases the pet's task list by exactly one."""
    pet = make_pet()
    assert len(pet.get_tasks()) == 0
    pet.add_task(Task("Walk", duration_minutes=30, priority=Priority.HIGH))
    assert len(pet.get_tasks()) == 1


# ===========================================================================
# Recurrence logic
# ===========================================================================

def test_daily_task_produces_next_occurrence():
    """Marking a DAILY task complete returns a new (incomplete) Task."""
    task = Task(
        "Morning walk", duration_minutes=30, priority=Priority.HIGH,
        frequency=Frequency.DAILY,
    )
    next_task = task.mark_complete()
    assert next_task is not None
    assert next_task.completed is False


def test_daily_task_next_occurrence_preserves_fields():
    """The next-occurrence task keeps the same title, duration, and priority."""
    task = Task(
        "Feeding", duration_minutes=10, priority=Priority.HIGH,
        frequency=Frequency.DAILY,
    )
    next_task = task.mark_complete()
    assert next_task.title == task.title
    assert next_task.duration_minutes == task.duration_minutes
    assert next_task.priority == task.priority
    assert next_task.frequency == Frequency.DAILY


def test_weekly_task_produces_next_occurrence():
    """Marking a WEEKLY task complete returns a new Task."""
    task = Task(
        "Bath time", duration_minutes=20, priority=Priority.MEDIUM,
        frequency=Frequency.WEEKLY,
    )
    next_task = task.mark_complete()
    assert next_task is not None
    assert next_task.frequency == Frequency.WEEKLY


def test_recurring_task_added_to_pet_after_complete():
    """Caller adds the next occurrence to the pet; task count stays the same total
    (one done + one new = same count)."""
    pet = make_pet()
    task = Task(
        "Walk", duration_minutes=30, priority=Priority.HIGH,
        frequency=Frequency.DAILY,
    )
    pet.add_task(task)
    assert len(pet.get_tasks()) == 1

    next_task = task.mark_complete()
    pet.add_task(next_task)
    assert len(pet.get_tasks()) == 2
    completed = [t for t in pet.get_tasks() if t.completed]
    pending   = [t for t in pet.get_tasks() if not t.completed]
    assert len(completed) == 1
    assert len(pending) == 1


# ===========================================================================
# Scheduler — build_schedule
# ===========================================================================

def test_scheduler_respects_time_budget():
    """Scheduled total must not exceed available_minutes."""
    owner = make_owner(minutes=30)
    pet = make_pet()
    pet.add_task(Task("Play",  duration_minutes=20, priority=Priority.HIGH))
    pet.add_task(Task("Groom", duration_minutes=20, priority=Priority.MEDIUM))
    owner.add_pet(pet)

    schedule = Scheduler(owner).build_schedule()
    total = sum(t.duration_minutes for _, t in schedule)
    assert total <= 30


def test_scheduler_skips_completed_tasks():
    """Completed tasks must not appear in the schedule."""
    owner = make_owner()
    pet = make_pet()
    done = Task("Morning walk", duration_minutes=30, priority=Priority.HIGH)
    done.mark_complete()
    pet.add_task(done)
    owner.add_pet(pet)

    assert len(Scheduler(owner).build_schedule()) == 0


def test_scheduler_prioritizes_high_priority_tasks():
    """HIGH priority tasks appear before LOW priority tasks."""
    owner = make_owner()
    pet = make_pet()
    pet.add_task(Task("Low task",  duration_minutes=10, priority=Priority.LOW))
    pet.add_task(Task("High task", duration_minutes=10, priority=Priority.HIGH))
    owner.add_pet(pet)

    schedule = Scheduler(owner).build_schedule()
    assert schedule[0][1].priority == Priority.HIGH


def test_scheduler_empty_when_no_tasks():
    """An owner with pets but no tasks produces an empty schedule."""
    owner = make_owner()
    owner.add_pet(make_pet("Mochi"))
    owner.add_pet(make_pet("Luna", "cat"))

    assert Scheduler(owner).build_schedule() == []


def test_scheduler_empty_when_no_pets():
    """An owner with no pets produces an empty schedule."""
    owner = make_owner()
    assert Scheduler(owner).build_schedule() == []


# ===========================================================================
# Sorting
# ===========================================================================

def test_sort_by_time_chronological_order():
    """sort_by_time returns tasks in ascending HH:MM order."""
    owner = make_owner()
    pet = make_pet()
    pet.add_task(Task("Evening walk", 30, Priority.MEDIUM, start_time="17:00"))
    pet.add_task(Task("Afternoon nap", 20, Priority.LOW,  start_time="13:00"))
    pet.add_task(Task("Morning walk",  30, Priority.HIGH, start_time="07:30"))
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    sorted_pairs = scheduler.sort_by_time(owner.get_all_tasks())
    times = [t.start_time for _, t in sorted_pairs]
    assert times == ["07:30", "13:00", "17:00"]


def test_sort_by_time_untimed_tasks_go_last():
    """Tasks without a start_time are placed after all timed tasks."""
    owner = make_owner()
    pet = make_pet()
    pet.add_task(Task("No time task", 10, Priority.HIGH))
    pet.add_task(Task("Early task",   10, Priority.HIGH, start_time="06:00"))
    owner.add_pet(pet)

    sorted_pairs = Scheduler(owner).sort_by_time(owner.get_all_tasks())
    assert sorted_pairs[0][1].start_time == "06:00"
    assert sorted_pairs[1][1].start_time is None


# ===========================================================================
# Filtering
# ===========================================================================

def test_filter_by_pet_name():
    """filter_tasks(pet_name=...) returns only that pet's tasks."""
    owner = make_owner()
    mochi = make_pet("Mochi")
    luna  = make_pet("Luna", "cat")
    mochi.add_task(Task("Walk",    20, Priority.HIGH))
    luna.add_task(Task("Feeding",  10, Priority.HIGH))
    owner.add_pet(mochi)
    owner.add_pet(luna)

    results = Scheduler(owner).filter_tasks(pet_name="Mochi")
    assert all(p.name == "Mochi" for p, _ in results)
    assert len(results) == 1


def test_filter_completed_only():
    """filter_tasks(completed=True) returns only done tasks."""
    owner = make_owner()
    pet = make_pet()
    t1 = Task("Walk",  20, Priority.HIGH)
    t2 = Task("Groom", 15, Priority.MEDIUM)
    t1.mark_complete()
    pet.add_task(t1)
    pet.add_task(t2)
    owner.add_pet(pet)

    done = Scheduler(owner).filter_tasks(completed=True)
    assert len(done) == 1
    assert done[0][1].title == "Walk"


def test_filter_pending_only():
    """filter_tasks(completed=False) returns only incomplete tasks."""
    owner = make_owner()
    pet = make_pet()
    t1 = Task("Walk",  20, Priority.HIGH)
    t2 = Task("Groom", 15, Priority.MEDIUM)
    t1.mark_complete()
    pet.add_task(t1)
    pet.add_task(t2)
    owner.add_pet(pet)

    pending = Scheduler(owner).filter_tasks(completed=False)
    assert len(pending) == 1
    assert pending[0][1].title == "Groom"


# ===========================================================================
# Conflict detection
# ===========================================================================

def test_no_conflicts_when_tasks_sequential():
    """Back-to-back tasks (one ends exactly when the next starts) do not conflict."""
    owner = make_owner()
    pet = make_pet()
    pet.add_task(Task("Walk",    30, Priority.HIGH,   start_time="08:00"))
    pet.add_task(Task("Feeding", 10, Priority.HIGH,   start_time="08:30"))
    owner.add_pet(pet)

    assert Scheduler(owner).detect_conflicts() == []


def test_conflict_detected_for_overlapping_tasks():
    """Two tasks whose windows overlap must produce at least one warning."""
    owner = make_owner()
    pet = make_pet()
    pet.add_task(Task("Vet call", 15, Priority.HIGH, start_time="08:05"))
    pet.add_task(Task("Feeding",  10, Priority.HIGH, start_time="08:00"))
    owner.add_pet(pet)

    warnings = Scheduler(owner).detect_conflicts()
    assert len(warnings) >= 1
    assert "Vet call" in warnings[0] or "Feeding" in warnings[0]


def test_conflict_detected_for_exact_same_start_time():
    """Two tasks with identical start times must be flagged as a conflict."""
    owner = make_owner()
    pet = make_pet()
    pet.add_task(Task("Task A", 20, Priority.HIGH,   start_time="09:00"))
    pet.add_task(Task("Task B", 20, Priority.MEDIUM, start_time="09:00"))
    owner.add_pet(pet)

    warnings = Scheduler(owner).detect_conflicts()
    assert len(warnings) >= 1


def test_conflict_ignores_completed_tasks():
    """Completed tasks must not be included in conflict checking."""
    owner = make_owner()
    pet = make_pet()
    done = Task("Old walk", 30, Priority.HIGH, start_time="08:00")
    done.mark_complete()
    pet.add_task(done)
    pet.add_task(Task("New walk", 30, Priority.HIGH, start_time="08:00"))
    owner.add_pet(pet)

    # Only one active task — no conflict possible
    assert Scheduler(owner).detect_conflicts() == []


def test_no_conflicts_for_untimed_tasks():
    """Tasks without start_time never trigger conflict warnings."""
    owner = make_owner()
    pet = make_pet()
    pet.add_task(Task("Walk",  30, Priority.HIGH))
    pet.add_task(Task("Groom", 30, Priority.HIGH))
    owner.add_pet(pet)

    assert Scheduler(owner).detect_conflicts() == []
