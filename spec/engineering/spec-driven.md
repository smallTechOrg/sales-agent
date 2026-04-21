# Spec-Driven Development

**Scope:** entire repository.

The spec is the source of truth. Code is a mechanical translation of the spec.

## The rule

1. **Spec first.** Before writing or changing code, write or update the relevant
   spec file. If there is no spec file for what you are building, create one.
2. **Code second.** Once the spec is clear and reviewed, translate it into code.
3. **Drift is a bug.** If code diverges from the spec, the spec wins — fix the
   code, or update the spec and note the intentional deviation.

## What counts as a spec change

- Adding a new behaviour the product did not previously have.
- Changing how an existing behaviour works.
- Removing a behaviour.
- Renaming a concept across the system.

## What does NOT require a spec change first

- Bug fixes that make code match the existing spec.
- Refactors that do not change observable behaviour.
- Test additions.

## How to find the right spec file

```
spec/
  product/   ← what the system does
  engineering/ ← how contributors write code
```

If the change affects what the system does → `product/`.
If the change affects how contributors write code → `engineering/`.
