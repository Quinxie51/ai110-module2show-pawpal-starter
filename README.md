# PawPal+ (Module 2 Project)

**PawPal+** is a Streamlit app that helps a pet owner plan daily care tasks across multiple pets — intelligently sorted, conflict-checked, and aware of recurring schedules.

---

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

---

## Features

| Feature | Description |
|---|---|
| **Priority scheduling** | Greedy scheduler fills the day with HIGH → MEDIUM → LOW tasks first, staying within the owner's time budget |
| **Sort by time** | Schedule is displayed in `HH:MM` chronological order using `datetime.strptime` for correct sorting (avoids lexicographic errors) |
| **Conflict detection** | Pairwise overlap check — warns when two tasks' time windows intersect (`start_A < end_B and start_B < end_A`) |
| **Recurring tasks** | Tasks marked `DAILY` or `WEEKLY` auto-generate their next occurrence when completed via `mark_complete()` |
| **Filtering** | `Scheduler.filter_tasks()` returns tasks by pet name and/or completion status |
| **Live conflict banner** | Conflict warnings appear in the UI as tasks are added, before the schedule is generated |
| **Mark complete in UI** | Dropdown lets you mark any pending task done; recurring next-occurrence is added automatically |

---

## Project Structure

```
pawpal_system.py    # Core logic: Task, Pet, Owner, Scheduler, Priority, Frequency
app.py              # Streamlit UI — wired to the logic layer
main.py             # CLI demo script
models.py           # Initial dataclass stubs (design artifact)
uml_final.md        # Final Mermaid UML class diagram
tests/
  test_pawpal.py    # 22 pytest tests
reflection.md       # Design and AI collaboration reflection
requirements.txt
```

---

## Getting Started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run the app

```bash
streamlit run app.py
```

### Run the CLI demo

```bash
python main.py
```

---

## Testing PawPal+

```bash
python -m pytest
```

The test suite (`tests/test_pawpal.py`) covers **22 behaviors** across five groups:

| Group | Tests | What's verified |
|---|---|---|
| Task basics | 3 | `mark_complete()` flips flag; ONCE returns `None`; `add_task` increments count |
| Recurrence | 4 | DAILY/WEEKLY return next task; fields preserved; caller adds it back correctly |
| Scheduler — schedule | 5 | Time budget; completed tasks skipped; HIGH before LOW; empty pets; no pets |
| Sorting | 2 | Chronological HH:MM order; untimed tasks go last |
| Filtering | 3 | By pet name; completed-only; pending-only |
| Conflict detection | 5 | Sequential (no false positive); overlap; exact same start; completed ignored; untimed ignored |

**Confidence: ★★★★☆** — all named behaviors are covered on happy paths and key edge cases.

---

## Smarter Scheduling

The algorithmic layer adds intelligence beyond a simple list:

- **Sorting by time** uses Python's `sorted()` with a `lambda` key and `datetime.strptime` so that `"09:00"` correctly sorts before `"10:00"` (plain string comparison would fail).
- **Conflict detection** uses a lightweight O(n²) pairwise scan that returns warning strings instead of raising exceptions — the UI displays warnings without crashing.
- **Recurring tasks** return the next `Task` instance from `mark_complete()` so the caller (Pet or UI) decides where to place it — clean separation of concerns.
- **Tradeoff:** `build_schedule()` is priority-based, not time-based. A HIGH priority task at 17:00 will be scheduled before a MEDIUM task at 08:00. `sort_by_time()` re-orders the final display, but the selection itself is priority-first.

---

## 📸 Demo

<a href="/course_images/ai110/pawpal_screenshot.png" target="_blank">
  <img src='/course_images/ai110/pawpal_screenshot.png' title='PawPal App' width='' alt='PawPal App' class='center-block' />
</a>

---

## Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
