# Meal Planner & Pantry Tracker – PREZENTARE

## 1. Elevator Pitch (30 sec)
Un asistent inteligent de planificare a meselor și gestionare a cămării care reduce risipa, optimizează cumpărăturile și oferă transparență nutrițională – totul local, rapid, fără baze de date greoaie. Planifici săptămâna, vezi ce îți lipsește, cumperi doar ce trebuie, gătești și urmărești stocurile și caloriile dintr-o interfață simplă.

## 2. Problema
- Oamenii cumpără prea mult (food waste + costuri).
- Lipsă vizibilitate asupra a ceea ce expiră curând.
- Planificare haotică → mese nesănătoase sau repetitive.
- Instrumente existente = fie prea complicate, fie fără adaptare locală.

## 3. Soluția
O aplicație web locală care combină:
1. Planificare săptămânală (mic dejun / prânz / cină).
2. Inventar cămară cu expirare și alerte automate.
3. Listă de cumpărături calculată (plan − stoc actual), inteligent agregată.
4. Nutriție sumarizată pe săptămână.
5. Tranzacții de cumpărare și resturi gătite (loop de feedback).

## 4. Public Țintă
- Familii care vor să reducă risipa.
- Persoane active care urmăresc macros / calorii.
- Studenți / cupluri care vor control al bugetului alimentar.
- Oricine vrea simplitate fără cloud/conturi.

## 5. Ce Obține Utilizatorul (Beneficii)
| Beneficiu | Cum îl livrăm |
|-----------|---------------|
| Economie bani | Liste precise (fără duplicate / surplus) |
| Mai puțină risipă | Alerte expirare + vizibilitate stoc |
| Eficiență timp | Plan complet + randomizare (viitor) |
| Control nutriție | Sumar calorii + macros pe zi & săptămână |
| Simplitate | Totul în fișiere locale JSON, portabil |

## 6. Demo Story (2 minute)
1. Deschid aplicația → văd ce gătesc săptămâna asta + calorii totale.
2. Observ în panou: 3 ingrediente aproape de expirare.
3. Ajustez 2 mese rapid (select rețeta din dropdown) → plan salvat imediat.
4. Merg la "Shopping List" → în 2 secunde am lista minus ce am deja.
5. Bifez ce am cumpărat → stocul se actualizează și alertă scăzută dispare.
6. Când gătesc, adaug preparatul gătit pentru a urmări resturile.
7. La final de săptămână verific total macros și export plan în PDF.

## 7. Arhitectură (Imagine Mentală)
```
UI (Jinja2 + JS) -> FastAPI -> Services (fațade) -> Rules (algoritmi) -> Domain (entități) -> Infra (JSON/PDF) -> Data
                           \-> Events (alerte stoc / expirare) -> Web observers -> UI polling
```

## 8. Fluxuri Cheie
| Flux | Intrare | Motor | Ieșire |
|------|---------|-------|--------|
| Planificare | Setare rețete în sloturi | PlanRepository | plan.json (fără date redundante) |
| Lista cumpărături | plan + rețete + cămară | Shopping_List_Builder | listă agregată lipsuri |
| Alerte | update ingredient | EventBus + evaluare | buffer events / UI poll |
| Nutriție | plan + rețete | Reporting_Service | calorii + macros agregate |
| Cumpărare | items selectate | buy endpoint + merge logic | actualizare stoc + tranzacție |

## 9. Elemente Diferențiatoare
- Fără DB → zero setup, portabil (doar JSON).
- Alerte reactive (event-driven) fără WebSocket (poll incremental foarte ieftin).
- Builder listă cumpărături cu normalizare plural/singular.
- Design pregătit pentru extensie Strategy (planuri inteligente) & State (life-cycle mese).
- Integrare automată nutrienți (API extern) la adăugare rețetă.

