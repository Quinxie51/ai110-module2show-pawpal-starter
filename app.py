import streamlit as st
from pawpal_system import Task, Pet, Owner, Scheduler, Priority

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ---------------------------------------------------------------------------
# Session state — initialised once per browser session so objects survive
# every re-run that Streamlit triggers on any user interaction.
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None          # set after the owner form below

# ---------------------------------------------------------------------------
# Step 1: Owner setup
# ---------------------------------------------------------------------------
st.subheader("Owner")

with st.form("owner_form"):
    owner_name = st.text_input("Your name", value="Jordan")
    available_minutes = st.number_input(
        "Available time today (minutes)", min_value=10, max_value=480, value=120
    )
    if st.form_submit_button("Save owner"):
        # Preserve existing pets if the owner already exists
        existing_pets = st.session_state.owner.pets if st.session_state.owner else []
        st.session_state.owner = Owner(
            name=owner_name,
            available_minutes=int(available_minutes),
            pets=existing_pets,
        )
        st.success(f"Owner saved: {owner_name} ({available_minutes} min available)")

if st.session_state.owner is None:
    st.info("Save an owner above to get started.")
    st.stop()

owner: Owner = st.session_state.owner

st.divider()

# ---------------------------------------------------------------------------
# Step 2: Add a pet
# ---------------------------------------------------------------------------
st.subheader("Pets")

with st.form("add_pet_form", clear_on_submit=True):
    pet_name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", ["dog", "cat", "other"])
    if st.form_submit_button("Add pet"):
        owner.add_pet(Pet(name=pet_name, species=species))
        st.success(f"Added {pet_name} the {species}!")

if owner.pets:
    for pet in owner.pets:
        st.markdown(f"- **{pet.name}** ({pet.species}) — {len(pet.get_tasks())} task(s)")
else:
    st.info("No pets yet. Add one above.")

st.divider()

# ---------------------------------------------------------------------------
# Step 3: Add a task to a pet
# ---------------------------------------------------------------------------
st.subheader("Tasks")

if not owner.pets:
    st.warning("Add at least one pet before adding tasks.")
else:
    with st.form("add_task_form", clear_on_submit=True):
        pet_options = {p.name: p for p in owner.pets}
        selected_pet_name = st.selectbox("Assign to pet", list(pet_options.keys()))
        task_title = st.text_input("Task title", value="Morning walk")
        duration = st.number_input(
            "Duration (minutes)", min_value=1, max_value=240, value=20
        )
        priority_str = st.selectbox("Priority", ["high", "medium", "low"])

        if st.form_submit_button("Add task"):
            new_task = Task(
                title=task_title,
                duration_minutes=int(duration),
                priority=Priority(priority_str),
            )
            pet_options[selected_pet_name].add_task(new_task)
            st.success(f'Added "{task_title}" to {selected_pet_name}.')

    # Show all tasks per pet
    for pet in owner.pets:
        tasks = pet.get_tasks()
        if tasks:
            st.markdown(f"**{pet.name}'s tasks**")
            for task in tasks:
                badge = "🔴" if task.is_high_priority() else ("🟡" if task.priority.value == "medium" else "🟢")
                done = "~~" if task.completed else ""
                st.markdown(
                    f"- {badge} {done}{task.title}{done} — {task.duration_minutes} min"
                )

st.divider()

# ---------------------------------------------------------------------------
# Step 4: Generate schedule
# ---------------------------------------------------------------------------
st.subheader("Build Schedule")

if st.button("Generate schedule"):
    all_tasks = owner.get_all_tasks()
    if not all_tasks:
        st.warning("Add some tasks first.")
    else:
        scheduler = Scheduler(owner=owner)
        schedule = scheduler.build_schedule()
        skipped = [
            (pet, task) for pet, task in all_tasks
            if not task.completed and (pet, task) not in schedule
        ]

        total = sum(t.duration_minutes for _, t in schedule)
        st.success(f"Scheduled {len(schedule)} task(s) — {total} / {owner.available_minutes} min used")

        if schedule:
            st.markdown("### Today's Plan")
            for i, (pet, task) in enumerate(schedule, 1):
                badge = "🔴" if task.is_high_priority() else ("🟡" if task.priority.value == "medium" else "🟢")
                st.markdown(
                    f"{i}. {badge} **[{pet.name}]** {task.title} — {task.duration_minutes} min"
                )

        if skipped:
            with st.expander(f"Skipped ({len(skipped)} task(s) — not enough time)"):
                for pet, task in skipped:
                    st.markdown(f"- [{pet.name}] {task.title} ({task.duration_minutes} min)")
