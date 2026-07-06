"""PawPal+ Streamlit UI.

Thin presentation layer over the backend classes in pawpal_system.py. All state
lives in a single Owner object held in st.session_state, so pets and tasks persist
across reruns and every widget reads/writes the same source of truth.
"""

from datetime import time

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# --- State: one Owner for the whole session -------------------------------
if "owner" not in st.session_state:
    st.session_state["owner"] = Owner(name="Jordan", available_minutes=90)

owner: Owner = st.session_state["owner"]

st.title("🐾 PawPal+")
st.caption("Plan your pets' care day around your available time and each task's priority.")

# Show any message carried over from an action that triggered a rerun.
if flash := st.session_state.pop("flash", None):
    st.success(flash)

# --- Owner settings --------------------------------------------------------
with st.expander("Owner settings", expanded=False):
    owner.name = st.text_input("Owner name", value=owner.name)
    owner.available_minutes = st.number_input(
        "Time available today (minutes)",
        min_value=5,
        max_value=600,
        value=owner.available_minutes,
        step=5,
        help="The scheduler keeps the highest-priority tasks that fit in this budget.",
    )

st.divider()

# --- Add a pet -------------------------------------------------------------
st.subheader("Add a pet")
with st.form("add_pet_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        new_pet_name = st.text_input("Pet name", value="")
    with col2:
        new_pet_species = st.selectbox("Species", ["dog", "cat", "other"])
    submitted_pet = st.form_submit_button("Add pet")

if submitted_pet:
    name = new_pet_name.strip()
    if not name:
        st.warning("Give your pet a name first.")
    elif owner.get_pet(name) is not None:
        st.warning(f"You already have a pet named {name}.")
    else:
        owner.add_pet(Pet(name=name, species=new_pet_species))
        st.success(f"Added {name} ({new_pet_species}).")

st.divider()

# --- Schedule a task -------------------------------------------------------
st.subheader("Schedule a task")
if not owner.pets:
    st.info("Add a pet above before scheduling tasks.")
else:
    with st.form("add_task_form", clear_on_submit=True):
        pet_names = [pet.name for pet in owner.pets]
        target_pet_name = st.selectbox("For which pet?", pet_names)

        task_title = st.text_input("Task title", value="Morning walk")
        col1, col2, col3 = st.columns(3)
        with col1:
            duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
        with col2:
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
        with col3:
            preferred = st.time_input("Preferred time", value=time(8, 0))

        col4, col5 = st.columns(2)
        with col4:
            category = st.selectbox(
                "Category", ["walk", "feeding", "meds", "enrichment", "grooming", "general"]
            )
        with col5:
            frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])

        submitted_task = st.form_submit_button("Add task")

    if submitted_task:
        title = task_title.strip()
        pet = owner.get_pet(target_pet_name)
        if not title:
            st.warning("Give the task a title first.")
        elif pet is None:
            st.warning("That pet no longer exists.")
        else:
            pet.add_task(
                Task(
                    title=title,
                    duration_minutes=int(duration),
                    priority=priority,
                    preferred_time=preferred,
                    category=category,
                    frequency=frequency,
                )
            )
            st.success(f"Added '{title}' for {pet.name}.")

st.divider()

# --- Current pets & tasks --------------------------------------------------
st.subheader("Your pets & tasks")
if not owner.pets:
    st.info("No pets yet.")
else:
    for pet in owner.pets:
        pending = pet.get_pending_tasks()
        st.markdown(f"**{pet.name}** ({pet.species}) — {len(pending)} pending task(s)")
        if not pet.tasks:
            st.caption("No tasks yet.")
            continue
        for i, task in enumerate(pet.tasks):
            cols = st.columns([6, 1])
            cols[0].write(("~~" + str(task) + "~~") if task.completed else str(task))
            if not task.completed:
                # A unique key per checkbox keeps Streamlit's widget state stable.
                if cols[1].checkbox("done", key=f"{pet.name}-{i}-{task.title}"):
                    task.mark_complete()
                    # Roll daily/weekly tasks forward to their next occurrence.
                    created = Scheduler(owner).advance_recurring_tasks()
                    msg = f"Marked '{task.title}' complete."
                    if created:
                        msg += f" Scheduled next {task.frequency} occurrence."
                    st.session_state["flash"] = msg
                    st.rerun()

st.divider()

# --- Generate today's schedule --------------------------------------------
st.subheader("Today's Schedule")
if st.button("Generate schedule"):
    scheduler = Scheduler(owner)

    # Surface any same-time conflicts before showing the plan.
    for warning in scheduler.detect_conflicts():
        st.warning(warning)

    plan = scheduler.build_plan()  # already sorted by time via Scheduler.sort_by_time

    if not plan:
        st.info("Nothing to plan — add some tasks (or you've completed them all!).")
    else:
        rows = [
            {
                "Time": t.preferred_time.strftime("%H:%M") if t.preferred_time else "—",
                "Pet": t.pet_name,
                "Task": t.title,
                "Duration": f"{t.duration_minutes} min",
                "Priority": t.priority,
            }
            for t in plan
        ]
        st.table(rows)
        st.caption(scheduler.explain_plan(plan))