## 10. Metrici (KPI) Propuse
| KPI | Măsurare | Beneficiu |
|-----|----------|-----------|
| % ingrediente expirate | (expirate / total) / săptămână | Indicator risipă |
| Economie estimată | (missing inițial − cumpărat efectiv) | Optimizare cumpărături |
| Diversitate rețete | # rețete unice / săptămână | Varietate alimentară |
| Aderență plan | (# mese gătite / # planificate) | Disciplina utilizatorului |
| Macros balance | deviație proteine/carbs/fats | Calitate nutrițională |

## 11. Roadmap (Etape Următoare)
| Fază | Obiectiv |
|------|----------|
| Faza 1 | Strategy pentru auto-plan (balanced, leftovers-first) |
| Faza 2 | State meal (planned→cooked→logged) + UI progres |
| Faza 3 | Conversii unități & normalizare avansată |
| Faza 4 | Autentificare multi-user + spații separate |
| Faza 5 | Export rapoarte: consum / waste / cost |
| Faza 6 | Offline-first PWA / mobil |

## 12. Riscuri & Mitigare
| Risc | Impact | Mitigare |
|------|--------|----------|
| Race condition la scriere JSON | Corupere fișiere | Atomic write pentru toate + lock |
| API extern Spoonacular limită | Lipsă nutriție | Cache local + fallback manual |
| Creștere volum rețete | Încetinire load | Indexare / segmentare fișiere |
| Lipsă autentificare | Modificări neautorizate | Introducere user realm |
| Date volatile evenimente | Pierdere istoric | Persist buffer opțional |

## 13. Stack Tehnic
- Backend: FastAPI (performant, async readiness)
- Frontend: Jinja2 + JS simplu (ușor de hacking / personalizat)
- Persistență: JSON files (local-first, zero supra-head)
- Alerte: EventBus in-process + polling incremental
- PDF: ReportLab (export plan săptămână)
- Testare: pytest + TestClient

## 14. De ce FastAPI + JSON
| Criteriu | FastAPI | JSON local |
|----------|---------|-----------|
| Viteză prototip | Ridicat | Ridicat |
| Curba învățare | Mică | Zero DB config |
| Extensibilitate | Pydantic / routers | Poate fi înlocuit cu DB ulterior |
| Observabilitate | Middleware & dependency injection | Simplitate debug |

## 15. Scalare Spre Producție (Viziune)
1. Înlocuire JSON → SQLite / Postgres (repository pattern deja pregătit conceptual).
2. Introducere layer cache (ex: Redis) pentru liste & alerte.
3. Observabilitate: metrics (Prometheus), tracing (OpenTelemetry).
4. Deploy container (Docker) + volume pentru date.
5. Autentificare OIDC / JWT.

## 16. Experiență Utilizator (UX Principii)
- Zero ecran gol: planul se auto-populează când lipsește.
- Alerte clare: stoc scăzut vs expirare distinct.
- Edit rapid: un click = schimbare rețetă.
- Fără blocaje: operații idempotente & fallback silențios pe erori non-critice.

## 17. Cea Mai Complexă Logică
Shopping list builder + achiziție:
- Normalizare + stemming → agregare consistentă.
- Diferențiere missing vs have (nu doar listă totală).
- Merge inteligent la cumpărare după (nume normalizat, data expirare) → prevenire dubluri.

## 18. Criterii „Definition of Done” (MVP)
- Poți planifica o săptămână completă.
- Poți genera listă cumpărături corectă.
- Poți marca cumpărare și vedea stoc actualizat.
- Alertele apar pentru expirare / low stock.
- Nutriția totală pe săptămână se calculează.

## 19. Exemple Mesaje Valoare (Pitch către utilizator)
- „Economisește până la 20% din bugetul alimentar lunar prin eliminarea cumpărăturilor redundante.”
- „Știi mereu ce expiră în următoarele 5 zile.”
- „Un singur click pentru a actualiza mesele săptămânii.”

## 20. Poziționare vs Alternative
| Tip Alternativă | Limită |
|-----------------|--------|
| Aplicații mobile generice | Lipsă transparență / export date |
| Foi de calcul | Muncă manuală + fără alerte dinamice |
| Aplicații enterprise | Greu de configurat / overkill |

## 21. Ce Urmează pentru un „Wow Moment”
- Recomandări rețete bazate pe ce expiră + ținta proteică zilnică.
- „Smart Fill Week” → plan complet în 2 secunde.
- Vizualizare calorii pe grafic sparkline inline.

## 22. Contribuții – Cum Începi (Dev)
1. Fork / clone.
2. Rulează setup minimal (vezi secțiunea 2).
3. Începe cu un test pentru noul comportament (ex: plural edge case).
4. Adaugă funcționalitate în `rules/` + expune prin service / route.
5. Deschide PR cu rezumat clar + test.

## 23. Pitch Final (o frază memorabilă)
„Planifică inteligent, gătește sigur, cumpără doar ce trebuie – fără cloud, fără bătăi de cap.”

## 24. Call To Action
- Vrei să reduci risipa? Încearcă planul tău pentru săptămâna viitoare acum.
- Ești developer? Ajută la implementarea strategiilor de planificare automată.

---
**Întrebări?** Propune o idee nouă și putem extinde arhitectura modulară existentă.

