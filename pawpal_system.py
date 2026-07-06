"""PawPal+ core system.

Implements the four core classes designed in Phase 1 (see diagrams/uml_draft.mmd):

    Owner  1 --> *  Pet   (an owner has many pets)
    Pet    1 --> *  Task  (a pet has many care tasks)
    Scheduler --> Owner   (the scheduler reads tasks through the owner)

The code favors clarity over cleverness: small methods, plain data flow, and a
single source of truth (PRIORITY_ORDER) for how priorities compare.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time, timedelta
from typing import Optional

# Ordering used to compare task priorities (higher number = more urgent).
PRIORITY_ORDER = {"low": 1, "medium": 2, "high": 3}

# Valid recurrence values for a task's `frequency` field.
VALID_FREQUENCIES = {"once", "daily", "weekly"}


@dataclass
class Task:
    """A single pet-care action (walk, feeding, meds, etc.) to be scheduled."""

    title: str
    duration_minutes: int
    priority: str = "medium"
    preferred_time: Optional[time] = None
    category: str = "general"
    frequency: str = "once"
    completed: bool = False
    task_id: str = ""
    # The calendar day this task is for; enables rolling recurring tasks forward.
    due_date: Optional[date] = None
    # Set True once a completed recurring task has spawned its next occurrence,
    # so we never create duplicate follow-ups for the same completion.
    rolled_over: bool = False
    # Set by Pet.add_task so the scheduler/UI can show which pet a task belongs to.
    pet_name: str = ""

    def mark_complete(self) -> None:
        """Mark this task as done so it is excluded from future plans."""
        self.completed = True

    def priority_rank(self) -> int:
        """Return a numeric rank for this task's priority (higher = more urgent)."""
        return PRIORITY_ORDER.get(self.priority, 0)

    def time_key(self) -> time:
        """Return a sortable time; tasks with no preferred time sort to the end of day."""
        return self.preferred_time or time(23, 59)

    def __str__(self) -> str:
        """Return a human-readable one-line summary of the task."""
        when = self.preferred_time.strftime("%H:%M") if self.preferred_time else "anytime"
        status = "done" if self.completed else "pending"
        return (
            f"{when} - {self.title} ({self.duration_minutes} min, "
            f"{self.priority} priority) [{status}]"
        )


@dataclass
class Pet:
    """An animal owned by the user; holds its own list of care tasks."""

    name: str
    species: str
    preferences: dict = field(default_factory=dict)
    tasks: list[Task] = field(default_factory=list)
    pet_id: str = ""

    def add_task(self, task: Task) -> None:
        """Attach a care task to this pet and stamp it with the pet's name."""
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> None:
        """Remove a task from this pet by its id (no-op if the id isn't found)."""
        self.tasks = [t for t in self.tasks if t.task_id != task_id]

    def get_all_tasks(self) -> list[Task]:
        """Return every task belonging to this pet."""
        return list(self.tasks)

    def get_pending_tasks(self) -> list[Task]:
        """Return only the tasks that are not yet completed."""
        return [t for t in self.tasks if not t.completed]


@dataclass
class Owner:
    """The app user; owns one or more pets and has a daily time budget."""

    name: str
    available_minutes: int = 120
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a new pet under this owner."""
        self.pets.append(pet)

    def get_pet(self, name: str) -> Optional[Pet]:
        """Look up one of the owner's pets by name (case-insensitive)."""
        for pet in self.pets:
            if pet.name.lower() == name.lower():
                return pet
        return None

    def get_all_tasks(self) -> list[Task]:
        """Collect tasks across all of the owner's pets into one flat list."""
        tasks: list[Task] = []
        for pet in self.pets:
            tasks.extend(pet.get_all_tasks())
        return tasks

    def get_pending_tasks(self) -> list[Task]:
        """Collect only the not-yet-completed tasks across all pets."""
        return [t for t in self.get_all_tasks() if not t.completed]


