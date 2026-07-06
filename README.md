# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Running the CLI demo (`python main.py`) produces:

```
🐾 Today's Schedule for Jordan
================================================
  07:30  Luna      Refill food           5 min  [medium]
  08:00  Mochi     Morning walk         30 min  [high]
  08:00  Luna      Litter cleanup       10 min  [high]
  16:00  Mochi     Fetch / play         25 min  [low]
  18:00  Mochi     Dinner               10 min  [high]
================================================
Time budget: 90 min. Planned 5 of 6 pending tasks using 80 min.
Tasks are chosen highest-priority first (so the day stays within budget), then listed by time of day.
Skipped for lack of time: Brush coat (low).

🔎 Conflicts
------------------------------------------------
  ⚠️ 08:00 conflict: Mochi's 'Morning walk', Luna's 'Litter cleanup'

🔁 Recurring roll-forward
------------------------------------------------
  Completed today: Morning walk (daily) for Mochi
  Created for Mon Jul 06: Morning walk for Mochi
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
============================= test session starts ==============================
platform darwin -- Python 3.13.5, pytest-9.1.1, pluggy-1.6.0
rootdir: ai110-module2show-pawpal-starter
collected 11 items

tests/test_pawpal.py::test_task_mark_complete_changes_status PASSED       [  9%]
tests/test_pawpal.py::test_adding_task_increases_pet_task_count PASSED    [ 18%]
tests/test_pawpal.py::test_add_task_stamps_pet_name PASSED                [ 27%]
tests/test_pawpal.py::test_owner_collects_tasks_across_pets PASSED        [ 36%]
tests/test_pawpal.py::test_scheduler_respects_time_budget PASSED          [ 45%]
tests/test_pawpal.py::test_completed_tasks_excluded_from_plan PASSED      [ 54%]
tests/test_pawpal.py::test_sort_by_time_returns_chronological_order PASSED [ 63%]
tests/test_pawpal.py::test_completing_daily_task_creates_next_day_occurrence PASSED [ 72%]
tests/test_pawpal.py::test_advance_recurring_does_not_duplicate PASSED    [ 81%]
tests/test_pawpal.py::test_detect_conflicts_flags_same_time_tasks PASSED  [ 90%]
tests/test_pawpal.py::test_detect_conflicts_ignores_distinct_times PASSED [100%]

============================== 11 passed in 0.02s ==============================
```

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_priority`, `Scheduler.sort_by_time` | Select tasks highest-priority-first (ties broken by time), then display sorted by time of day. |
| Filtering | `Scheduler.filter_to_budget`, `filter_by_pet`, `filter_by_completion`; `Owner/Pet.get_pending_tasks` | Greedily keep the highest-priority tasks that fit the owner's time budget; also filter by pet or by completion status. |
| Conflict handling | `Scheduler.detect_conflicts` | Flags tasks sharing the exact same preferred time (across all pets); surfaced via `st.warning` in the UI. |
| Recurring tasks | `Scheduler.create_next_occurrence`, `advance_recurring_tasks` | Completing a daily/weekly task creates the next occurrence with `datetime.timedelta` (+1 or +7 days), guarded so it never duplicates. |

## 📸 Demo Walkthrough

1. **Set up the owner** — open the app (`streamlit run app.py`) and, under *Owner settings*, set your name and how many minutes you have today. This becomes the scheduler's time budget.
2. **Add a pet** — enter a name and species and click *Add pet*. Duplicate and blank names are rejected; a success message confirms the add.
3. **Schedule tasks** — pick a pet, then add tasks with a duration, priority, preferred time, category, and frequency (once / daily / weekly).
4. **View today's schedule** — click *Generate schedule*. PawPal+ keeps the highest-priority tasks that fit your time budget and lists them **sorted by time of day**, with a one-line explanation of what it planned and skipped.
5. **See conflict warnings** — if two tasks share the same time (even across different pets), a ⚠️ warning appears above the schedule.
6. **Complete a task** — tick *done*. Completed tasks drop out of the plan, and **daily/weekly tasks automatically roll forward** to their next occurrence.

**Key Scheduler behaviors:** sorting (by priority to select, by time to display), budget filtering, exact-time conflict detection, and recurring roll-forward.

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
