# AI assistant

Code: `api/app/services/assistant/`. Page: `web/src/pages/Assistant.jsx`. Evaluation: `api/app/assistant_eval.py`,
`docs/ASSISTANT_EVALUATION.md`.

## What it is for
Plain-English questions about sales, guests, dishes, outlets, kitchen stock, forecasts, anomalies and *why* numbers
changed. Example questions the README uses: "Why was Outlet 3 revenue lower this week?", "Which ingredients may run
out in the next 14 days?", "How many guests did we serve last week?", "What forecast model performed best for desserts?"

## The core rule (D8)
The assistant **does not write SQL and does not invent numbers**. Each question is mapped to an intent. Each intent is a
fixed, reviewed query template. The answer is built from the template's results, and it shows where the numbers came from.

**Why:** an auditable answer matters more than a clever one. Generated SQL can return a wrong number with no visible
error. A fixed template either returns the right number or fails loudly.

## Pipeline
1. **Normalise** the question (lowercase, restaurant synonyms such as "guests" for covers, "stock" for ingredients).
2. **Match intents** (`nlu.py`): weighted patterns. The highest-weight match wins. Example: a headcount pattern at weight 5 routes "how many guests" to sales, not to customers.
3. **Resolve items**: `_resolve_item_kind` decides whether a name is a dish or an ingredient. Longest-name matching picks "Paneer Butter Masala" over "Paneer".
4. **Run the template** (`tools.py`, `insight_tools.py`) with the user's outlet scope (D3).
5. **Build the answer**: text, tables (which open as a spreadsheet), charts, and **provenance**: data source, filters, time window, model version and caveats.
6. **Cache** (`response_cache.py`): keyed by the SHA-256 of the context JSON (`06`).
7. **Optional phrasing** through a local LLM (Ollama). It is on by default in `config.py` (`LLM_ENABLED=true`) and is turned off in tests and in the e2e server. The numbers still come from step 4.

## Routing decisions and why
- **Definition and how-to questions** ("what is food cost?", "how do I void a bill?") go to **retrieval over `docs/knowledge/`**, not to a data template. Reason: they have no data answer, and the project's own docs are the right source.
- **Requests to create a spreadsheet, table or CSV of something** are read as requests for data, and the answer opens as a spreadsheet (fc09565).
- **Requests to change data** ("delete this bill", "set stock to 10") are **refused**. The assistant is read-only by design. Changes go through the normal screens, where roles and audit apply.
- **Stock how-to questions** are answered from docs (fc09565).
- **Forecast busy** (D7): the assistant says forecasts are busy rather than waiting.

## Provenance (why every answer has it)
The owner's promise is "every number traces back to the data". Each answer shows the query it used, the filters, the date
window, the model version for forecasts, and caveats (for example, "rainfall is an association, not a proven cause").

## Restaurant features (90c91d2)
- Guests and spend per guest in sales answers.
- Dish portions: "how many portions of butter chicken can we make" → `_dish_portions` → `product_stock_plan` (D13).
- Ingredient stock answers: "how much paneer is left" → ingredient stock per outlet.
- Restaurant wording throughout.

## Evaluation
- **Intent evaluation:** 31 cases. 31/31 match the expected intent.
- **Number evaluation:** 21 answers checked against independent SQL. 21/21 match.
- Run by `assistant_eval.py`. Results are written to `docs/ASSISTANT_EVALUATION.md`.
- The history of the number: 27/27 and 19/19 (fc09565), then 31/31 and 21/21 after the restaurant change.

## Known weak points
- Free-form questions outside the templates get a "I can't answer that from the data" style reply, by design. Coverage is what the 31 intents cover.
- Phrasing from the optional LLM is not evaluated the same way as the templates.
- Routing is pattern-based. A new way of asking a known question can route wrongly until a pattern is added. The evaluation set is the regression net for this.

## Changing the assistant later
When adding an intent:
1. Add the intent's pattern and weight in `nlu.py`.
2. Add a fixed query in `tools.py` or `insight_tools.py`, scoped to outlets.
3. Add provenance fields.
4. Add evaluation cases in `assistant_eval.py` for both the routing and the numbers.
5. Re-run the evaluation and update `ASSISTANT_EVALUATION.md`.
