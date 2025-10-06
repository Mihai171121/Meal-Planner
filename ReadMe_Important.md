# Meal Planner & Pantry Tracker – ESENȚIAL

Acest fișier este un rezumat scurt cu cele mai importante informații pentru a înțelege, porni, modifica și extinde proiectul.

---
## 1. Scop
Planifică mesele săptămânale, gestionează cămara (ingrediente + expirări), calculează lista de cumpărături și oferă sumar nutrițional + alerte (stoc scăzut, expirare apropiată).

---
## 2. Lansare Rapidă
```bash
python -m venv .venv
.venv/Scripts/activate        # Windows
pip install -r requirements.txt
python -m uvicorn meal.api.api_run:app --reload --port 8000
# Accesează: http://localhost:8000
```
Script alternativ (Windows): `run_meal_main_WIND.bat`.

---
## 3. Directoare Critice (MINI-HARTĂ)
| Dir | Rol |
|-----|-----|
| `meal/api/` | Endpoint-uri + pagini HTML (FastAPI + Jinja2) |
| `meal/domain/` | Modele pure (Ingredient, Recipe, Plan, Pantry) |
| `meal/rules/` | Algoritmi (shopping list) + placeholders patterns |
| `meal/infra/` | Persistență JSON + PDF export |
| `meal/events/` | EventBus + buffer alerte UI |
| `meal/services/` | Fațade (doar raportare nutriție implementată acum) |
| `meal/data/` | Fișiere JSON persistente (stare aplicație) |
| `meal/static/` | CSS / JS / imagini |
| `meal/templates/` | Șabloane Jinja2 |

---
## 4. Fișiere JSON cheie
| Fișier | Descriere | Chei principale |
|--------|-----------|-----------------|
| `Pantry_ingredients.json` | Stoc curent ingrediente | `name, unit, default_quantity, data_expirare, tags` |
| `Pantry_recipe_cooked.json` | Preparate gătite (resturi) | `name, default_quantity, data_expirare, date_cooked` |
| `recipes.json` | Catalog rețete | `name, servings, ingredients[], steps[], tags[], calories_per_serving, macros{}` |
| `plan.json` | Planuri săptămânale | `YYYY-Www -> { Monday:{breakfast,lunch,dinner}, ... }` |
| `shopping_transactions.json` | Istoric cumpărări | `id, timestamp, week, merged[], added[]` |

---
## 5. Evenimente (EventBus)
| Nume | Declanșat când | Payload chei |
|------|----------------|--------------|
| `pantry.low_stock` | Cantitate ≤ prag | `ingredient, remaining, threshold` |
| `pantry.near_expiry` | Expirare ≤ 5 zile (default) | `ingredient, days_left, threshold` |
| `pantry.expiring_snapshot` | Pagina /camara generează snapshot | `count, items[]` |

Consumate de `web_observers` → accesibile via `GET /api/pantry/alerts` (poll incremental, cursor `since`).

---
## 6. Endpoint-uri Critice (minim necesar)
| Metodă | URL | Rol | Note |
|--------|-----|-----|------|
| GET | `/` | Dashboard (plan + nutriție + alerte) | Param opționali week/year |
| POST | `/update_meal` | Setează rețetă într-un slot | Acceptă form sau JSON |
| GET | `/shopping-list` | HTML listă cumpărături | Param: `include_past` |
| GET | `/api/shopping-list` | JSON listă cumpărături | `skip_past=1` ignoră zile trecute |
| POST | `/api/shopping-list/buy` | Aplică achiziție | Fuzionează ingrediente |
| GET | `/api/pantry/alerts` | Alerte stoc/expirare | Poll: `?since=<cursor>` |
| CRUD | `/api/pantry/ingredient` | Administrare cămară | Unicitate `name` |
| CRUD | `/api/pantry/cooked` | Administrare preparate gătite | Nume + dată împotriva duplicatelor |
| POST | `/recipes` | Adăugare rețetă (cu Spoonacular) | Upload imagine + nutrienți |

---
## 7. Algoritm Listă Cumpărături (Esential)
Funcție: `rules/Shopping_List_Builder.build_shopping_list(plan, recipes, pantry, skip_past_days)`
Pași:
1. Index rețete după nume normalizat.
2. Agregare cantități cerute pentru toate sloturile ≠ '-' (opțional fără zile trecute).
3. Normalizare & stemming simplu (tomatoes→tomato, peppers→pepper etc.).
4. Scădere stoc actual (`Pantry_ingredients.json`).
5. Returnează doar itemii cu `missing > 0`, sortați alfabetic.

Structură element rezultat: `{ name, unit, required, have, missing }`.

---
## 8. Praguri & Constante Critice
Definite în `utilities/constants.py`:
```
DATE_FORMAT = "%d-%m-%Y"
DAYS_BEFORE_EXPIRY = 5
LOW_STOCK_THRESHOLD = {"g": 200, "ml": 500, "pcs": 3, "cloves": 2}
```
Schimbarea lor afectează direct evenimentele & alertele.