class Scheduler:
    """Builds and explains a daily care plan from an owner's tasks and constraints."""

    def __init__(
        self,
        owner: Owner,
        start_time: time = time(8, 0),
        time_budget: Optional[int] = None,
    ):
        """Bind the scheduler to an owner, a day start time, and a time budget (minutes).

        If time_budget is None, the owner's available_minutes is used.
        """
        self.owner = owner
        self.start_time = start_time
        self.time_budget = time_budget if time_budget is not None else owner.available_minutes

    def sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered highest priority first, breaking ties by preferred time."""
        return sorted(tasks, key=lambda t: (-t.priority_rank(), t.time_key()))

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered by their preferred time of day (earliest first)."""
        return sorted(tasks, key=lambda t: t.time_key())

    def filter_to_budget(self, tasks: list[Task]) -> list[Task]:
        """Greedily keep the highest-priority tasks that fit within the time budget.

        Tasks are considered in priority order; each is kept only if it still fits
        in the remaining minutes. Lower-priority tasks are dropped once time runs out.
        """
        kept: list[Task] = []
        remaining = self.time_budget
        for task in self.sort_by_priority(tasks):
            if task.duration_minutes <= remaining:
                kept.append(task)
                remaining -= task.duration_minutes
        return kept

    def build_plan(self) -> list[Task]:
        """Produce today's ordered plan: pending tasks, chosen by priority, shown by time.

        Steps: gather pending tasks from all pets -> keep those that fit the budget
        (highest priority wins) -> present the result sorted by time of day.
        """
        pending = self.owner.get_pending_tasks()
        chosen = self.filter_to_budget(pending)
        return self.sort_by_time(chosen)

    def explain_plan(self, plan: list[Task]) -> str:
        """Return a text explanation of how the plan was built and why tasks were dropped."""
        pending = self.owner.get_pending_tasks()
        used = sum(t.duration_minutes for t in plan)
        dropped = [t for t in pending if t not in plan]

        lines = [
            f"Time budget: {self.time_budget} min. Planned {len(plan)} of "
            f"{len(pending)} pending tasks using {used} min.",
            "Tasks are chosen highest-priority first (so the day stays within budget), "
            "then listed by time of day.",
        ]
        if dropped:
            names = ", ".join(f"{t.title} ({t.priority})" for t in dropped)
            lines.append(f"Skipped for lack of time: {names}.")
        else:
            lines.append("Everything pending fit in the budget.")
        return "\n".join(lines)

    # --- Filtering ---------------------------------------------------------

    def filter_by_pet(self, tasks: list[Task], pet_name: str) -> list[Task]:
        """Return only the tasks belonging to the named pet (case-insensitive)."""
        return [t for t in tasks if t.pet_name.lower() == pet_name.lower()]

    def filter_by_completion(self, tasks: list[Task], completed: bool = False) -> list[Task]:
        """Return only the tasks whose completed status matches the flag."""
        return [t for t in tasks if t.completed == completed]

    # --- Recurring tasks ---------------------------------------------------

    def create_next_occurrence(self, task: Task) -> Optional[Task]:
        """Build the next occurrence of a recurring task, or None if it doesn't recur.

        A daily task rolls forward one day and a weekly task seven days, using
        datetime.timedelta. The new task starts uncompleted with the same time,
        priority, and duration; its due_date advances from the original's date.
        """
        if task.frequency not in ("daily", "weekly"):
            return None

        step = timedelta(days=1) if task.frequency == "daily" else timedelta(days=7)
        base_date = task.due_date or date.today()
        return Task(
            title=task.title,
            duration_minutes=task.duration_minutes,
            priority=task.priority,
            preferred_time=task.preferred_time,
            category=task.category,
            frequency=task.frequency,
            completed=False,
            due_date=base_date + step,
        )

    def advance_recurring_tasks(self) -> list[Task]:
        """Roll every completed recurring task forward, attaching the next occurrence.

        Scans all pets; for each completed daily/weekly task not yet rolled over,
        creates its next occurrence, adds it to the same pet, and marks the original
        so it isn't rolled again. Returns the newly created tasks.
        """
        created: list[Task] = []
        for pet in self.owner.pets:
            for task in list(pet.tasks):
                if task.completed and not task.rolled_over:
                    nxt = self.create_next_occurrence(task)
                    if nxt is not None:
                        pet.add_task(nxt)
                        task.rolled_over = True
                        created.append(nxt)
        return created

    # --- Conflict detection -----------------------------------------------

    def detect_conflicts(self, tasks: Optional[list[Task]] = None) -> list[str]:
        """Return warning messages for tasks sharing the exact same preferred time.

        Groups pending tasks by preferred_time (ignoring tasks with no set time)
        and flags any time slot holding more than one task, across all pets.
        """
        if tasks is None:
            tasks = self.owner.get_pending_tasks()

        by_time: dict[time, list[Task]] = {}
        for task in tasks:
            if task.preferred_time is not None:
                by_time.setdefault(task.preferred_time, []).append(task)

        warnings: list[str] = []
        for slot in sorted(by_time):
            clashing = by_time[slot]
            if len(clashing) > 1:
                labels = ", ".join(f"{t.pet_name}'s '{t.title}'" for t in clashing)
                warnings.append(f"⚠️ {slot.strftime('%H:%M')} conflict: {labels}")
        return warnings
