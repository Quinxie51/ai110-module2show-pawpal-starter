from pawpal_system import Task, Pet, Owner, Scheduler, Priority, Frequency


def section(title: str) -> None:
    print(f"\n{'-'*50}")
    print(f"  {title}")
    print(f"{'-'*50}")


# ---------------------------------------------------------------------------
# Setup: owner + pets + tasks (intentionally added out of time order)
# ---------------------------------------------------------------------------
jordan = Owner(name="Jordan", available_minutes=120)

mochi = Pet(name="Mochi", species="dog")
luna  = Pet(name="Luna",  species="cat")

# Tasks added OUT of time order to prove sort_by_time works
mochi.add_task(Task("Evening walk",    30, Priority.MEDIUM, start_time="17:00"))
mochi.add_task(Task("Morning walk",    30, Priority.HIGH,   start_time="07:30", frequency=Frequency.DAILY))
mochi.add_task(Task("Obedience class", 20, Priority.LOW,    start_time="10:00"))

luna.add_task(Task("Feeding",          10, Priority.HIGH,   start_time="08:00", frequency=Frequency.DAILY))
luna.add_task(Task("Litter cleaning",  10, Priority.HIGH,   start_time="08:15"))
luna.add_task(Task("Playtime",         25, Priority.MEDIUM, start_time="15:00"))

# Conflict task: overlaps with Luna's Feeding (08:00–08:10) by 5 min
mochi.add_task(Task("Vet call",        15, Priority.HIGH,   start_time="08:05"))

jordan.add_pet(mochi)
jordan.add_pet(luna)

scheduler = Scheduler(owner=jordan)

# ---------------------------------------------------------------------------
# 1. Full schedule sorted by time
# ---------------------------------------------------------------------------
section("1. Today's Schedule (sorted by start_time)")
scheduler.print_schedule()

# ---------------------------------------------------------------------------
# 2. Filter — incomplete tasks for Mochi only
# ---------------------------------------------------------------------------
section("2. Filter: Mochi's pending tasks")
mochi_pending = scheduler.filter_tasks(pet_name="Mochi", completed=False)
for pet, task in mochi_pending:
    print(f"  {task}")

# ---------------------------------------------------------------------------
# 3. Recurring tasks — mark complete, collect next occurrence
# ---------------------------------------------------------------------------
section("3. Recurring task: mark 'Morning walk' complete")
for pet, task in scheduler.filter_tasks(pet_name="Mochi"):
    if task.title == "Morning walk":
        next_task = task.mark_complete()
        print(f"  Completed : {task}")
        if next_task:
            pet.add_task(next_task)
            print(f"  Next occ. : {next_task}")

section("4. Filter: completed tasks (after mark_complete)")
done = scheduler.filter_tasks(completed=True)
for pet, task in done:
    print(f"  [{pet.name}] {task}")

# ---------------------------------------------------------------------------
# 5. Conflict detection
# ---------------------------------------------------------------------------
section("5. Conflict detection")
conflicts = scheduler.detect_conflicts()
if conflicts:
    for warning in conflicts:
        print(f"  {warning}")
else:
    print("  No conflicts found.")
