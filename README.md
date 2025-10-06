# Meal Planner & Pantry Tracker – Documentație (RO)

Acest proiect oferă o aplicație web (FastAPI + Jinja2) pentru:
- Gestionare cămară (ingrediente cu cantități, unități, expirare, tag-uri)
- Gestionare rețete (ingrediente, pași, nutriție, imagini)
- Planificare mese săptămânale (mic dejun / prânz / cină, pe zile)
- Generare listă de cumpărături din plan (scăzând ce există în cămară)
- Achiziții (marcare cumpărare și consolidare ingrediente)
- Evidență preparate gătite
- Calcul sumar nutrițional pe săptămână
- Alerte stoc scăzut și expirare apropiată (prin EventBus + buffer web)

---
## 1. Structura proiectului
```
meal/
  main.py                  # Pornire uvicorn (entry simplu)
  api/                     # Layer HTTP (FastAPI) + template pages
    api_run.py             # Instanța FastAPI, pagini HTML, endpoint-uri JSON
    routes/                # Sub-rute logice: recipes, pantry, logs, add, ...
  domain/                  # Entități de bază (Ingredient, Recipe, Plan, Pantry,...)
  infra/                   # Persistență simplă JSON + utilități (PDF)
  rules/                   # Logică de business (shopping list builder, strategii TODO)
  services/                # (Placeholder) Fațade servicii – TODO
  events/                  # Event Bus + observatori web
  utilities/               # Constante & utilitare
  static/                  # CSS, JS, imagini, thumbnails
  templates/               # Jinja2 HTML templates
  tests/                   # Teste unitare / API (parțiale)
  data/                    # Fișiere JSON persistente
```
Fișier suplimentar existent: `README-Meal-Planner-and-Pantry.md` (scop inițial EN). Acest document (README.md) este versiunea extinsă în română.

---
## 2. Entități Domain (folder `domain/`)
### Ingredient
Câmpuri: `name`, `unit`, `default_quantity`, `data_expirare`, `tags`.
Metode: `set_quantity(delta)`, `from_dict`, `to_dict`, `__str__`.

### Recipe
Câmpuri: `name`, `servings`, `ingredients` (listă Ingredient), `steps`, `tags`, `calories_per_serving`, `macros`.
Funcționalități: conversie dict, citire din JSON (`read_from_json`), verificare ingrediente disponibile (`check_ingredients`), simulare gătire (`cook`) – consumă ingrediente și returnează `RecipeCooked`.

### RecipeCooked
Extinde `Ingredient` (moștenire pentru a permite tratarea resturilor ca ingrediente cu expirare scurtă). Adaugă `kallories`.

### Pantry
Conține listă de `Ingredient` și un `EventBus` pentru notificări. La adăugare / modificare declanșează:
- `pantry.low_stock` dacă cantitatea ≤ prag (per unitate) din `LOW_STOCK_THRESHOLD`.
- `pantry.near_expiry` dacă expirarea este în ≤ `DAYS_BEFORE_EXPIRY` zile.
Metode principale: `add_item`, `remove_item`, `update_quantity`, `scan_and_notify`.

### Plan
Structură: `week_number`, `year`, `meals` (dict: Day → { breakfast, lunch, dinner, date }). Datele sunt injectate de repository la fiecare încărcare.

---
## 3. Persistență & Infra (folder `infra/`)
JSON local (fără DB). Fișiere cheie în `meal/data/`:
- `recipes.json` – catalog rețete (listă dict)
- `Pantry_ingredients.json` – inventar cămară
- `Pantry_recipe_cooked.json` – preparate gătite
- `plan.json` – planuri săptămânale keyed de `YYYY-Www`
- `shopping_transactions.json` – istoricul achizițiilor (append / merge)

Repository-uri:
- `Plan_Repository.py` – creează + menține structura plan săptămână (completare date, randomize week). Salvează fără câmpul `date` (derivat la fiecare load).
- `Recipe_Repository.py` / `Pantry_Repository.py` – lectură simplă JSON (unele rămase în fază inițială vs API actual).

`pdf_utils.generate_pdf_for_week(plan)` – export tabelar plan săptămânal (A4 landscape, ReportLab).

