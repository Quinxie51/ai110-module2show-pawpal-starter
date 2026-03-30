# PawPal+ — Final UML Class Diagram

```mermaid
classDiagram
    class Priority {
        <<enumeration>>
        LOW
        MEDIUM
        HIGH
    }

    class Frequency {
        <<enumeration>>
        ONCE
        DAILY
        WEEKLY
    }

    class Task {
        +str title
        +int duration_minutes
        +Priority priority
        +str|None start_time
        +Frequency frequency
        +bool completed
        +mark_complete() Task|None
        +is_high_priority() bool
        +__str__() str
    }

    class Pet {
        +str name
        +str species
        +list~Task~ tasks
        +add_task(task: Task) None
        +get_tasks() list~Task~
        +__str__() str
    }

    class Owner {
        +str name
        +int available_minutes
        +list~Pet~ pets
        +add_pet(pet: Pet) None
        +get_all_tasks() list~tuple~
    }

    class Scheduler {
        +Owner owner
        +build_schedule() list~tuple~
        +sort_by_time(pairs) list~tuple~
        +filter_tasks(pet_name, completed) list~tuple~
        +detect_conflicts() list~str~
        +print_schedule() None
        -_all_tasks_by_priority() list~tuple~
    }

    Task --> Priority : uses
    Task --> Frequency : uses
    Pet "1" o-- "0..*" Task : contains
    Owner "1" o-- "1..*" Pet : manages
    Scheduler --> Owner : reads from
    Scheduler ..> Task : schedules
    Scheduler ..> Pet : references
```

## Relationships

| Relationship | Type | Description |
|---|---|---|
| `Task` → `Priority` | Association | Each task holds one Priority enum value |
| `Task` → `Frequency` | Association | Each task holds one Frequency enum value |
| `Pet` ◇── `Task` | Aggregation | Pet owns a list of Tasks; tasks can exist without a pet |
| `Owner` ◇── `Pet` | Aggregation | Owner manages a list of Pets |
| `Scheduler` → `Owner` | Dependency | Scheduler reads owner data to build a plan |
| `Scheduler` ··> `Task`/`Pet` | Usage | Scheduler returns (Pet, Task) pairs but does not own them |

## Changes from initial design

| Initial | Final | Reason |
|---|---|---|
| `DailyPlan` class | Removed | Replaced by `list[tuple[Pet, Task]]` — simpler, no extra wrapper needed |
| `Task` had no `start_time` | Added `start_time: str\|None` | Required for time-based sorting and conflict detection |
| `Task` had no `frequency` | Added `frequency: Frequency` | Required for recurring task logic |
| `mark_complete()` returned `None` | Returns `Task\|None` | Caller receives the next occurrence for recurring tasks |
| `Owner` had `add_task()` | Removed | Tasks belong to Pets, not directly to Owner |
| `Scheduler` took `(owner, pet, tasks)` | Takes only `owner` | Owner already holds all pets and tasks — simpler API |
