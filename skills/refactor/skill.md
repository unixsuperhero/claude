---
name: refactor
description: >
  Apply refactoring principles to code. Use when the user asks to refactor, clean up,
  improve structure, reorganize, or apply design principles to code. Also use when
  reviewing code for composition, abstraction layers, naming conventions, or
  object-oriented design issues. Covers Ruby/Rails (partners, customers-backend),
  TypeScript/React (IPP), and general principles.
tools: Read, Edit, Glob, Grep, Bash
---

# Refactoring Principles

Apply these principles to the code in the current context. The user may provide additional
context or a scope: $ARGUMENTS

---

## Scope Detection

The user can specify a scope to limit which files to refactor:

- **`scope:dirty`** — Only refactor files with uncommitted changes. Run:
  `git diff --name-only && git diff --name-only --cached`
- **`scope:branch`** — Only refactor files changed since branch diverged from base. Run:
  `git merge-base HEAD main` then `git diff --name-only <merge-base>..HEAD`
- **`scope:pr`** — Same as `scope:branch`; use for pre-PR cleanup

When a scope is specified:
1. Run the appropriate git commands to determine the relevant files
2. Read only those files
3. Apply refactoring principles only to those files

If no scope is specified, apply refactoring to whatever code the user indicates.

---

## Instacart-Specific Patterns

### Ruby/Rails (partners, customers-backend)

**Run validation after refactoring:**
```bash
# Lint changed files
bin/rubocop --parallel $(git diff --name-only HEAD | grep '\.rb$' | tr '\n' ' ')

# Run affected specs
bin/rspec <path/to/spec_file>

# For model/service changes, run the spec for the class being changed
bin/rspec spec/models/my_model_spec.rb
bin/rspec spec/services/my_service_spec.rb
```

**Rails-specific refactoring targets:**
- Move logic out of controllers into service objects or POROs
- Replace fat models (models > 300 lines) with service objects and value objects
- Use `scope` in models instead of class methods for chainable queries
- Use `attr_reader` with frozen `initialize` for value objects (no `attr_writer`)
- ActiveRecord callbacks: prefer service objects over `before_save`/`after_create` for
  complex logic — callbacks are hard to test and hide behavior
- Use `with_lock` or `update_counters` for concurrent state changes
- Prefer `find_each` over `all.each` for large datasets
- Use `includes`/`preload`/`eager_load` to eliminate N+1 queries

**Service object conventions at Instacart:**
- Live in `app/services/` or under a relevant namespace
- Single public method (usually `call` or `perform`)
- Instantiate with context, call with operation arguments
- Return a result object or raise on error — avoid returning `nil`

### TypeScript/React (IPP - Instacart Partner Platform)

**Run validation after refactoring:**
```bash
# Lint
yarn lint --fix <path/to/file>
# or
npx eslint --fix <path/to/file>

# TypeScript check
yarn tsc --noEmit

# Tests
yarn test <path/to/test-file>
# or
yarn jest <path/to/test-file>
```

**React-specific refactoring targets:**
- Extract reusable logic into custom hooks (`use*`)
- Move non-React logic out of components into plain functions or classes
- Separate data-fetching (hooks/queries) from presentation (components)
- Break large components (> 200 lines) into smaller, focused components
- Use React Query for server state; avoid duplicating server state in local state
- Use discriminated unions for component prop types when state varies significantly
- Colocate types with the code that owns them; avoid giant `types.ts` files
- Prefer named exports over default exports for easier refactoring

### When to Break Into Multiple PRs

Break a refactor across multiple PRs when:
- The diff is > 400 lines and touches > 5 files
- The rename/move makes the first PR hard to review
- You're changing both the interface AND callers simultaneously
- The refactor involves a database migration alongside code changes

**Split strategy:**
1. PR 1: Add the new abstraction (new class/file), existing code untouched
2. PR 2: Migrate callers to use the new abstraction
3. PR 3: Delete the old code

---

## Core Philosophy

Refactor toward **composable, reusable code** by separating concerns across clear
abstraction layers. Think "functional core, imperative shell" (Gary Bernhardt).

**ALMOST NEVER:** Use inheritance or mixins.
**ALMOST ALWAYS:** Favor composition.
**ALWAYS:** Check references after renaming classes or changing method signatures
(name, args, return value) and update anything that would break.

### Composition Over Mixins

When multiple classes share behavior, **do not** extract it into a mixin/module.
Instead, build a **generic, reusable class** and have each specific class compose it.

---

## 1. Data-First

**Separate data from behavior.**

- Extract **value objects** that represent pure data
- Prefer methods that **return data** over methods that perform actions
- Data should flow through the system; behavior operates on data at boundaries
- When you see a method doing both computation AND side-effects, split it

**Goal:** Lower-level abstractions should be more **declarative** with **referential
transparency** — a method name should consistently represent the same value.

---

## 2. Interface Over Implementation

**The interface IS the design.**

Requirements for composable objects:
- **No side-effects** in data/computation methods
- **Single atomic operation** per method
- Methods expose information/possibilities, not workflows
- **Sane defaults** for convenience — infer context when not provided

---

## 3. Levels of Abstraction

### Low-Level (Data & Computation)
- **Atomic operations only** — one thing per method
- **Expose possibilities** — let callers compose
- **Pure functions** where possible

### Mid-Level (Composition)
- Compose low-level objects
- Expose **domain-relevant data**
- Still mostly side-effect free

