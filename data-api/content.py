"""The text of the write-up.

Rendered to both .docx and .pdf by build.py, using the writers from the Day 3
assignment. The figures are produced by the scripts in scripts/.
"""
from __future__ import annotations

TITLE = "Building a Data Processing API with Pandas, NumPy and FastAPI"
DAY = "Day 6 Assignment"
AUTHOR = "John Michael Bilbao"
COURSE = "Techstart"
DATE = "August 14, 2026"


def blocks() -> list[tuple]:
    b: list[tuple] = []
    p = lambda t: b.append(("p", t))
    h = lambda t: b.append(("h1", t))
    fig = lambda name, caption, width: b.append(("fig", name, caption, width))

    # ------------------------------------------------------------ introduction
    h("Introduction")
    p("This assignment asks for a FastAPI service that does data processing work "
      "with Pandas and NumPy, tested with curl and documented with screenshots.")
    p("The dataset is the Iris measurements, 150 rows and five columns, which "
      "ships with the project as a CSV. POST /load_data reads it into a Pandas "
      "DataFrame that is held in memory, and the other seven endpoints work on "
      "that DataFrame. Pandas does the loading, describing, filtering and "
      "grouping; NumPy does the statistics and the correlation matrix.")
    p("The three endpoints the assignment names are all there, and I added five "
      "more, because /load_data and /describe_data on their own do not really "
      "exercise either library. Everything is run from PowerShell on Windows.")

    # ----------------------------------------------------------------- step 1
    h("Step 1: Setting up the environment")
    p("A virtual environment, then the four packages. FastAPI is installed with "
      "the standard extras, which is what brings in Uvicorn and the fastapi "
      "command line tool.")
    fig("fig-env.png", "The environment, and the versions in it", 5.0)
    p("Before writing any endpoint I looked at the data in a plain Python "
      "session, because the shape of the API follows from the shape of the "
      "dataset. Four float columns and one text column is what leads to /stats "
      "refusing text columns and /filter_data needing to convert its value "
      "before comparing.")
    fig("fig-dataset.png",
        "The dataset: 150 rows, four numeric columns, one text column, no "
        "missing values", 5.6)
    p("The assignment asks for the project to be started with the fastapi "
      "command line tool, so the server runs with fastapi dev. It finds the app "
      "object itself, turns on reloading, and prints where the service and its "
      "documentation are:")
    fig("fig-devserver.png", "fastapi dev starting the development server", 4.4)

    # ----------------------------------------------------------------- step 2
    h("Step 2: Designing the API endpoints")
    p("Eight endpoints. The three in the assignment, four more that do actual "
      "processing, and a health check:")
    b.append(("table", [
        ["Endpoint", "What it does", "Library"],
        ["POST /load_data", "Read the CSV into a DataFrame and report its "
                            "shape, dtypes, memory use and first five rows",
         "Pandas"],
        ["GET /describe_data", "describe(include='all'), so text columns are "
                               "summarised too", "Pandas"],
        ["GET /filter_data", "Filter rows with one of seven comparisons",
         "Pandas"],
        ["GET /columns", "Per-column dtype, null count and distinct count",
         "Pandas"],
        ["GET /stats/{column}", "Mean, median, standard deviation, quartiles "
                                "and Tukey outlier fences", "NumPy"],
        ["GET /group_by", "Group on one column, aggregate another",
         "Pandas"],
        ["GET /correlation", "Pearson matrix over the numeric columns",
         "NumPy"],
        ["GET /health", "Whether the service is up and data is loaded", "\u2014"],
    ], [1.65, 3.6, 0.95]))
    p("The design decision that shaped everything else is that the DataFrame is "
      "state. It has to be loaded before anything can read it, so every read "
      "returns 409 with a message naming the endpoint to call first, rather "
      "than an empty result that looks like an answer.")
    p("The other decision is that every argument goes in the query string. "
      "Nothing takes a request body, which keeps the curl commands short enough "
      "to fit in a screenshot and means each endpoint is a URL that can be "
      "pasted into a browser.")
    p("The failures are three codes: 409 when nothing is loaded, 404 for a "
      "column that does not exist or is the wrong type, and 400 when the "
      "arguments cannot be applied to the data. All of them return the same two "
      "fields:")
    b.append(("code", [
        "{",
        '  "error": "data_not_loaded",',
        '  "message": "No dataset is loaded. Call POST /load_data first."',
        "}",
    ]))

    # ----------------------------------------------------------------- step 3
    h("Step 3: Implementing the endpoints")
    p("The endpoints themselves are thin. Each one gets the DataFrame, calls a "
      "function in processing.py and wraps the result in a response model. "
      "/filter_data is the most involved, because it is the one with real "
      "parameters:")
    fig("fig-code-endpoint.png",
        "The /filter_data endpoint. Declaring op as a Literal is what makes "
        "FastAPI reject an unknown operator before the function runs.", 6.3)
    p("Declaring op as a Literal rather than a string is worth pointing out. It "
      "gives FastAPI the list of valid operators, so a bad one is rejected with "
      "a 422 before the endpoint body executes, and it turns into a dropdown in "
      "the generated documentation. I did not have to write that validation.")
    p("The NumPy work is in processing.py. Pandas would give most of these "
      "figures directly, but the outlier bounds are easier to express as "
      "arithmetic on percentiles, and the assignment asks for NumPy:")
    fig("fig-code-numpy.png",
        "The statistics, computed on the column as a float array", 5.6)
    p("Two details in there caused real problems. NumPy scalars are not JSON "
      "serialisable, so every value goes through a helper that converts them to "
      "Python numbers. And NaN is not valid JSON at all, so any non-finite "
      "value becomes null; that is why describe() comes back with nulls where a "
      "statistic does not apply to a text column instead of failing to encode.")

    # ----------------------------------------------------------------- step 4
    h("Step 4: Testing the API with curl")
    p("Every endpoint below was called with curl.exe against the running "
      "server. The -i flag prints the status line and the headers as well as "
      "the body.")
    p("First, the health check before and after loading. This is the state the "
      "rest of the API depends on:")
    fig("fig-curl-health.png",
        "GET /health, before and after the dataset is loaded", 5.0)
    p("Loading the data. The response is the DataFrame's shape, the dtypes "
      "Pandas inferred, how much memory it occupies and the first five rows:")
    fig("fig-curl-load.png", "POST /load_data", 4.0)
    p("The per-column view, which is what tells a client which columns it can "
      "ask for statistics on. species is the only one with numeric false, and "
      "its three distinct values are the three species:")
    fig("fig-curl-columns.png", "GET /columns", 3.8)
    p("describe() across all five columns. Two columns are omitted from the "
      "screenshot to keep it on one page; the endpoint returns all five:")
    fig("fig-curl-describe.png", "GET /describe_data", 3.6)
    p("Filtering on the text column. 50 of the 150 rows are setosa, which is "
      "what the dataset should give:")
    fig("fig-curl-filter-text.png",
        "GET /filter_data with an equality match on species", 5.8)
    p("Filtering on a numeric column. 42 rows have a petal length above 5.0, "
      "and matched reports the true total while limit controls how many rows "
      "come back:")
    fig("fig-curl-filter-number.png",
        "GET /filter_data with a greater-than comparison", 5.8)
    p("The contains comparison, which is case-insensitive, so VIRGIN in upper "
      "case still finds all 50 virginica rows:")
    fig("fig-curl-filter-contains.png",
        "GET /filter_data with a partial, case-insensitive match", 6.0)
    p("The NumPy statistics for petal length. The mean of 3.758 and the median "
      "of 4.35 are far apart, which is the two-cluster shape of this dataset "
      "showing up in a single column:")
    fig("fig-curl-stats.png", "GET /stats/petal_length", 5.4)
    p("Sepal width is the column with outliers. The fences come out at 2.05 and "
      "4.05, and four measurements fall outside them:")
    fig("fig-curl-stats-outliers.png",
        "GET /stats/sepal_width, where the Tukey fences catch four values", 4.8)
    p("Grouping. Mean petal length per species separates the three cleanly, "
      "1.462 against 4.26 against 5.552, and the second call shows a different "
      "aggregation on a different column:")
    fig("fig-curl-groupby.png",
        "GET /group_by, with mean and then max", 4.4)
    p("The correlation matrix. Petal length and petal width come out at 0.963, "
      "nearly collinear, while sepal width is slightly negatively correlated "
      "with everything else:")
    fig("fig-curl-correlation.png", "GET /correlation", 4.4)

    # ------------------------------------------------------------- the errors
    h("The failure cases")
    p("A read before anything is loaded, and a column that does not exist. The "
      "404 lists the columns that do exist, which saves the caller a trip to "
      "the documentation:")
    fig("fig-curl-errors-1.png",
        "409 before loading, and 404 for an unknown column", 6.2)
    p("Then three more: text compared against a numeric column, statistics "
      "asked for on a text column, and an operator the API does not accept. The "
      "last one is a 422 rather than a 400 because FastAPI rejects it from the "
      "Literal before the endpoint runs, and its message names the seven values "
      "it would have accepted:")
    fig("fig-curl-errors-2.png",
        "400 for a value that cannot be compared, 404 for statistics on text, "
        "and FastAPI's own 422 for a bad operator", 5.0)

    # ----------------------------------------------------------------- step 5
    h("Step 5: The generated documentation")
    p("FastAPI builds an OpenAPI document from the type hints and the response "
      "models, and serves two interactive views of it. Nothing here was written "
      "by hand; the descriptions come from the endpoint decorators and the "
      "field descriptions in schemas.py.")
    fig("fig-docs-header.png",
        "The service description at /docs, taken from the FastAPI constructor",
        6.3)
    p("All eight endpoints, grouped by the tags they were given:")
    fig("fig-docs-endpoints.png", "The endpoints at /docs", 6.3)
    p("Expanding POST /load_data shows the response model with every field "
      "described, and an example built from the model itself:")
    fig("fig-docs-load.png", "POST /load_data expanded", 4.4)
    p("/filter_data shows what the type hints bought. Each parameter has its "
      "description and example, op is a dropdown of the seven operators, limit "
      "shows its range, and the three error responses are listed with the "
      "shape they return:")
    fig("fig-docs-filter.png",
        "/filter_data expanded, with the parameters FastAPI derived from the "
        "function signature", 6.0)
    p("The schemas section lists every model. ValidationError and "
      "HTTPValidationError were not written by me; FastAPI adds them because it "
      "does the parameter validation:")
    fig("fig-docs-schemas.png", "The generated schemas", 5.6)
    p("StatsResult expanded, with the descriptions from the Pydantic fields:")
    fig("fig-docs-schema-stats.png", "The StatsResult schema", 4.2)
    p("The same document also renders as ReDoc at /redoc, which is easier to "
      "read end to end:")
    fig("fig-redoc.png", "The same API at /redoc", 4.0)

    # ------------------------------------------------------------- try it out
    h("Calling the API from the documentation")
    p("Swagger UI can call the service itself, which makes the documentation a "
      "test client. The responses below came back from the running API.")
    p("Loading the data from the browser. This has to happen first, for the "
      "same reason it does from curl:")
    fig("fig-docs-tryit-load.png",
        "POST /load_data executed from /docs", 4.2)
    p("Then filtering, with the parameters filled in the form. The curl command "
      "Swagger UI shows is the same request written out, which is a convenient "
      "way to get a working command line:")
    fig("fig-docs-tryit-filter.png",
        "/filter_data executed from /docs, with the equivalent curl command",
        3.8)
    p("And the statistics endpoint, with the column supplied as a path "
      "parameter:")
    fig("fig-docs-tryit-stats.png",
        "/stats/petal_length executed from /docs", 4.2)

    # ------------------------------------------------------------------ tests
    h("Automated tests")
    p("40 tests cover the endpoints. They are worth more than the screenshots, "
      "because a screenshot proves the API worked once and these keep proving "
      "it.")
    fig("fig-tests.png",
        "The test run, and the filter, statistics and correlation tests by name",
        5.6)
    p("The values are asserted against numbers that are known for this dataset: "
      "a petal length mean of 3.758, a median of 4.35, 42 rows above 5.0, a "
      "setosa mean of 1.462 and a petal length to petal width correlation of "
      "0.963. If a filter or a statistic quietly broke, those would catch it, "
      "which a test that only checks for a 200 would not.")
    p("Several tests exist because of mistakes I made. One checks that no "
      "response body contains the text NaN, after describe() first failed to "
      "encode. One checks that value=5 and value=5.0 match the same 42 rows, "
      "after an early version compared the query string against a float column "
      "as text and returned nothing. One checks that every read returns 409 "
      "before loading, across all six read endpoints at once.")

    # ------------------------------------------------------------- reflection
    h("What I would change")
    p("The DataFrame in memory is the obvious weakness. It is a module-level "
      "variable, so two workers would each have their own copy and a client "
      "would get different answers depending on which one it reached. For "
      "anything real the data would be loaded at startup, or held somewhere "
      "both workers could see.")
    p("I would also add pagination properly. /filter_data has a limit but no "
      "offset, so there is no way to walk past the first page of matches. The "
      "matched and returned counts in the response were meant to make the "
      "truncation obvious, and they do, but they are not a substitute for being "
      "able to ask for the rest.")
    p("What went better than I expected was how much of the documentation came "
      "for free. Declaring op as a Literal, giving limit a range and putting "
      "descriptions on the Pydantic fields produced the parameter table, the "
      "dropdown, the validation and the examples in the screenshots above "
      "without any separate specification to keep in step. On the previous "
      "assignment I wrote an OpenAPI document by hand and needed tests to stop "
      "it drifting from the code; here the code is the document.")

    return b
