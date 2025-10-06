# Design Patterns în proiectul Meal Planner & Pantry

> Scop: documentează intenția arhitecturală, ce pattern-uri sunt **implementate**, care sunt **parțial** sau doar **schelet (TODO)** și cum pot fi extinse corect.

## 1. Hartă rapidă a pattern‑urilor

| Pattern | Status | Fișiere / Module | Rol principal |
|---------|--------|------------------|---------------|
| Domain Model (Entități) | Implementat | `domain/Ingredient.py`, `domain/Recipe.py`, `domain/RecipeCooked.py`, `domain/Plan.py` | Modelează conceptele de business (ingredient, rețetă, plan săptămânal) |
| Value Object (Ingrediente agregate) | Implementat | `Ingredient`, `RecipeCooked` | Transportă date + logică minimă (ex: conversii, consum cantitate) |
| Repository | Implementat (mixt) | `infra/Plan_Repository.py`, `infra/Recipe_Repository.py`, (pantry via funcții `load_ingredients`) | Persistență și încărcare entități din JSON |
| Service Layer | Parțial | `services/Reporting_Service.py`, TODO în alte fișiere service | Izolează operații de business compuse deasupra entităților |
| Builder (custom pipeline) | Implementat | `rules/Shopping_List_Builder.py` | Construcția listei de cumpărături din surse disparate |
| Observer / Event Bus | Implementat | `events/Event_Bus.py`, `events/web_observers.py`, integrare în `api_run.py` | Publish/subscribe pentru alerte din pantry |
| Singleton (light) | Implementat | `GLOBAL_EVENT_BUS` | Instanță unică partajată global |
| Strategy | Schelet (TODO) | `rules/Plan_Strategy.py` | Diferite politici de generare a planului (balanced, leftovers, budget) |
| State | Schelet (TODO) | `rules/Meal_State.py` | Tranziții: Planned → Cooked → Logged pentru o masă |
| Template Method | Schelet (TODO) | `rules/Recipe_Importer.py` | Cadru general pentru import (JSON, YAML, alt format) |
| Template Rendering (MVC-ish) | Implementat | `templates/*.html` + FastAPI endpoints | Separare logică server / prezentare |
| Facade (rol practic) | Implementat implicit | `api/api_run.py` | Expune un front unificat către UI / clienți |

---
## 2. Domain Model & Value Objects
**Fișiere:** `Ingredient`, `Recipe`, `RecipeCooked`, `Plan`.

Principii:
- Domeniul este explicit: un `Recipe` conține o listă de `Ingredient` (ca obiecte, nu dict raw) ⇒ claritate și testare ușoară.
- `RecipeCooked` extinde `Ingredient` pentru a reutiliza structura (cantitate, unit, data expirare) atunci când o rețetă devine un produs „stocat” (ex: porții gătite ce pot fi consumate ulterior). Aceasta este o aplicare pragmatică a moștenirii pentru a evita duplicare (un fel de Value Object reutilizat).
- `Ingredient.to_dict()` și `from_dict()` definesc o **graniță de serializare** (ușor de schimbat formatul intern fără a rupe API-ul extern).

Beneficii:
- Teste unitare simple pe entități fără a porni serverul.
- Izolare logică (ex: verificări de cantitate la gătit) fără cod HTTP.

---
## 3. Repository Pattern
**Fișiere:** `infra/Plan_Repository.py`, `infra/Recipe_Repository.py` (+ funcțiile `load_ingredients` / `save_ingredients`).

Rol:
- Abstractizează modul de stocare (JSON local acum) față de restul aplicației.
- Permite viitoare migrare spre DB (SQLite, Postgres) cu schimbări minime în servicii.

Caracteristici:
- `PlanRepository.get_week_plan()` normalizează structura și injectează datele calendaristice la fiecare încărcare (logică de hidratare a modelului) → seamănă cu un „Data Mapper simplificat”.
- `save_week_plan()` curăță câmpuri derivate (ex: `date`) înainte de scriere – reduce duplicarea și coruperea datelor persistate.

Îmbunătățiri posibile:
- Introducerea unei interfețe / clase abstracte `BaseRepository` pentru consistență.
- Implementarea reală a unui `LogRepository` (acum doar TODO).