---
## 4. Evenimente (folder `events/`)
`Event_Bus.py` implementă un bus elementar (Observer). Evenimente folosite:
- `pantry.low_stock`
- `pantry.near_expiry`
- `pantry.expiring_snapshot` (snapshot periodic / la acces pagină)

`web_observers.py` se abonează la primele două și păstrează un buffer in‑memory (ring buffer) pentru interogări AJAX (`/api/pantry/alerts`). Structura răspuns:
```
{
  events: [ { id, type, ts, name, quantity, threshold, days_left? }, ...],
  next_cursor: <ultimul_id>
}
```
Clientul poate face polling incremental folosind `since=<next_cursor>`.

`event_helpers.py` oferă funcții sugar pentru publicare: `publish_low_stock`, `publish_near_expiry`, `publish_expiring_snapshot`.

---
## 5. Regulile de Business (folder `rules/`)
### Shopping_List_Builder
Funcție centrală: `build_shopping_list(plan, recipes, pantry, skip_past_days=False)`
Returnează listă de dict:
`{ name, unit, required, have, missing }` doar pentru `missing > 0`.
Caracteristici:
- Normalizare nume (case-insensitive, trimming)
- „Stemming” simplu plural → singular (ies→y, oes→o, es/s → remove) pentru agregare corectă
- Poate ignora zile trecute (dacă `skip_past_days=True` și plan are câmp `date`). Logică folosită la generarea din UI pentru săptămâna curentă.

### TODO placeholders
- `Plan_Strategy.py` – Strategy Pattern pentru generare plan (balanced / leftovers-first / budget) – încă neimplementat.
- `Meal_State.py` – State Pattern (Planned → Cooked → Logged) – placeholder.
- `Recipe_Importer.py` – Template Method pentru import multi‑format (JSON/YAML) – placeholder.

---
## 6. Layer API & UI (folder `api/`)
### `api_run.py`
Inițializează FastAPI, montează static + templates, pornește observatori evenimente.
Pagini HTML (Jinja2):
- `/` (index) – vizualizare plan + alerte + nutriție agregată
- `/meal-plan/{week}` – vizualizare explicită săptămână
- `/shopping-list` – listă cumpărături (opțional exclude zile trecute)
- `/camara` – status cămară + preparate gătite + alerte
- `/camara/edit` – interfață editare
- `/recipe/{recipe_name}` – detaliu rețetă (ingrediente, pași, macros)
- `/recipes-page` – listare rețete (+ filtrare tag)
- `/add-recipe` – formular adăugare rețetă (cu upload imagine + fetch nutriție Spoonacular)

Endpoint‑uri JSON principale:
- `GET /api/shopping-list` (param: `week`, `year`, `skip_past=1`) – listă cumpărături
- `GET /api/shopping-list/current` – shortcut săptămână curentă
- `POST /api/shopping-list/buy` – efectuează „cumpărare” listă (vede shopping list, validează și inserează/merge în `Pantry_ingredients.json`, log tranzacție). Face:
  - Normalizare + „stemming” nume
  - Fuzionează înregistrări existente cu aceeași dată de expirare
  - Creează ingrediente noi dacă nu există
  - Marchează skip pentru articole inexistente sau fără missing
- `GET /api/pantry/alerts` – evenimente recente (polling incremental)

CRUD cămară:
- `POST /api/pantry/ingredient` – adaugă ingredient (unicitate pe `name`)
- `PUT /api/pantry/ingredient/{name}` – editează; previne coliziuni de nume
- `DELETE /api/pantry/ingredient/{name}` – șterge
- `POST /api/pantry/ingredients/bulk-delete` – ștergere multiplă

Preparat gătit:
- `POST /api/pantry/cooked`
- `PUT /api/pantry/cooked/{name}`
- `DELETE /api/pantry/cooked/{name}`

Rețete (demo / debug / add):
- `GET /_debug/recipes` / `/_debug/recipes-path`
- `POST /recipes` (în router `add`) – salvează + îmbogățește nutriția prin Spoonacular (API key hard‑codificat – vedeți secțiunea Securitate).

