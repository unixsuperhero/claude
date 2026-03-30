---
name: encapsulate
description: >
  Design and write encapsulated value objects: classes that wrap data, expose everything
  through clean one-liner methods, and compose into item + collection pairs. Use when
  extracting logic from service objects or inner classes, designing new domain objects,
  reviewing code for encapsulation quality, or when told to "wrap this" / "make a class
  for this" / "extract this". Emphasizes Ruby/Rails patterns but the principles apply broadly.
tools: Read, Edit, Write, Glob, Grep, Bash
---

# Encapsulation

Encapsulate data. Expose it through methods. One method, one thing. $ARGUMENTS

---

## The Canonical Pattern

This is the template every value object should follow. Read it once and internalize it.

```ruby
class PendingAttribute
  # --- 1. Alternate constructors first (from_ prefix) ---

  def self.from_form(attribute, onboarding_form)
    name = attribute[:name]
    new(
      attribute: attribute,
      onboarding_attribute: onboarding_form.attribute_by_name(name),
      approval_request: onboarding_form.approval_request_map[name],
      all_stored_values: onboarding_form.approval_request_map.transform_values(&:deserialized_attribute_value),
      form_type: onboarding_form.form_type,
    )
  end

  # --- 2. attr_reader for every constructor argument, no exceptions ---

  attr_reader :name, :value, :onboarding_attribute, :approval_request, :all_stored_values, :form_type

  # --- 3. Constructor stores args only, nothing else ---

  def initialize(attribute:, onboarding_attribute:, approval_request:, all_stored_values:, form_type:)
    @name                = attribute[:name]
    @value               = attribute[:value]
    @onboarding_attribute = onboarding_attribute
    @approval_request    = approval_request
    @all_stored_values   = all_stored_values
    @form_type           = form_type
  end

  # --- 4. Data accessors — one line, no logic ---

  def stored_value         = approval_request&.deserialized_attribute_value
  def raw_value            = approval_request&.attribute_value
  def expected_data_type   = onboarding_attribute&.data_type
  def data_type            = value.class

  # --- 5. Predicate methods — boolean, one line ---

  def admin_form?          = form_type == ADMIN
  def type_valid?          = onboarding_attribute&.valid_data_type?(value) || false
  def should_validate?     = required? || stored_value_present?

  # --- 6. Computed methods — may be multi-line, but single concern ---

  def stored_value_present?
    sv = stored_value
    return true if sv == false  # false is a valid boolean value
    sv.present?
  end

  def required?
    return true if onboarding_attribute&.required?
    satisfied_required_scenarios.any?
  end

  def satisfied_required_scenarios
    scenarios = onboarding_attribute&.required_if || []
    scenarios.select do |scenario|
      scenario.all? { |attr_name, expected| expected == all_stored_values[attr_name.to_s] }
    end
  end

  # --- 7. Error predicates — compose the above, never reach into raw data ---

  def missing_error?   = required? && !stored_value_present?
  def invalid_error?   = should_validate? && !type_valid?
  def invisible_error? = !admin_form? && !visible_on_form?
end
```

### Why every rule exists

| Rule | Reason |
|------|--------|
| `attr_reader` for every arg | Object travels to other classes; without readers, context is gone |
| Constructor stores only | Side effects (DB, file, parsing) belong in lazy methods or `from_*` constructors |
| `from_` prefix | Signals "different input source" without polluting `initialize` |
| One-liners for derived data | Reads like a spec; easy to scan, easy to test |
| Error predicates compose others | The predicate layer is free of implementation — change `required?` and errors update automatically |

---

## Item + Collection

When a service has 3+ private methods clustered around "look up a record by name and
interpret it", extract two classes: one item, one collection.

```
Private methods in the service:        →   Where they go:
  build_index                               Collection constructor
  value(name)                               Collection#value → Item#value
  present?(name)                            Collection#present? → Item#present?
  required?(name)                           Collection#required? → Item#required?
  visible?(name)                            Collection#visible? → Item#visible?
```

**The Collection:**
- Owns the index (built once at construction)
- Delegates all semantics to Item — never calls raw AR methods directly
- Uses `each_with_object` to build the index as Item instances, not `index_by` with raw records

```ruby
class PendingAttributes
  include Enumerable

  def self.from_form(attributes, onboarding_form)
    # Compute shared data ONCE — don't let each Item recompute it
    all_stored_values = onboarding_form.approval_request_map
                          .transform_values(&:deserialized_attribute_value)

    items = attributes.map do |attribute|
      name = attribute[:name]
      PendingAttribute.new(
        attribute:            attribute,
        onboarding_attribute: onboarding_form.attribute_by_name(name),
        approval_request:     onboarding_form.approval_request_map[name],
        all_stored_values:    all_stored_values,
        form_type:            onboarding_form.form_type,
      )
    end

    new(items)
  end

  attr_reader :items

  def initialize(items) = @items = items
  def each(&block)      = @items.each(&block)
end
```

**The Item:**
- Wraps one record, owns all domain logic for that record
- Never reaches back into the collection or the service
- Every piece of data it needs is passed in at construction time