---
## 4. Service Layer
**Fișier activ:** `services/Reporting_Service.py` (restul sunt TODO).

Motivație:
- Înlătură calcule agregate / transversale din controllers (FastAPI endpoints) – ex: agregare nutrițională pe săptămână.
- Pregătește terenul pentru orchestrare (ex: cooking workflow, inventory audit) fără a aglomera rutele.

Exemplu: `compute_week_nutrition(plan, recipes)` – centralizează tot mappingul, normalizarea macro‑nutrienților și calculul sumelor.

Extinderi recomandate:
- `PantryService`: validări compuse (low stock recompute, batch add cu rollback).
- `PlanningService`: logica de randomizare + viitoare strategii (vezi Strategy pattern).
- `LoggingService`: encapsulare a fluxului cook → deduct pantry → log.

---
## 5. Builder (Shopping List Builder)
**Fișier:** `rules/Shopping_List_Builder.py`.

De ce e un „Builder”:
- Construiește un obiect complex (lista finală) din mai multe surse: Plan (sloturi), Catalog Rețete, Stoc curent.
- Normalizează plural/singular, agregă cantități duplicate, filtrează zile trecute (opțional) și exclude sloturi deja gătite.

Pași (pipeline logic):
1. Indexare rețete.
2. Parcurgere plan (cu filtrare zile trecute + cooked skip).
3. Agregare cantități per ingredient canonical.
4. Scădere disponibil din pantry.
5. Producere listă ordonată doar cu missing > 0.

Beneficii: separă clar calculul listei de restul aplicației → testare izolată.

---
## 6. Observer / Event Bus
**Fișiere:** `events/Event_Bus.py`, `events/web_observers.py`.

Elemente cheie:
- `EventBus` menține un dicționar event_name → listă callback-uri.
- `publish()` distribuie payloadul; fiecare subscriber tratează independent (fail‑safe log).
- `GLOBAL_EVENT_BUS` joacă rol de **Singleton pragmatic** (importabil oricând).
- `web_observers.start()` se abonează și colectează evenimente într-un buffer circular (pattern Observer extins cu caching pentru UI polling incremental).

Beneficii:
- Decuplare producători (ex: scanare low stock) de consumatori (UI alert feed).
- Extindere ușoară: adăugarea unei persistări istorice → alt subscriber.

---
## 7. Singleton (lightweight)
`GLOBAL_EVENT_BUS` – o instanță creată o singură dată și reutilizată. Nu forțează Singleton strict (poți crea alt EventBus), dar oferă acces global controlat.

Avantaj: Simplitate + claritate; Dezavantaj: în testare poate necesita reset (în viitor util un `reset()` helper).

---
## 8. Strategy (schelet)
**Fișier:** `rules/Plan_Strategy.py` (TODO placeholder).

Intenție:
- Definirea unei interfețe `PlanStrategy` cu metoda (ex) `assign(plan, recipes, pantry) -> None`.
- Implementări:
  - `BalancedPlanStrategy` – distribuie calorii / macro-uri relativ uniform.
  - `LeftoversFirstStrategy` – prioritizează rețete ce consumă ingrediente pe cale să expire.
  - `BudgetStrategy` – minimizează cost (ar necesita preț / gram în meta‑date ingredient).

Pseudo-structură propusă:
```python
class PlanStrategy:
    def assign(self, plan, recipes, pantry):
        raise NotImplementedError

class LeftoversFirstStrategy(PlanStrategy):
    def assign(self, plan, recipes, pantry):
        # 1. Sortează pantry după zile până la expirare
        # 2. Map ingredient -> rețete care îl folosesc
        # 3. Populează sloturi libere cu rețete ce „salvează” ingrediente
        ...
```
Integrare: `PlanningService.randomize_week(strategy=LeftoversFirstStrategy())`.

---
## 9. State (schelet)
**Fișier:** `rules/Meal_State.py` (TODO).

Flux dorit pentru un slot de masă:
```
Planned  --cook-->  Cooked  --log (opțional metrics/feedback)-->  Logged
```
Momentan starea e reprezentată implicit: string (numele rețetei) sau dict `{'name': .., 'cooked': True, ...}`.

Propunere implementare:
```python
class MealState: pass
class Planned(MealState): ...
class Cooked(MealState): ...
class Logged(MealState): ...
```
Adaptor de serializare ca dict pentru persistență JSON.

