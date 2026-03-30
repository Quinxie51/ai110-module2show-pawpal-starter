from pawpal_system import Task, Pet, Owner, Scheduler, Priority

# --- Build owner ---
jordan = Owner(name="Jordan", available_minutes=90)

# --- Build pets ---
mochi = Pet(name="Mochi", species="dog")
luna = Pet(name="Luna", species="cat")

# --- Add tasks to Mochi ---
mochi.add_task(Task("Morning walk",      duration_minutes=30, priority=Priority.HIGH))
mochi.add_task(Task("Brush coat",        duration_minutes=15, priority=Priority.MEDIUM))
mochi.add_task(Task("Obedience training",duration_minutes=20, priority=Priority.LOW))

# --- Add tasks to Luna ---
luna.add_task(Task("Feeding",            duration_minutes=10, priority=Priority.HIGH))
luna.add_task(Task("Litter box cleaning",duration_minutes=10, priority=Priority.HIGH))
luna.add_task(Task("Playtime",           duration_minutes=25, priority=Priority.MEDIUM))

# --- Register pets with owner ---
jordan.add_pet(mochi)
jordan.add_pet(luna)

# --- Run scheduler ---
scheduler = Scheduler(owner=jordan)
scheduler.print_schedule()