**Decision: when to extract item vs collection first?**
- Start with the item. Get the interface right.
- Add the collection when you need to build many items from a shared source and want
  to avoid redundant lookups.

---

## One-Liner Philosophy

If a method body fits on one line AND reads clearly, write it on one line.
Use `=` syntax for these:

```ruby
# Good — one-liners are easy to scan
def name           = @name
def total          = subtotal - discount
def admin?         = role == ADMIN
def missing?       = required? && !present?
def display_name   = "#{first_name} #{last_name}".strip

# Multi-line is fine when there's branching or a guard
def present?
  return true if value == false  # false is a valid boolean
  value.present?
end
```

A class of 8 one-liners reads like a spec sheet for the object. That's the goal.

### Don't use one-liner syntax when:
- There's more than one expression (use `end`)
- The line exceeds ~100 characters
- There's a guard clause (`return early if ...`)

---

## Constructor Rules

**Constructors store. Methods compute.**

```ruby
# Bad: constructor does work
def initialize(record)
  @record = record
  @index = build_index(record)  # side effect
  @total = record.items.sum(&:price)  # computation
end

# Good: constructor stores, methods compute lazily
def initialize(record)
  @record = record
end

def index
  @index ||= build_index(@record)
end

def total
  @total ||= @record.items.sum(&:price)
end
```

**`attr_reader` for everything.** Even if you don't expect to read it back today.
When the object gets passed to another class, readers are the only window into it.

**Alternate constructors use `from_` prefix:**

```ruby
class Order
  def self.from_params(params)   = new(id: params[:id], ...)
  def self.from_webhook(payload) = new(id: payload["orderId"], ...)
  def self.from_csv_row(row)     = new(id: row[0], ...)
end
```

---

## Naming: Nouns, Not Verbs

Methods are named for **what they return**, not what they do.

```ruby
# Bad (verb) → Good (noun)
def calculate_total   → def total
def resolve_user      → def user
def fetch_value       → def value
def check_visibility  → def visible?
def determine_tier    → def tier
```

**Predicates end in `?`** and return a boolean. They compose freely:

```ruby
def invalid_error? = should_validate? && !type_valid?
```

**Classes are named for things, not actors:**

```ruby
# Bad (actor)        → Good (thing)
TaskStarter          → Task (add #start) or Task::Prerequisites
PriceCalculator      → Pricing or CartPricing
AttributeValidator   → AttributeValidation or PendingAttribute
```

---

## Separation of Concerns

**Value object:** owns its data, exposes it cleanly, no side effects. This is where
one-liner methods live.

**Service object:** orchestrates. Calls value objects, calls repositories, triggers
side effects. Should read like a high-level description:

```ruby
class UpdateAttributesService
  def perform
    # No computation here — delegate everything
    update_approval_requests
    validate_pending_attributes   # <- calls into PendingAttributes
    propagate_downstream if should_propagate?
  end

  private

  def validate_pending_attributes
    pending_attributes.each do |attr|
      raise MissingValueError if attr.missing_error?
      raise InvalidTypeError  if attr.invalid_error?
      raise InvisibleError    if attr.invisible_error?
    end
  end

  def pending_attributes
    @pending_attributes ||= PendingAttributes.from_form(attributes, onboarding_form)
  end
end
```

**Service objects should NOT:**
- Have loops doing data manipulation
- Call `.deserialized_attribute_value` directly
- Know what "present?" means for an attribute

---

## File Organization

One class per file. File named after the class. Inner classes in a subdirectory.

```
app/services/whitelabel_sites/
  onboarding_form_service.rb            # OnboardingFormService
  onboarding_form_service/
    pending_attribute.rb                # OnboardingFormService::PendingAttribute
    pending_attributes.rb               # OnboardingFormService::PendingAttributes
```

---

## Checklist

When designing or reviewing an object, ask:

1. **Does `initialize` do anything besides `@x = x`?** Move side effects to lazy methods
2. **Is there an `attr_reader` for every `initialize` argument?** Add them
3. **Are methods named for what they return?** Rename verbs to nouns
4. **Do any methods return data AND cause side effects?** Split them
5. **Are there 3+ private methods around "look up a record by key"?** Extract item + collection
6. **Does the collection compute shared data once?** Move it to the `from_*` constructor
7. **Does the item reach back into the service or collection?** Pass the data in at construction instead
8. **Are there one-liners that could use `= ` syntax?** Clean them up
9. **Is this class named like an actor (`*er`, `*or`, `*Manager`)?** Rename to the thing it represents
10. **Does this service object do computation?** Extract a value object and delegate

---

## Apply Now

Look at the code in context. Find:
- Private methods that cluster around one record/concept → extract a value object
- Hashes passed between methods that have a name → make them a class
- Methods that do lookup + interpretation → separate the lookup (collection) from the interpretation (item)
- Constructors with side effects → move them to lazy methods
- Verb method names that return data → rename to nouns

Make the changes. Lint when done (`RBENV_VERSION=3.3.7 script/lint <files>`).
