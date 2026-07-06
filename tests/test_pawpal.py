"""Basic pytest suite for PawPal+ core behaviors.

Run with:  python -m pytest
"""

from datetime import date, time, timedelta

from pawpal_system import Owner, Pet, Scheduler, Task


def test_task_mark_complete_changes_status():
    """A new task starts pending; mark_complete() should flip it to completed."""
    task = Task("Morning walk", 30, "high")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_adding_task_increases_pet_task_count():
    """Adding a task to a pet should grow that pet's task list by one."""
    pet = Pet(name="Mochi", species="dog")
    assert len(pet.get_all_tasks()) == 0
    pet.add_task(Task("Dinner", 10, "high"))
    assert len(pet.get_all_tasks()) == 1


def test_add_task_stamps_pet_name():
    """Pet.add_task should record the pet's name on the task for later display."""
    pet = Pet(name="Luna", species="cat")
    task = Task("Refill food", 5, "medium")
    pet.add_task(task)
    assert task.pet_name == "Luna"


def test_owner_collects_tasks_across_pets():
    """Owner.get_all_tasks should flatten tasks from every pet into one list."""
    owner = Owner(name="Jordan")
    dog = Pet(name="Mochi", species="dog")
    cat = Pet(name="Luna", species="cat")
    owner.add_pet(dog)
    owner.add_pet(cat)
    dog.add_task(Task("Walk", 30, "high"))
    cat.add_task(Task("Feed", 5, "medium"))
    assert len(owner.get_all_tasks()) == 2


def test_scheduler_respects_time_budget():
    """The scheduler should drop lower-priority tasks that don't fit the budget."""
    owner = Owner(name="Jordan", available_minutes=30)
    pet = Pet(name="Mochi", species="dog")
    owner.add_pet(pet)
    pet.add_task(Task("Walk", 30, "high", time(8, 0)))    # fills the whole budget
    pet.add_task(Task("Play", 20, "low", time(9, 0)))     # no room left -> dropped

    plan = Scheduler(owner).build_plan()
    titles = [t.title for t in plan]
    assert "Walk" in titles
    assert "Play" not in titles


def test_completed_tasks_excluded_from_plan():
    """Tasks already marked complete should not appear in today's plan."""
    owner = Owner(name="Jordan", available_minutes=120)
    pet = Pet(name="Mochi", species="dog")
    owner.add_pet(pet)
    done = Task("Walk", 30, "high", time(8, 0))
    done.mark_complete()
    pet.add_task(done)
    pet.add_task(Task("Dinner", 10, "high", time(18, 0)))

    plan = Scheduler(owner).build_plan()
    titles = [t.title for t in plan]
    assert "Walk" not in titles
    assert "Dinner" in titles


# --- Phase 4 features: sorting, recurrence, conflicts ---------------------

def test_sort_by_time_returns_chronological_order():
    """sort_by_time should order tasks from earliest to latest preferred time."""
    owner = Owner(name="Jordan")
    scheduler = Scheduler(owner)
    # Deliberately out of order so a passing test proves real sorting.
    tasks = [
        Task("Evening", 10, "low", time(18, 0)),
        Task("Morning", 10, "high", time(7, 0)),
        Task("Noon", 10, "medium", time(12, 0)),
    ]
    ordered = scheduler.sort_by_time(tasks)
    times = [t.preferred_time for t in ordered]
    assert times == [time(7, 0), time(12, 0), time(18, 0)]


def test_completing_daily_task_creates_next_day_occurrence():
    """Marking a daily task done and advancing should spawn an uncompleted copy
    dated one day later, attached to the same pet."""
    owner = Owner(name="Jordan")
    pet = Pet(name="Mochi", species="dog")
    owner.add_pet(pet)
    walk = Task("Walk", 30, "high", time(8, 0), "walk", "daily", due_date=date(2026, 7, 5))
    pet.add_task(walk)

    walk.mark_complete()
    created = Scheduler(owner).advance_recurring_tasks()

    assert len(created) == 1
    next_walk = created[0]
    assert next_walk.completed is False
    assert next_walk.due_date == date(2026, 7, 5) + timedelta(days=1)
    assert next_walk in pet.tasks


def test_advance_recurring_does_not_duplicate():
    """Rolling forward twice should not create a second follow-up for the same
    completion (guarded by the task's rolled_over flag)."""
    owner = Owner(name="Jordan")
    pet = Pet(name="Mochi", species="dog")
    owner.add_pet(pet)
    walk = Task("Walk", 30, "high", time(8, 0), "walk", "daily", due_date=date(2026, 7, 5))
    pet.add_task(walk)
    walk.mark_complete()

    scheduler = Scheduler(owner)
    scheduler.advance_recurring_tasks()
    created_again = scheduler.advance_recurring_tasks()
    assert created_again == []  # the freshly created task isn't complete, so nothing rolls


def test_detect_conflicts_flags_same_time_tasks():
    """Two tasks at the same preferred time (even across different pets) should
    produce exactly one conflict warning for that slot."""
    owner = Owner(name="Jordan")
    dog = Pet(name="Mochi", species="dog")
    cat = Pet(name="Luna", species="cat")
    owner.add_pet(dog)
    owner.add_pet(cat)
    dog.add_task(Task("Walk", 30, "high", time(8, 0)))
    cat.add_task(Task("Litter", 10, "high", time(8, 0)))  # same 08:00 slot -> conflict

    conflicts = Scheduler(owner).detect_conflicts()
    assert len(conflicts) == 1
    assert "08:00" in conflicts[0]


def test_detect_conflicts_ignores_distinct_times():
    """Tasks at different times should not be flagged as conflicting."""
    owner = Owner(name="Jordan")
    pet = Pet(name="Mochi", species="dog")
    owner.add_pet(pet)
    pet.add_task(Task("Walk", 30, "high", time(8, 0)))
    pet.add_task(Task("Dinner", 10, "high", time(18, 0)))

    assert Scheduler(owner).detect_conflicts() == []
