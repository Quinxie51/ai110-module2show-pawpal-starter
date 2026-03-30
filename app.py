import streamlit as st
from pawpal_system import Task, Pet, Owner, Scheduler, Priority, Frequency

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("Smart pet care scheduling — sort by time, detect conflicts, and handle recurring tasks.")

# ---------------------------------------------------------------------------
# Session state — survives every Streamlit re-run within the same browser tab
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None

# ---------------------------------------------------------------------------
# Section 1: Owner
# ---------------------------------------------------------------------------
st.subheader("Owner")

with st.form("owner_form"):
    owner_name = st.text_input("Your name", value="Jordan")
    available_minutes = st.number_input(
        "Available time today (minutes)", min_value=10, max_value=480, value=120
    )
    if st.form_submit_button("Save owner"):
        existing_pets = st.session_state.owner.pets if st.session_state.owner else []
        st.session_state.owner = Owner(
            name=owner_name,
            available_minutes=int(available_minutes),
            pets=existing_pets,
        )
        st.success(f"Saved: {owner_name} with {available_minutes} min available today.")

if st.session_state.owner is None:
    st.info("Save an owner above to get started.")
    st.stop()

owner: Owner = st.session_state.owner

st.divider()

# ---------------------------------------------------------------------------
# Section 2: Pets
# ---------------------------------------------------------------------------
st.subheader("Pets")

with st.form("add_pet_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        pet_name = st.text_input("Pet name", value="Mochi")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "other"])
    if st.form_submit_button("Add pet"):
        owner.add_pet(Pet(name=pet_name, species=species))
        st.success(f"Added {pet_name} the {species}!")

if owner.pets:
    cols = st.columns(len(owner.pets))
    for col, pet in zip(cols, owner.pets):
        pending = sum(1 for t in pet.get_tasks() if not t.completed)
        done    = sum(1 for t in pet.get_tasks() if t.completed)
        col.metric(label=f"{pet.name} ({pet.species})", value=f"{pending} pending", delta=f"{done} done")
else:
    st.info("No pets yet. Add one above.")

st.divider()

# ---------------------------------------------------------------------------
# Section 3: Tasks
# ---------------------------------------------------------------------------
st.subheader("Tasks")

_PRIORITY_EMOJI = {"high": "🔴", "medium": "🟡", "low": "🟢"}
_FREQ_LABELS    = {"once": "Once", "daily": "Daily", "weekly": "Weekly"}

if not owner.pets:
    st.warning("Add at least one pet before adding tasks.")
else:
    with st.form("add_task_form", clear_on_submit=True):
        pet_options = {p.name: p for p in owner.pets}
        c1, c2 = st.columns(2)
        with c1:
            selected_pet_name = st.selectbox("Assign to pet", list(pet_options.keys()))
            task_title = st.text_input("Task title", value="Morning walk")
            start_time_str = st.text_input("Start time (HH:MM, optional)", value="")
        with c2:
            duration      = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
            priority_str  = st.selectbox("Priority", ["high", "medium", "low"])
            frequency_str = st.selectbox("Frequency", ["once", "daily", "weekly"])

        if st.form_submit_button("Add task"):
            new_task = Task(
                title=task_title,
                duration_minutes=int(duration),
                priority=Priority(priority_str),
                start_time=start_time_str.strip() or None,
                frequency=Frequency(frequency_str),
            )
            pet_options[selected_pet_name].add_task(new_task)
            st.success(f'Added "{task_title}" to {selected_pet_name}.')

    # -- Conflict banner (live, before schedule is generated) --
    scheduler = Scheduler(owner=owner)
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        with st.expander(f"⚠️ {len(conflicts)} scheduling conflict(s) detected — expand to review", expanded=True):
            for w in conflicts:
                st.warning(w)

    # -- Task table per pet --
    for pet in owner.pets:
        tasks = pet.get_tasks()
        if not tasks:
            continue
        st.markdown(f"**{pet.name}'s tasks**")
        rows = []
        for task in tasks:
            rows.append({
                "": _PRIORITY_EMOJI.get(task.priority.value, ""),
                "Title": ("~~" + task.title + "~~") if task.completed else task.title,
                "Start": task.start_time or "—",
                "Duration": f"{task.duration_minutes} min",
                "Priority": task.priority.value,
                "Frequency": task.frequency.value,
                "Status": "done" if task.completed else "pending",
            })
        st.table(rows)

    # -- Mark tasks complete --
    with st.expander("Mark a task complete"):
        pending_pairs = scheduler.filter_tasks(completed=False)
        if not pending_pairs:
            st.info("All tasks are already complete.")
        else:
            options = {
                f"[{p.name}] {t.title}": (p, t) for p, t in pending_pairs
            }
            chosen = st.selectbox("Select task to mark complete", list(options.keys()))
            if st.button("Mark complete"):
                pet, task = options[chosen]
                next_task = task.mark_complete()
                if next_task:
                    pet.add_task(next_task)
                    st.success(
                        f'"{task.title}" marked done. '
                        f"Next {task.frequency.value} occurrence added automatically."
                    )
                else:
                    st.success(f'"{task.title}" marked done.')

st.divider()

# ---------------------------------------------------------------------------
# Section 4: Schedule
# ---------------------------------------------------------------------------
st.subheader("Today's Schedule")

if st.button("Generate schedule", type="primary"):
    all_tasks = owner.get_all_tasks()
    if not all_tasks:
        st.warning("Add some tasks first.")
    else:
        scheduler  = Scheduler(owner=owner)
        schedule   = scheduler.sort_by_time(scheduler.build_schedule())
        skipped    = [
            (p, t) for p, t in all_tasks
            if not t.completed and (p, t) not in schedule
        ]
        conflicts  = scheduler.detect_conflicts()
        total      = sum(t.duration_minutes for _, t in schedule)

        # Conflict warnings at the top
        if conflicts:
            for w in conflicts:
                st.warning(f"⚠️ {w}")

        # Summary metric row
        m1, m2, m3 = st.columns(3)
        m1.metric("Tasks scheduled", len(schedule))
        m2.metric("Time used", f"{total} min", delta=f"{owner.available_minutes - total} min free")
        m3.metric("Tasks skipped", len(skipped))

        if schedule:
            st.markdown("#### Plan (sorted by start time)")
            for i, (pet, task) in enumerate(schedule, 1):
                badge = _PRIORITY_EMOJI.get(task.priority.value, "")
                time_tag  = f"**{task.start_time}** — " if task.start_time else ""
                freq_tag  = f" *(repeats {task.frequency.value})*" if task.frequency != Frequency.ONCE else ""
                st.markdown(
                    f"{i}. {badge} {time_tag}**[{pet.name}]** {task.title}"
                    f" — {task.duration_minutes} min{freq_tag}"
                )

        if skipped:
            with st.expander(f"Skipped ({len(skipped)} task(s) — not enough time)"):
                for pet, task in skipped:
                    st.markdown(
                        f"- [{pet.name}] {task.title}"
                        f" ({task.duration_minutes} min, {task.priority.value})"
                    )

        if not schedule:
            st.info("Nothing to schedule — all tasks may already be complete or exceed your time budget.")