Actualizare plan din UI:
- `POST /update_meal` – primește (form-data sau JSON fallback) și înlocuiește rețeta unui slot.

### Normalizări și sanitizare
- `routes/pantry.py` forțează tag dintr-un set permis și completează câmpuri lipsă.
- `routes/logs.py` convertește format vechi date gătit (YYYY-MM-DD → DD-MM-YYYY) o singură dată.

---
## 7. Calcul Nutrițional
`Reporting_Service.compute_week_nutrition(plan, recipes)` produce:
```
{
  days: {
    Monday: { date, calories, protein, carbs, fats, meals: { breakfast:{...}, ... } },
    ...
  },
  week_totals: { calories, protein, carbs, fats }
}
```
Macronutrienții se normalizează (carbohydrates / carbs, fat / fats). Folosit în paginile index / meal-plan.

---
## 8. Fișiere Date (format)
Exemplu ingredient (`Pantry_ingredients.json`):
```
{
  "name": "Chicken breast",
  "unit": "g",
  "default_quantity": 500,
  "data_expirare": "05-10-2025",
  "tags": ["meat-chicken"]
}
```
Rețetă (`recipes.json`):
```
{
  "name": "Chicken Curry",
  "servings": 4,
  "ingredients": [ {"name":"Chicken breast", "unit":"g", "default_quantity":500}, ...],
  "steps": ["Cut chicken", ...],
  "tags": ["dinner"],
  "calories_per_serving": 420,
  "macros": {"protein": 35, "carbohydrates": 20, "fats": 18},
  "image": "chicken_curry.jpg"
}
```
Plan (`plan.json`):
```
{
  "2025-W39": {
    "Monday": {"breakfast":"-","lunch":"Chicken Curry","dinner":"-"},
    ...
  }
}
```
Datele calendaristice se adaugă la runtime (nu se persistă `date` pentru evitarea drift).

---
## 9. Praguri & Constante (`utilities/constants.py`)
- `DATE_FORMAT = "%d-%m-%Y"`
- `DAYS_BEFORE_EXPIRY = 5` (trigger near_expiry)
- `LOW_STOCK_THRESHOLD = {"g":200, "ml":500, "pcs":3, "cloves":2}`

---
## 10. Fluxuri Principale
### A. Generare listă cumpărături
1. User setează rețete în plan.
2. `GET /shopping-list` → încarcă plan + rețete + cămară.
3. `build_shopping_list` agregă necesarul → scade stocul existent → returnează doar ce lipsește.
4. UI oferă posibilitate marcare cumpărare (checkbox / select) → `POST /api/shopping-list/buy`.
5. Endpoint „buy” actualizează `Pantry_ingredients.json` (merge după nume + expirare). Creează tranzacție.

### B. Alerte Cămară
- La încărcare ingredient sau update cantitate → se evaluează stoc + expirare.
- `Pantry` publică evenimente → `web_observers` le salvează.
- Frontend poll `/api/pantry/alerts` și afișează badge / listă.

### C. Nutriție Săptămână
- La randare pagină plan: se calculează sumar per slot și total (fără multiplicare suplimentară – 1 serving presupus per consum). Extensibil ulterior.

### D. Adăugare Rețetă Nouă
1. Formular trimite: nume, porții, ingrediente (JSON string), pași, tags, imagine.
2. Backend apelează Spoonacular `analyze` cu lista ingredientelor text.
3. Extrage macros (Calories, Protein, Carbohydrates, Fat) → salvează.

---
## 11. Endpoint-uri (sinopsis rapid)
| Tip | Endpoint | Descriere |
|-----|----------|-----------|
| GET | / | Dashboard plan + alerte + nutriție |
| GET | /shopping-list | Listă cumpărături (HTML) |
| GET | /camara | Vizualizare cămară |
| GET | /recipe/{name} | Detaliu rețetă |
| GET | /recipes-page | Catalog rețete (filtrare tag) |
| GET | /api/shopping-list | JSON listă cumpărături |
| POST | /api/shopping-list/buy | Marchează cumpărare articole |
| GET | /api/pantry/alerts | Evenimente alerte recente |
| CRUD | /api/pantry/ingredient[...] | Add / edit / delete / bulk-delete |
| CRUD | /api/pantry/cooked[...] | Add / edit / delete preparat gătit |
| POST | /update_meal | Actualizează un slot (plan) |
| POST | /recipes | Adăugare rețetă (cu upload) |