---
## 9. Nutriție
Funcție: `services/Reporting_Service.compute_week_nutrition(plan, recipes)`
Returnează:
```
{
  days: { DayName: { calories, protein, carbs, fats, meals{ slot->{...} } }, ... },
  week_totals: { calories, protein, carbs, fats }
}
```
Macronutrienți acceptă `carbs|carbohydrates`, `fats|fat`.

---
## 10. Cazuri de Atenție (Riscuri)
- API key Spoonacular hardcodificat (`api/routes/add.py`) → pune-l în env: `SPOONACULAR_API_KEY` (viitor).
- Lipsă locking atomic la majoritatea fișierelor (risc la scrieri simultane).
- Fără autentificare (toți utilizatorii pot edita datele).
- Buffer evenimente doar in-memory (dispare la restart, nu scalează cross-process).

---
## 11. Extensii Rapide Recomandate
| Idee | Loc | Beneficiu |
|------|-----|-----------|
| Strategy Plan (balanced, leftovers-first) | `rules/Plan_Strategy.py` | Automatizează planificarea |
| State pentru mese | `rules/Meal_State.py` | Tracking clar al progresului |
| YAML Import rețete | `rules/Recipe_Importer.py` | Flexibilitate input |
| Conversii unități | nou: `utilities/units.py` | Liste de cumpărături mai precise |
| Auth simplu | middleware / router nou | Protecție date |

---
## 12. Chei JSON / Câmpuri Critice
| Entitate | Chei Must-Have | Observații |
|----------|----------------|-----------|
| Ingredient | `name, unit, default_quantity, data_expirare?, tags[]` | Tag unic (listă cu 1) |
| Recipe | `name, servings, ingredients[], steps[], tags[], calories_per_serving, macros{}` | `macros` fallback dacă lipsesc valori |
| Plan Day Slot | `breakfast|lunch|dinner` | `-` = necompletat |
| Cooked Recipe | `name, default_quantity, data_expirare, date_cooked` | Eliminare duplicate (nume + dată) |
| Shopping Item | `name, unit, required, have, missing` | Generat din builder |
| Event Payload | low_stock: `ingredient, remaining, threshold` | near_expiry: +`days_left` |
| Transaction | `id, timestamp, week, merged[], added[]` | Folosit la audit minimal |

---
## 13. Minimal Workflow Zilnic
1. Actualizezi planul săptămânal (/).
2. Verifici lista cumpărături `/shopping-list` -> cumperi -> `POST /api/shopping-list/buy`.
3. Gătești și marchezi resturile ca preparate gătite (UI / API).
4. Monitorizezi alertele (poll `/api/pantry/alerts`).
5. Ajustezi ingredientele când consumi manual.

---
## 14. Alerte – Cum Funcționează (Rezumat 5 sec)
1. Pantry (sau rulările de scan) publică evenimente.
2. `web_observers` le pune în buffer cu ID incremental.
3. Frontend cere `/api/pantry/alerts?since=<ultimul_id>`.
4. Primește doar ce-i nou → UI actualizat fără reîncărcare grea.

---
## 15. Validări & Sanitizare Critice
- Tag ingrediente forțat în lista permisă (`pantry.py` → fallback `other`).
- Conversie date vechi gătit `YYYY-MM-DD` → `DD-MM-YYYY` (`logs.py`).
- Eliminare dubluri rețete (nume case-insensitive) la adăugare.
- Fuzionare ingrediente cumpărate cu aceeași dată de expirare.

---
## 16. Check rapid înainte de commit (manual)
- Plan încă se generează? `GET /api/shopping-list` return 200.
- Alerte apar? `GET /api/pantry/alerts` are `events`.
- Rețetă nouă se salvează? `POST /recipes` → 200 + macros.
- `plan.json` nu are câmpuri `date` persistente.

---
## 17. Ce Să NU faci
- Să scrii direct în `plan.json` date calendaristice (se regenerează).
- Să hardcodezi noi praguri în mai multe locuri (doar `constants.py`).
- Să adaugi logică de business grea în `api_run.py` (mut-o în rules/services).

---
## 18. Glosar Ultra-Succint
| Termen | Explicație |
|--------|-----------|
| Slot | Unul din: breakfast/lunch/dinner |
| Missing | Cantitate ce lipsește din cămară pentru un ingredient planificat |
| Snapshot Expiring | Lista curentă ingrediente care expiră curând |
| Cursor (alerts) | Ultimul ID de eveniment consumat |

---
## 19. Contact & Contribuții
Adaugă issue / PR (după publicare). Prioritizează: stabilitate la scriere JSON, implementare strategii plan, acoperire test builder.

---
## 20. TL;DR Tehnic (o frază)
FastAPI + Jinja2 + JSON storage + EventBus simplu pentru alerte, cu un builder care deduce ce trebuie cumpărat din diferența (plan − cămară).

---
(Sfârșit) – Păstrează acest fișier concis și actualizat la schimbări majore.