Beneficii anticipate: reguli clare (nu poți „log” fără să fi gătit, etc.).

---
## 10. Template Method (schelet import rețete)
**Fișier:** `rules/Recipe_Importer.py` (TODO).

Scop: definirea pașilor comuni de import:
1. Load raw content
2. Parse structură
3. Normalize (chei, unități)
4. Validare (nume unic, câmpuri obligatorii)
5. Persist / return

Clase concrete: `JSONRecipeImporter`, `YAMLRecipeImporter` (ulterior `CSVRecipeImporter`).

Pseudo-exemplu:
```python
class BaseImporter:
    def import_file(self, path):
        raw = self._read(path)
        data = self._parse(raw)
        norm = self._normalize(data)
        self._validate(norm)
        return norm
    # Hook-uri protejate
    def _read(self, path): ...
    def _parse(self, raw): ...
    def _normalize(self, data): return data
    def _validate(self, data): pass
```

---
## 11. Facade (rol pragmatic al layer-ului API)
`api/api_run.py` combină:
- Routing UI + API JSON
- Orchestrare evenimente (startup observers)
- Colectare snapshot (expiring, low stock)

Devine *Fațada* externă peste modelul de domeniu și servicii – UI nu cunoaște detalii interne (numele fișierelor JSON, cum se calculează nutriția etc.).

---
## 12. DTO & Boundary Objects
- Structurile JSON expuse (plan slots, shopping list items, cooked log) sunt DTO-uri (Data Transfer Objects) non-rich.
- Conversia la/ din entități se face la margine (ex: `Ingredient.from_dict`).

Beneficiu: flexibilitate de schimbare internă fără a rupe contractul API.

---
## 13. Testare & Pattern-uri suport
- Testele pentru API (`test_shopping_list_api`, `test_cook_api`) validează integrări (Service + Repository + Builder).
- Noua logică builder (skip cooked) este acoperită → regresiile asupra pattern-urilor sunt detectate.

---
## 14. Extinderi recomandate (Roadmap)
| Task | Pattern / Beneficiu |
|------|---------------------|
| Implementare Strategy reală | Decuplare logică randomizare plan |
| Implementare State meal | Reguli tranzitii + validări coerente |
| Import rețete (Template Method) | Extensibil pentru formate multiple |
| LogRepository + LoggingService | Separă jurnalizare de cooking |
| Introducere AbstractRepository | Uniformizare persistență |
| Evenimente suplimentare (`recipe.cooked`) | Extindere Observer pentru analytics |
| Cache layer (decorator) | Performanță la agregări frecvente |

---
## 15. Ghid scurt de contribuție pe pattern-uri
1. **Adaugă o strategie nouă**: creează clasă în `Plan_Strategy.py`, implementează `assign(plan, recipes, pantry)`, expune-o în `__all__`, injectează printr-un parametru în Service/endpoint.
2. **Stare nouă**: definește clasă + reguli de tranziție; adaugă adapter pentru serializare în plan JSON.
3. **Importer nou**: moștenește din `BaseImporter`, implementează `_parse` și `_validate`.
4. **Eveniment nou**: adaugă constantă în `Event_Bus.py`, publică printr-un helper și abonează observatorul în `web_observers.start()`.

---
## 16. De ce aceste pattern-uri?
- **Claritate**: Domeniul culinar (plan, rețete, pantry) e central → Domain Model + Repositories.
- **Extensibilitate**: Modelele de planificare se pot schimba fără a atinge restul UI → Strategy.
- **Reactivitate**: Alerte proaspete pentru expirare / low stock → Observer.
- **Evoluție sigură**: Testele bat pe părțile critice (builder, cook) prevenind regresii.

---
## 17. Concluzie
Arhitectura actuală combină pattern-uri clasice pentru a păstra codul clar, extensibil și testabil. Unele module sunt doar schelete (marcate TODO) – documentul oferă direcții concrete pentru completarea lor fără a devia de la stilul existent. Următorul pas recomandat: implementarea efectivă a Strategy + State, apoi Template Method pentru import.

Dacă extinzi un pattern, actualizează și acest fișier pentru a menține documentația „adevărului arhitectural”.

---
*Ultima actualizare: generat automat – adaptați după noi implementări.*