---
## 12. Rulare & Setup
### Dependențe
Lista în `requirements.txt` (versiuni pinned principale): FastAPI, Uvicorn, Pydantic v2, Jinja2, python-multipart, httpx, reportlab, pytest-asyncio, typer, rich.

### Rulare rapidă (Windows)
1. Creați virtual env (opțional):
```
python -m venv .venv
.venv\Scripts\activate
```
2. Instalați dependențe:
```
pip install -r requirements.txt
```
3. Porniți serverul:
```
python -m uvicorn meal.api.api_run:app --reload --host 0.0.0.0 --port 8000
```
Sau folosiți scriptul: `run_meal_main_WIND.bat` (activează venv + pornește).

4. Accesați: http://localhost:8000

### PDF Export
(Dacă există buton / integrare – utilizați `generate_pdf_for_week(plan)`; altfel se poate apela manual în viitor printr-un endpoint dedicat.)

---
## 13. Testare
Testele actuale (parțiale):
- `test_pantry.py` – operații de bază add/remove
- `test_shopping_list_api.py` – verifică generare listă cumpărături și cazuri specifice (Bell pepper lipsă, spaghetti suficient, chicken breast deficit)
- (Fișiere placeholder goale: `test_shopping_list_builder.py` etc.)

Rulare:
```
pytest -q
```
(Instalați `pytest` dacă nu e deja – se include tranzitiv prin alte dependențe în unele medii, altfel `pip install pytest`.)

---
## 14. Considerații Securitate & Limite
- Cheia Spoonacular este hardcodificată în `add.py` → mutați într-o variabilă de mediu înainte de producție.
- Fără autentificare / ACL – orice utilizator poate modifica datele.
- Concurență: scrierea JSON folosește `_atomic_write` doar pentru `recipes.json`. Alte fișiere pot suferi race conditions dacă există scrieri simultane.
- Evenimentele sunt in‑memory; într-un deployment multi‑proces vor fi per proces (nu sincronizate central) – suficient pentru un scenariu local.

---
## 15. Posibile Îmbunătățiri (Roadmap)
1. Implementare reală Strategy (`Plan_Strategy`) – generare automată plan echilibrat macro / folosire resturi.
2. State Pattern pentru evoluție masă: planned → cooked → logged (persistență în logs dedicat).
3. Import rețete YAML / PDF / copy‑paste text (Template Method în `Recipe_Importer`).
4. Consolidare cantități + unit conversions (g ↔ kg, ml ↔ L) pentru listă cumpărături.
5. Observabilitate: log structură + endpoint health.
6. Persistență în SQLite sau LiteFS pentru integritate + locking.
7. Autentificare simplă (JWT / cookie) + multi user.
8. UI îmbunătățit: drag & drop pentru plan, progressive enhancement.
9. Cache nutriție pentru a evita request repetat la API extern.
10. Teste suplimentare: shopping list builder (plural merge, skip past), event bus, buy merging logic.

---
## 16. Edge Cases Gestionate
- Nume rețete/ingrediente cu spații / case differences (normalizare la comparare).
- Formate expirare diverse la achiziție (acceptă `%d-%m-%Y` și `%Y-%m-%d`).
- Zile fără date parse‑abile: ignorare filtrare `skip_past_days` (fail-safe).
- Plural simplu: tomatoes → tomato, candies → candy, boxes → box, peppers → pepper.
- Dublu POST rețetă cu același nume: eroare 400.
- Adăugare preparat gătit duplicat (nume + dată): blocat.
- Alert buffer gol: la primul call `/api/pantry/alerts` se generează snapshot inițial.

