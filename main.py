"""PawPal+ CLI demo.

Builds a small owner/pet/task setup, runs the Scheduler, and prints a clean,
human-readable "Today's Schedule". Run with:  python main.py
"""

from datetime import time

from pawpal_system import Owner, Pet, Scheduler, Task


def print_schedule(owner: Owner, scheduler: Scheduler) -> None:
    """Print today's plan as a tidy, time-sorted table with an explanation."""
    plan = scheduler.build_plan()

    print(f"\n🐾 Today's Schedule for {owner.name}")
    print("=" * 48)
    if not plan:
        print("  Nothing planned — add some tasks!")
    else:
        for task in plan:
            when = task.preferred_time.strftime("%H:%M") if task.preferred_time else "  --  "
            print(
                f"  {when}  {task.pet_name:<8}  {task.title:<18}"
                f"  {task.duration_minutes:>3} min  [{task.priority}]"
            )
    print("=" * 48)
    print(scheduler.explain_plan(plan))


def main() -> None:
    """Assemble a demo owner with two pets and several tasks, then show the plan."""
    owner = Owner(name="Jordan", available_minutes=90)

    mochi = Pet(name="Mochi", species="dog")
    luna = Pet(name="Luna", species="cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)

    # Tasks span different times and priorities so the scheduler has real choices.
    # Note: Mochi's walk and Luna's litter cleanup are BOTH at 08:00 -> a conflict.
    mochi.add_task(Task("Morning walk", 30, "high", time(8, 0), "walk", "daily"))
    mochi.add_task(Task("Dinner", 10, "high", time(18, 0), "feeding", "daily"))
    mochi.add_task(Task("Fetch / play", 25, "low", time(16, 0), "enrichment"))
    luna.add_task(Task("Refill food", 5, "medium", time(7, 30), "feeding", "daily"))
    luna.add_task(Task("Litter cleanup", 10, "high", time(8, 0), "grooming", "daily"))
    luna.add_task(Task("Brush coat", 15, "low", time(20, 0), "grooming", "weekly"))

    scheduler = Scheduler(owner)
    print_schedule(owner, scheduler)

    # --- Conflict detection demo ------------------------------------------
    print("\n🔎 Conflicts")
    print("-" * 48)
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        for warning in conflicts:
            print(f"  {warning}")
    else:
        print("  No scheduling conflicts.")

    # --- Recurring task demo ----------------------------------------------
    print("\n🔁 Recurring roll-forward")
    print("-" * 48)
    walk = mochi.tasks[0]  # the daily 08:00 "Morning walk"
    walk.mark_complete()
    print(f"  Completed today: {walk.title} (daily) for {walk.pet_name}")
    created = scheduler.advance_recurring_tasks()
    for task in created:
        due = task.due_date.strftime("%a %b %d") if task.due_date else "next day"
        print(f"  Created for {due}: {task.title} for {task.pet_name}")


if __name__ == "__main__":
    main()
