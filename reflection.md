# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

The initial UML included five classes: `Priority` (enum), `Task`, `Pet`, `Owner`, `DailyPlan`, and `Scheduler`. Each class had a single responsibility:

- `Task` — holds one activity's data (title, duration, priority)
- `Pet` — groups tasks for one animal
- `Owner` — aggregates pets and exposes all tasks
- `DailyPlan` — a value object representing the output of scheduling
- `Scheduler` — the decision-making engine

`Task` and `Pet` were designed as dataclasses from the start to eliminate boilerplate `__init__` code and get `__repr__` for free.

**b. Design changes**

Three significant changes occurred during implementation:

1. **`DailyPlan` was removed.** It turned out to be a thin wrapper around a list. Replacing it with `list[tuple[Pet, Task]]` was simpler and more Pythonic — the Scheduler just returns the pairs directly.

2. **`Task` gained `start_time` and `frequency`.** These were not in the initial design. Adding `start_time` (a `"HH:MM"` string) unlocked time-based sorting and conflict detection. Adding `Frequency` (ONCE / DAILY / WEEKLY) enabled recurring task logic without requiring a separate `RecurringTask` subclass.

3. **`Scheduler` constructor simplified from `(owner, pet, tasks)` to `(owner)`.** The original constructor accepted redundant arguments — `owner` already holds all pets and tasks. Removing the extras made every call site cleaner.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers two constraints:

- **Time budget** (`Owner.available_minutes`): tasks are greedily packed until no more fit.
- **Priority** (`Priority.HIGH / MEDIUM / LOW`): tasks are sorted HIGH → MEDIUM → LOW before the greedy loop runs, so the most important tasks are selected first.

Priority was chosen as the primary constraint because a pet owner's most urgent tasks (medication, feeding) must happen regardless of time. Time budget acts as a secondary hard limit to keep the plan realistic.

**b. Tradeoffs**

*Tradeoff: priority-first selection vs. time-aware selection.*

`build_schedule()` selects tasks by priority, then `sort_by_time()` re-orders the display. This means a HIGH-priority task at 17:00 will be selected over a MEDIUM task at 08:00, even though the 08:00 task happens first in the day. The final display looks correct (sorted by time), but the selection logic is not truly time-aware.

This is reasonable for the current scenario: the owner's primary question is "what is most important today?" not "what fits neatly into my calendar?" A future improvement would merge priority and time into a single time-window-aware scheduler.

---

## 3. AI Collaboration

**a. How you used AI**

AI was used in three distinct ways across the project:

- **Design brainstorming (Phase 1):** Asked for suggestions on class responsibilities and which Python patterns (dataclasses, enums) fit best. The AI correctly identified that `DailyPlan` might be over-engineering for a small project.
- **Algorithm generation (Phase 3):** Used inline chat to draft `sort_by_time()` with a `lambda` key and `datetime.strptime`. The suggestion to use `datetime.max` as the sentinel for untimed tasks was a clean pattern that would have taken longer to find independently.
- **Test planning (Phase 4):** Asked for a list of edge cases for "a pet scheduler with sorting and recurring tasks." The AI surfaced the "completed task conflict false-positive" edge case — where a done task and its auto-generated next occurrence share the same `start_time` — which led to adding the `not t.completed` guard in `detect_conflicts()`.

The most useful prompt form was: *"Based on [specific method/class], what edge cases should I test?"* — it produced concrete, actionable answers rather than generic advice.

**b. Judgment and verification**

When asked to implement conflict detection, the AI initially suggested raising a `ValueError` when a conflict was found. This was rejected because crashing the program is the wrong behavior for a UI app — the user needs a warning, not a crash. The method was changed to return `list[str]` warnings so the caller (UI or CLI) decides how to present them.

The AI's suggestion was verified by asking: "What happens to the Streamlit app if this raises an exception mid-render?" The answer made the problem obvious.

---

## 4. Testing and Verification

**a. What you tested**

The 22-test suite covers five groups:

1. **Task basics** — `mark_complete()` side effects, ONCE returns `None`, `add_task` count
2. **Recurrence** — DAILY/WEEKLY produce a new Task; fields are preserved; pet task count after re-adding
3. **Scheduler core** — time budget, completed skipped, priority order, empty pets, no pets
4. **Sorting** — chronological HH:MM order; untimed tasks sink to the end
5. **Conflict detection** — overlap detected; same start time flagged; sequential tasks not flagged; completed and untimed tasks excluded

These tests were important because the algorithmic methods are interdependent. A bug in `sort_by_time` would silently produce a correct-looking but wrong schedule. Tests made each method's contract explicit.

**b. Confidence**

**★★★★☆** — high confidence in the individually tested behaviors. The one unverified gap is integration: `build_schedule()` uses priority order, but the final display uses `sort_by_time()`. An integration test that checks the *combined* output (selected by priority, displayed by time) would close that gap.

Next edge cases to test:
- Owner with `available_minutes=0` (should schedule nothing)
- Task whose `duration_minutes` exactly equals `available_minutes` (boundary case)
- Conflict between tasks on *different* pets at the same time

---

## 5. Reflection

**a. What went well**

The layered architecture (data classes → logic layer → UI) paid off in Phase 5. Because `app.py` only calls `Scheduler` methods and never manipulates `Task` or `Pet` internals directly, every UI improvement was a matter of calling an already-tested method and choosing the right Streamlit component to display the result. No business logic had to move into the UI.

**b. What you would improve**

The scheduler's priority-first selection should be replaced with a time-window-aware algorithm that respects `start_time` during selection, not just display. Tasks with a fixed time (e.g., medication at 08:00) should be anchored to that slot first; then remaining time should be filled with priority-ordered tasks.

**c. Key takeaway**

AI is most valuable as a *reviewer and edge-case generator*, not as an architect. Asking "what edge cases should I test for this method?" consistently produced better results than asking "write this method for me." The best AI-assisted sessions in this project were the ones where the human wrote the design and used AI to stress-test it — not the other way around. Keeping separate chat sessions per phase enforced this discipline: each session had a clear scope, which prevented AI suggestions from one phase polluting the design decisions of another.