---
## 17. Limitări Curente
- Fără refolosirea codului `Pantry` în endpoint‑urile CRUD (lucrează direct pe dict JSON) – strat inconsistent.
- Lipsă validări pydantic pentru payload‑uri (majoritatea sunt dict brute).
- Lipsă centralizare conversii unități.
- Lipsă UI pentru editare plan random / reset (există în repository metode dar nu expuse complet).

---
## 18. Stil & Convenții
- Date: `DD-MM-YYYY` (vechiul format ISO se migrează la load în logs).
- Chei JSON snake_case (ex: `default_quantity`).
- Tag-uri ingrediente: set controlat (fallback `other`).

---
## 19. Cum să Extinzi
1. Adaugă un nou tip de alertă (ex: high_protein_day):
   - Publică un eveniment nou dintr-un serviciu.
   - Abonează-l în `web_observers.start`.
2. Adaugă conversia macro la plan:
   - Extinde `compute_week_nutrition` cu calcul pe porții dinamice.
3. Persistență DB:
   - Creează layer repository nou (SQLAlchemy) dar menține API identic pentru `PlanRepository`.

---
## 20. Rezumat Rapid Flow Tehnic
1. User accesează UI → FastAPI servește template Jinja2.
2. Template încarcă JS / CSS din `/static`.
3. JS poll la `/api/pantry/alerts` pentru alerte (json incremental).
4. Acțiuni user (update meal / add recipe / buy list) → endpoint JSON → scrie fișiere JSON.
5. Evenimente generare listă / modificări cămară → event bus → buffer → UI.

---
## 21. Licență / Atribuire
(Nespecificată încă – adăugați o licență dacă proiectul devine public.)

---
## 22. Întrebări Frecvente (FAQ)
Q: De ce nu persistă câmpul `date` în `plan.json`?
A: Este derivat din `(year, week_number)` la încărcare pentru a evita inconsistențe când se schimbă calendarul ISO.

Q: Cum pot schimba pragul de expirare?
A: Modificați `DAYS_BEFORE_EXPIRY` în `utilities/constants.py`.

Q: Pot adăuga altă unitate cu prag low-stock?
A: Adăugați pereche în `LOW_STOCK_THRESHOLD`. Apoi reîncărcați aplicația.

Q: De ce nu văd alerte imediat?
A: Dacă buffer-ul e gol, primul GET la `/api/pantry/alerts` declanșează o scanare.

---
## 23. Contact / Contribuții
- Deschideți issue / pull request (după publicare repo) pentru buguri / idei.
- Sugestii testare: începeți cu cazuri pluralization + merge la cumpărare.

---
Happy cooking & planning! 🍲


---
## 24. Detaliere Directoare & Separarea Logicii
Această secțiune explică explicit de ce există fiecare director și cum este împărțită logica pe straturi (layered / hexagonal-ish).

### Vedere de ansamblu (straturi)
```
[ UI / Presentation ]  ->  api/  + templates/ + static/
        |                (servește pagini + expune endpoint-uri REST/HTML)
        v
[ Application / Orchestration ]  -> services/ (fațade – momentan placeholders)
        v
[ Domain Core ]  -> domain/ (entități pure + reguli interne simple)
        v
[ Business Rules / Policies ]  -> rules/ (algoritmi: shopping list, strategii plan, import)
        v
[ Events / Integration ]  -> events/ (publish-subscribe, adaptare către UI)
        v
[ Infrastructure ]  -> infra/ (persistență JSON, PDF, acces fișiere)
        v
[ Data / Storage ]  -> data/ (artefacte persistente JSON)

(Utilities și tests sunt transversale; utilities fără dependențe inverse.)
```
Direcția de dependență recomandată: în jos (UI poate folosi services/rules/domain/infra; domain NU importă api/ sau infra).

### Răspuns rapid per director
- `meal/` – pachetul principal Python; conține toate submodulele aplicației.
- `meal/main.py` – punct simplu de pornire (rulează uvicorn cu app creată în `api_run.py`).

