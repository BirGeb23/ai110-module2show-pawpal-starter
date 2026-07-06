# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

My initial UML had four classes mapped to real-world roles. `Owner` represents
the user and owns many `Pet`s; each `Pet` owns many `Task`s; `Task` is a single
care action (walk, feeding, meds); and `Scheduler` is the algorithm that reads an
owner's tasks and builds a daily plan. I made `Owner`, `Pet`, and `Task`
dataclasses because they are mostly data containers, and kept `Scheduler` a plain
class because it holds behavior rather than data.

**b. Design changes**

Yes. Two changes came out of implementation. First, I replaced `Task.recurring`
(a bool) with a `frequency` string ("once"/"daily"/"weekly") once I realized a
boolean couldn't distinguish daily from weekly recurrence. Second, I added a
`due_date` field and a `pet_name` stamp to `Task`: `due_date` was needed so the
recurrence logic could use `datetime.timedelta` to move a task to the next day,
and `pet_name` (set when a pet adds a task) let the `Scheduler` keep operating on
plain lists of tasks while the UI could still show which pet each task belonged to.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers three constraints: the owner's available time (a minute
budget), each task's priority, and its preferred time of day. I decided priority
mattered most, so the scheduler selects tasks highest-priority-first and keeps
only what fits the budget, then orders the survivors by time so the day reads
naturally. Health-critical tasks (walks, meds) should never be dropped in favor
of nice-to-haves.

**b. Tradeoffs**

Conflict detection flags tasks only when they share the *exact same start time*,
not when their time *ranges overlap*. This keeps the logic a simple group-by-time
that is easy to read, test, and explain to a user ("two things are booked for
08:00"). The cost is that it misses partial overlaps — an 08:00 30-minute walk
and an 08:15 feeding won't be flagged. That's reasonable for a v1 planner because
routine pet tasks sit on round time slots, and exact-match still catches the
common double-booking mistake without computing task end times.

---

## 3. AI Collaboration

**a. How you used AI**

I used AI as a design partner and pair-programmer: brainstorming the class
breakdown and UML, scaffolding class skeletons from the diagram, and then
implementing the scheduling logic in small increments (sorting, budget filtering,
recurrence, conflict detection). The most helpful prompts were specific ones that
named a method and its contract — e.g., "sort by priority then time, then keep
what fits the budget" — rather than vague "build a scheduler" requests.

**b. Judgment and verification**

I did not accept suggestions blindly. After each phase I ran `main.py` and
`pytest`, and I read the schedule output to confirm the ordering and the budget
math matched what I intended. When a suggestion introduced a new field or method,
I checked it against the UML and asked whether the added complexity was worth it.

---

## 4. Testing and Verification

**a. What you tested**

I tested the core promises of the app: task completion, adding a task to a pet,
collecting tasks across pets, budget filtering, exclusion of completed tasks,
chronological sorting, recurrence roll-forward (and a no-duplicate guard), and
conflict detection (both a positive case and a negative case). These matter
because they cover both correct data flow and correct scheduling decisions —
the two things the app is judged on.

**b. Confidence**

Fairly confident: 11 focused tests pass and the CLI demo behaves as expected.
If I had more time I'd test the `due_date=None` recurrence fallback (which uses
today's date), zero/empty-budget days, and eventually interval-overlap conflict
detection.

---

## 5. Reflection

**a. What went well**

I'm most satisfied with the clean separation between the logic layer
(`pawpal_system.py`) and the UI (`app.py`). Because all state lives in a single
`Owner` object, the Streamlit app stayed thin and the same classes power both the
CLI demo and the tests.

**b. What you would improve**

I'd add persistence (save/load to JSON) so data survives a restart, and upgrade
conflict detection to interval-overlap so partial time clashes are caught.

**c. Key takeaway**

The most important thing I learned is that AI accelerates *generating* and
*scaffolding*, but architecture is a series of judgment calls — what to keep
simple, what earns its complexity, and verifying it actually works. One concrete
example: AI proposed an advanced interval-overlap conflict detector, but I chose
the simpler exact-time-match version because it was easier to read, test, and
explain, and it caught the common mistake. Owning those decisions — and verifying
them with tests and real runs — is what the "lead architect" role is really about.