### High-Level (Human/Business)
- **Orchestrates** mid/low level objects
- **Side-effects happen here** at the boundary
- **NEVER mix levels** — a high-level class should never do low-level work; delegate instead

**Where high-level code lives:**
- Rails: controller actions and service objects the controller calls
- Background jobs: the `perform` method
- TypeScript: API route handlers, top-level React data hooks

### Service Object Pattern

Service objects are **high-level only**. They should not do any heavy lifting themselves —
they orchestrate and delegate to mid/low-level abstractions.

**Service objects should:**
- Coordinate workflow between objects
- Handle side-effects at boundaries
- Read like a high-level description of what happens

**Service objects should NOT:**
- Contain loops, regex, or data manipulation
- Know implementation details of how things work
- Mix abstraction levels

---

## 4. Separate Presentation from Application

**Formatting and display are not business logic.**

Presentation logic: string formatting, output structure, user-facing messages.
Application logic: domain rules, calculations, state transitions.

Keep them in separate layers. Application code returns data; presentation code formats it.

---

## 5. Don't Mix Abstraction Levels

**Each method/class should operate at ONE level of abstraction.**

Signs you're mixing levels:
- A method has both loops/regex AND service calls
- Reading the method requires constant context-switching
- Some lines describe "what" while others describe "how"

---

## 6. Naming: Nouns Over Verbs

**Methods should be named for what they return, not what they do.**

In mid/low-level code, avoid verbs unless the method's **only purpose** is to mutate
internal state. Name methods after **what the return value IS**:

```ruby
# Bad: verb-based naming
def calculate_total(order)  # returns a number

# Good: noun-based naming
def total   # returns the total
```

**Class naming:** avoid actor/verb naming (`TaskStarter`, `OrderProcessor`).

1. **First choice:** Look for an existing object that should own this behavior
   - `TaskStarter` → Add `Task#start`
2. **If logic is complex:** Extract to a helper named after what it **represents**
   - `PriceCalculator` → `Pricing` or `CartPricing`

---

## 7. File Organization

- Name files after the main class/module they define
- Each file should define one primary class, with inner classes in subdirectories
- When renaming files, rename the inner class folder too
- Promote inner classes used throughout the codebase to an accessible namespace

**Alternate Constructors** — use `from_` prefix for different construction sources:
```ruby
Prompt.from_file(path)
Prompt.from_text(text)
Prompt.new(already_parsed_doc)
```

---

## 8. Avoid Primitive Obsession

**Don't pass raw primitives when a domain concept exists.**

Signs of primitive obsession:
- The same string/integer format is validated or parsed in multiple places
- A hash with specific expected keys is passed between methods
- Methods take 3+ primitives that together represent one concept

**Layered Value Objects pattern:** When a service has several private methods clustered
around "look up and interpret records by key", extract two classes:
- **Item** — wraps one record, owns domain semantics (e.g., what "present?" means)
- **Collection** — owns the index, delegates to item; never calls raw AR methods directly

Build the index with `each_with_object` wrapping items (not `index_by` storing raw records).

---

## 9. DRY: Don't Repeat Yourself

### Search Before Extracting
Before creating something new, search for something that already exists.

### Extract to Eliminate Duplication
Two occurrences is usually enough to extract. Three or more: extract immediately.

### When NOT to DRY
**Incidental similarity** — two things that look alike now but represent different concepts
— should stay separate. Only DRY up true conceptual duplication.

---

## Refactoring Checklist

1. **Is data mixed with behavior?** Extract value objects / computation methods
2. **Does this method have side-effects AND return data?** Split it
3. **Is this method doing multiple things?** Break into atomic operations
4. **Are there conditionals in low-level code?** Push decisions up to callers
5. **Is low-level code making business decisions?** Move logic up the stack
6. **Is high-level code doing data manipulation?** Extract to lower layer
7. **Is the interface clear?** Method name, args, return value should be obvious
8. **Can this be composed?** If not, it might be doing too much
9. **Is presentation mixed with logic?** Separate formatting from domain rules
10. **Does this method mix abstraction levels?** Extract details to helpers
11. **Does this method have a verb name but return data?** Rename to what it returns
12. **Is this class named like an actor (TaskStarter)?** Move to the object it acts on
13. **Does this method belong here?** If not, extract to a value object that owns the data
14. **Is this file named after its main class?** Rename to match
15. **Are there multiple top-level classes in one file?** Extract each to its own file
16. **Does this class need to be constructed from different sources?** Add `from_*` constructors
17. **Is this using inheritance?** Refactor to use composition instead
18. **Is this service object doing heavy lifting?** Extract to mid/low-level classes
19. **Are primitives being passed around for a domain concept?** Extract a value object
20. **Before extracting a method, did you search for an existing one that already does this?**
21. **Does the same 2+ line block appear in multiple methods?** Extract to a shared method
22. **Are there parallel methods differing only in one variable?** Make it a parameter
23. **Does similar-looking code represent the same concept, or just the same accident?** Only DRY true duplication
24. **Are there 3+ private methods clustered around "look up a record by key"?** Extract item + collection value objects

---

## Apply Now

Look at the code in context and identify refactoring opportunities based on these principles.
Prioritize changes that:
1. Separate data from behavior
2. Create clear, composable interfaces
3. Respect abstraction boundaries
4. Keep presentation separate from application logic
5. Maintain consistent abstraction level within each method
6. Use noun-based naming
7. Organize files properly
8. Extract value objects for repeated primitive patterns

After identifying opportunities, explain your reasoning, then make the changes.
If there are many changes, ask which to prioritize first.