#### Presentation Layer
- `meal/api/` – configurează FastAPI, montează static & templates, definește paginile principale și include routere modulare.
- `meal/api/api_run.py` – instanța `FastAPI`, pagini HTML (TemplateResponse), endpoints JSON, inițiere observatori evenimente.
- `meal/api/routes/` – rute tematice separate (single-responsibility):
  - `recipes.py` – încărcare/citire catalog rețete (demo + text response simplu).
  - `pantry.py` – încărcare/salvare ingrediente + sanitizare tag-uri & câmpuri.
  - `logs.py` – conversii format dată pentru preparate gătite; load/save.
  - `add.py` – formular + upload imagini + integrare Spoonacular pentru nutriție.
  - `plans.py` – (gol momentan) loc pentru endpoints dedicate planurilor.
- `templates/` – șabloane Jinja2 (server-side rendered UI).
- `static/` – resurse front-end (CSS, JS, imagini, thumbnails, icons). JS comunică cu API pentru acțiuni (ex: update meal, poll alerte).

#### Domain Core
- `domain/` – obiecte model pure: `Ingredient`, `Recipe`, `RecipeCooked`, `Pantry`, `Plan`. Minimizăm aici dependențele (folosește doar `utilities/constants` și primitive Python). Nu fac I/O direct (cu excepția unor metode de helper moștenite istoric — pot fi extrase).

#### Business Rules / Policies
- `rules/` – algoritmi și pattern-uri de extensibilitate:
  - `Shopping_List_Builder.py` – logica centrală pentru derivarea listei de cumpărături (normalizare/stemming + agregare).
  - `Plan_Strategy.py` – placeholder Strategy Pattern pentru auto‑generare plan.
  - `Meal_State.py` – placeholder State Pattern (Planned → Cooked → Logged).
  - `Recipe_Importer.py` – placeholder Template Method (multi‑format import).

#### Application / Services Layer
- `services/` – planificat pentru fațade / orchestrare use-case (de ex. `Planning_Service`, `Pantry_Service`, `Reporting_Service`). În prezent doar `Reporting_Service` este implementat (nutriție săptămânală) – restul TODO.

#### Events / Integration
- `events/` – canal decuplare notificări de stoc & expirare:
  - `Event_Bus.py` – bus simplu pub/sub + constante evenimente.
  - `event_helpers.py` – wrapperi semantici (publish_low_stock etc.).
  - `web_observers.py` – adaptori care transformă evenimente în buffer consultabil HTTP (poll).
  Beneficiu: UI poate interoga incremental fără a reciti toată cămara.

#### Infrastructure Layer
- `infra/` – cod dependent de detalii tehnice (fișiere JSON, ReportLab PDF):
  - `Plan_Repository.py` – încărcare/salvare planuri, generare structuri implicite, randomizare.
  - `Recipe_Repository.py` / `Pantry_Repository.py` – citire inițială JSON (unele piese au fost înlocuite deja de rutele API directe).
  - `pdf_utils.py` – generare PDF plan săptămânal.
  Observație: O parte din logică de acces fișiere migrează spre rutele API; pe termen lung merită unificat prin services + repository clar.

#### Data Store
- `data/` – fișiere JSON persistente (surse de adevăr locale). Nu conțin cod executabil. Exemple: `recipes.json`, `Pantry_ingredients.json`, `plan.json`, `shopping_transactions.json`.

#### Utilities
- `utilities/` – valori globale și (potențial) helperi transversali. Actualmente doar `constants.py`. Are voie să fie importat de oricine (nu depinde de alte module).

#### Testing
- `tests/` – teste unitare / integrare minimal curente. Structura viitoare recomandată:
  - Unit (domain & rules)
  - Integration (api endpoints)
  - Regression / scenario (flux complet plan → listă → buy)

#### Frontend Assets
- `static/` subdiviziuni (js, thumbnails, pictures, icons) pentru separare clară.
  - `week_controls.js`, `ingredient_edit.js` etc. – cod orientat pe interacțiuni AJAX / DOM.

#### Scripturi / Rădăcină
- `run_meal_main_WIND.bat` – pornire rapidă pentru Windows (activează venv + uvicorn).
- `requirements.txt` – pin dependințe pentru reproductibilitate (FastAPI, uvicorn, pydantic, httpx, reportlab etc.).
- `README-Meal-Planner-and-Pantry.md` – rezumat inițial (în engleză) cu scope & patterns.

