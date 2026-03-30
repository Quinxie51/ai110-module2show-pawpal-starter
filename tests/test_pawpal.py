import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import Task, Pet, Owner, Scheduler, Priority


# --- Task tests ---

def test_mark_complete_changes_status():
    """mark_complete() should flip completed from False to True."""
    task = Task("Bath time", duration_minutes=20, priority=Priority.MEDIUM)
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_adding_task_increases_pet_task_count():
    """add_task() should increase the pet's task list by one."""
    pet = Pet(name="Mochi", species="dog")
    assert len(pet.get_tasks()) == 0
    pet.add_task(Task("Walk", duration_minutes=30, priority=Priority.HIGH))
    assert len(pet.get_tasks()) == 1


# --- Scheduler tests ---

def test_scheduler_respects_time_budget():
    """Scheduler should not schedule more minutes than the owner's available time."""
    owner = Owner(name="Jordan", available_minutes=30)
    pet = Pet(name="Luna", species="cat")
    pet.add_task(Task("Play",  duration_minutes=20, priority=Priority.HIGH))
    pet.add_task(Task("Groom", duration_minutes=20, priority=Priority.MEDIUM))
    owner.add_pet(pet)

    schedule = Scheduler(owner).build_schedule()
    total = sum(t.duration_minutes for _, t in schedule)
    assert total <= 30


def test_scheduler_skips_completed_tasks():
    """Scheduler should not include tasks that are already completed."""
    owner = Owner(name="Jordan", available_minutes=120)
    pet = Pet(name="Mochi", species="dog")
    done_task = Task("Morning walk", duration_minutes=30, priority=Priority.HIGH)
    done_task.mark_complete()
    pet.add_task(done_task)
    owner.add_pet(pet)

    schedule = Scheduler(owner).build_schedule()
    assert len(schedule) == 0


def test_scheduler_prioritizes_high_priority_tasks():
    """HIGH priority tasks should appear before LOW priority tasks in the schedule."""
    owner = Owner(name="Jordan", available_minutes=120)
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Low task",  duration_minutes=10, priority=Priority.LOW))
    pet.add_task(Task("High task", duration_minutes=10, priority=Priority.HIGH))
    owner.add_pet(pet)

    schedule = Scheduler(owner).build_schedule()
    priorities = [task.priority for _, task in schedule]
    assert priorities[0] == Priority.HIGH
