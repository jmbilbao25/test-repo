# Data Processing API

Day 6 hands-on. The write-up is **[Data-Processing-API-Assignment.docx](../Data-Processing-API-Assignment.docx)**,
with a **[PDF copy](../Data-Processing-API-Assignment.pdf)** — 30 pages, 29 screenshots.

A FastAPI service that does data processing with Pandas and NumPy over the Iris
dataset. `POST /load_data` reads `data/iris.csv` into a DataFrame held in memory;
the other endpoints work on it and return **409** if it has not been loaded.

## Endpoints

| Endpoint | What it does | Library |
| --- | --- | --- |
| `POST /load_data` | Read the CSV, report shape, dtypes, memory and a preview | Pandas |
| `GET /describe_data` | `describe(include="all")` | Pandas |
| `GET /filter_data` | Filter rows with one of seven comparisons | Pandas |
| `GET /columns` | Per-column dtype, nulls, distinct count | Pandas |
| `GET /stats/{column}` | Mean, median, std, quartiles, Tukey outlier fences | NumPy |
| `GET /group_by` | Group on one column, aggregate another | Pandas |
| `GET /correlation` | Pearson matrix over the numeric columns | NumPy |
| `GET /health` | Whether the service is up and data is loaded | — |

Every argument goes in the query string, so nothing takes a request body and
every endpoint is a URL you can paste into a browser.

Errors are three codes — 409 (nothing loaded), 404 (no such column, or wrong
type), 400 (arguments cannot be applied) — all returning the same shape:

```json
{ "error": "data_not_loaded", "message": "No dataset is loaded. Call POST /load_data first." }
```

FastAPI adds its own **422** for parameters it rejects before the endpoint runs,
such as an operator outside the seven allowed.

## Running it

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
fastapi dev data_api\main.py
```

- API: http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

A quick check:

```powershell
curl.exe -i -X POST http://127.0.0.1:8000/load_data
curl.exe -i "http://127.0.0.1:8000/filter_data?column=petal_length&op=gt&value=5.0&limit=3"
curl.exe -i http://127.0.0.1:8000/stats/petal_length
```

## Tests

```powershell
python -m pytest tests/ -v      # 40 tests
```

Values are asserted against figures that are known for this dataset: a petal
length mean of 3.758, a median of 4.35, 42 rows above 5.0, a setosa mean of
1.462, and a petal length to petal width correlation of 0.963. A test that only
checked for a 200 would not notice if any of those broke.

Three tests exist because of bugs I hit:

- no response body may contain the text `NaN`, after `describe()` first failed to
  encode — NaN is not valid JSON, so non-finite values become `null`
- `value=5` and `value=5.0` must match the same 42 rows, after an early version
  compared the query string against a float column as text and matched nothing
- all six read endpoints must return 409 before loading

## Rebuilding the write-up

```bash
python3 scripts/capture_env.py      # setup, dataset, dev server, tests
python3 scripts/capture_curl.py     # every endpoint through curl
python3 scripts/capture_swagger.py  # /docs and /redoc, including Try it out
python3 scripts/make_figures.py     # terminal and code figures
python3 build.py                    # writes the .docx and the .pdf
```

Every figure is real output from this project. The terminal figures use the
Windows Terminal styling in `../todo-app/scripts/render.py`, and the prompts are
PowerShell because that is where the project is run from.

Two presentation notes, both applied by the capture scripts and stated in the
report: JSON bodies are re-indented and long arrays trimmed, since the API
answers on one line and a 150-row response would not fit on a page; and absolute
paths printed by `fastapi dev` are rewritten to the Windows project path, so a
PowerShell session does not show a Linux path halfway down.
