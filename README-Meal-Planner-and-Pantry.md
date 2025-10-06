# Meal Planner + Pantry Tracker (CLI)

**Goal:** Manage recipes and pantry; plan weekly menus; log daily progress so pantry and weekly goals stay in sync. Python‑only, local‑first.

---

## Scope & Must‑Have Features
- Import recipes (YAML/JSON); scale servings; tags.
- Pantry CRUD with quantities/units and optional expiry.
- Weekly plan: assign recipes to meal slots (breakfast/lunch/dinner).
- Shopping list from plan **minus** pantry; export CSV/Markdown.
- Daily log: mark cooked, adjust portions; leftovers return to pantry.
- Reports: pantry low/expiry, weekly goal progress, waste estimate.

## Core Entities
- **Recipe**: name, servings, ingredients[item, qty, unit], steps, tags[]
- **PantryItem**: name, qty, unit, expiry?, tags[]
- **Plan**: week_start, slots[day→meal→recipe], targets?
- **ShoppingList**: derived items
- **LogEntry**: date, meal, cooked?, leftovers qty

## Design Patterns (Required)
- **Template Method**: recipe parsing/rendering; shopping list build pipeline.
- **Strategy**: plan generation variants (balanced tags, leftovers‑first, budget‑first).
- **Observer**: pantry alerts (low/expiry) on plan/log updates.
- **Repository**: recipes, pantry, plans, logs.
- **State**: meal status (planned → cooked → logged).

## Team Roles
- **Tech Lead**: data contracts for ingredients/units, strategy choice; only person to ask instructor.
- **Backend**: parsers, repositories, reconciliation of plan ↔ pantry ↔ logs.
- **Frontend/CLI**: commands for plan/recipe/list; friendly tables and exports.
- **Tester**: fixtures (recipes/pantry), tests for list generation, leftovers, reports.

## Acceptance Criteria
- Shopping list accurately subtracts pantry and respects scaled servings.
- Logging a cooked meal decrements pantry; leftovers increase it.
- Low/expiry report lists items with dates and thresholds.
- Export renders readable weekly plan and shopping list.

## Sample CLI
```bash
meal recipes import recipes/*.yml
meal pantry add "Tomato" --qty 6 --unit pcs --expiry 2025-10-01
meal plan create --week 2025-09-22 --meals mon:dinner="Chili" tue:dinner="Pasta"
meal list build --week 2025-09-22 > shopping.csv
meal cook --date 2025-09-22 --meal dinner --leftovers 2
meal pantry report --low --expiry
```

## Milestones (2 Weeks)
- **D1–3:** models + import/export; pantry ops.
- **D4–6:** plan & Strategy; shopping list.
- **D7–9:** daily log + Observer alerts.
- **D10–12:** reports + CLI polish + docs.
- **D13–14:** tests + demo.

## Stretch Goals
- Nutrition fields; simple substitute suggestions.

---

## Common Stack & Layout
```bash
app/
  cli/              # commands (Command pattern)
  domain/           # entities, value objects
  services/         # Facade services (ReportingService, AccessService)
  infra/            # repos (Repository pattern), storage, crypto adapters
  rules/            # Strategy/Factory implementations
  events/           # Observer bus + handlers (audit, alerts)
  tests/            # unit + scenario tests
```