### Principii de separare
1. Domain fără dependențe către infrastructură sau UI.
2. `rules/` poate folosi `domain/`, dar nu direct `api/`.
3. `services/` orientează use-case combinând domain + rules + infra.
4. `api/` este stratul vizibil – orchestrează și validează input, chemând services/rules.
5. `events/` oferă mecanism transversal decuplat (publish domeniu → consum UI adapter).
6. `infra/` NU ar trebui să cheme `api/` (direcție inversă). Dacă apare nevoie, extrageți într-un service.
7. `utilities/` doar oferă constante; evităm ca ele să importe alt cod pentru a preîntâmpina import cycles.

### Diagrama simplificată a dependențelor (ideală)
```
api ---> services ---> rules ---> domain
  |          |            |         ^
  |          |            v         |
  |          |----------> infra ----|
  |                       |
  |                       v
  |---------------------> events (subscribe)

utilities: folosit transversal (nu depinde de nimeni)
data: folosit DOAR de infra (și tranzitoriu de unele rute moștenite)
```

### Recomandări pentru menținere
- Când adaugi un nou algoritm (ex. scoring rețete), pune-l în `rules/` și expune-l printr-un service.
- Evită să pui logica business direct în `api_run.py`; creează funcție în `services/` și apeleaz-o.
- Migrează orice acces direct la JSON din rute către repository-uri pentru consistență.

### Plan de maturizare (refactor incremental)
1. Mută read/write ingrediente & cooked în repository dedicat (`PantryRepositoryV2`).
2. Concretizează `Planning_Service` pentru randomize + strategie.
3. Implementează `Recipe_Importer` ca Template Method (JSON/YAML) și extrage parsing din rute.
4. Introdu conversii unități într-un modul nou `utilities/units.py` și actualizează `Shopping_List_Builder`.

---
## 25. Copiere Offline (Fără Git)
Dacă dorești să creezi o copie a proiectului într-un alt director pentru a lucra separat (fără legătură la repository-ul Git curent sau înainte de a publica pe GitHub), poți folosi scriptul `copy_project_clean.bat` adăugat în rădăcina proiectului.

### A. Folosind scriptul automat (Windows CMD)
1. Rulează dublu-click pe `copy_project_clean.bat` (sau:
```
cmd /c "copy_project_clean.bat"
```
2. Scriptul copiază tot proiectul în locația implicită:
```
D:\Curs Python\Meal-Planner-Pantry-OFFLINE
```
3. Sunt excluse: `.git`, medii virtuale (`.venv`, `venv`), `__pycache__`, fișiere `.pyc`, directoare build/egg info, setări IDE.
4. După copiere, în noul director poți inițializa un repository Git complet separat:
```
cd /d D:\Curs Python\Meal-Planner-Pantry-OFFLINE
git init
git add .
git commit -m "Initial offline copy"
```
5. (Opțional) Mai târziu îl publici pe GitHub:
```
git branch -M main
git remote add origin https://github.com/<username>/<repo-nou>.git
git push -u origin main
```

### B. Personalizare destinație
Editează în script linia:
```
set "DEST_PATH=D:\Curs Python\Meal-Planner-Pantry-OFFLINE"
```
Schimbă cu orice cale validă (păstrează ghilimelele dacă sunt spații în cale).

### C. Copiere manuală alternativă
Fără script, în CMD:
```
robocopy "D:\Curs Python\Python-Academy-Projects" "D:\Curs Python\Meal-Planner-Pantry-OFFLINE" /E /XD .git .venv venv env ENV __pycache__ .idea .vscode dist build *.egg-info /XF *.pyc *.pyo *.pyd
```

### D. După copiere
- Creează eventual un nou mediu virtual în copia offline.
- Modificările nu vor afecta sursa originală.
- Poți experimenta restructurări majore înainte de a decide ce duci înapoi în proiectul principal.

### E. Observații
- Scriptul nu șterge nimic în sursă.
- Dacă rulezi din nou și destinația există, doar suprascrie fișiere schimbate.
- Pentru o copie „înghețată”, șterge destinația înainte de a rula din nou.

---
