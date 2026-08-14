"""The endpoints, over HTTP."""
from __future__ import annotations

NUMERIC = ["sepal_length", "sepal_width", "petal_length", "petal_width"]
READS = ["/columns", "/describe_data", "/correlation",
         "/stats/petal_length", "/filter_data?column=species&value=setosa",
         "/group_by?by=species&column=petal_length"]


# --------------------------------------------------------------------- health
def test_health_before_loading(client):
    body = client.get("/health").json()
    assert body == {"status": "ok", "data_loaded": False, "rows": None}


def test_health_after_loading(loaded):
    body = loaded.get("/health").json()
    assert body["data_loaded"] is True
    assert body["rows"] == 150


# ------------------------------------------------------------------ load_data
def test_load_data_reports_the_shape(client):
    body = client.post("/load_data").json()
    assert body["rows"] == 150
    assert body["columns"] == 5
    assert body["column_names"] == NUMERIC + ["species"]


def test_load_data_reports_dtypes_and_memory(client):
    body = client.post("/load_data").json()
    assert body["dtypes"]["petal_length"] == "float64"
    assert body["dtypes"]["species"] == "object"
    assert body["memory_bytes"] > 0
    assert body["source"].endswith("iris.csv")


def test_load_data_returns_a_five_row_preview(client):
    preview = client.post("/load_data").json()["preview"]
    assert len(preview) == 5
    assert preview[0] == {"sepal_length": 5.1, "sepal_width": 3.5,
                          "petal_length": 1.4, "petal_width": 0.2,
                          "species": "setosa"}


def test_load_data_is_repeatable(client):
    first = client.post("/load_data").json()
    second = client.post("/load_data").json()
    assert first["rows"] == second["rows"] == 150


# -------------------------------------------------- everything needs the data
def test_reads_are_409_before_loading(client):
    for path in READS:
        response = client.get(path)
        assert response.status_code == 409, path
        assert response.json()["error"] == "data_not_loaded"


def test_the_409_says_what_to_do(client):
    assert "load_data" in client.get("/columns").json()["message"]


# -------------------------------------------------------------------- columns
def test_columns_lists_every_column(loaded):
    body = loaded.get("/columns").json()
    assert body["rows"] == 150
    assert [c["name"] for c in body["columns"]] == NUMERIC + ["species"]


def test_columns_flags_which_are_numeric(loaded):
    by_name = {c["name"]: c for c in loaded.get("/columns").json()["columns"]}
    assert by_name["petal_length"]["numeric"] is True
    assert by_name["species"]["numeric"] is False
    assert by_name["species"]["unique"] == 3
    assert by_name["petal_length"]["nulls"] == 0


# -------------------------------------------------------------- describe_data
def test_describe_covers_all_columns(loaded):
    body = loaded.get("/describe_data").json()
    assert set(body["describe"]) == set(NUMERIC + ["species"])


def test_describe_numeric_values_are_right(loaded):
    petal = loaded.get("/describe_data").json()["describe"]["petal_length"]
    assert petal["count"] == 150
    assert round(petal["mean"], 3) == 3.758
    assert petal["min"] == 1.0
    assert petal["max"] == 6.9


def test_describe_includes_text_columns(loaded):
    species = loaded.get("/describe_data").json()["describe"]["species"]
    assert species["count"] == 150
    assert species["unique"] == 3
    assert species["freq"] == 50


def test_describe_uses_null_not_nan(loaded):
    """NaN is not valid JSON, so gaps have to come back as null."""
    body = loaded.get("/describe_data").text
    assert "NaN" not in body
    species = loaded.get("/describe_data").json()["describe"]["species"]
    assert species["mean"] is None


# ---------------------------------------------------------------- filter_data
def test_filter_equals_on_text(loaded):
    body = loaded.get("/filter_data?column=species&op=eq&value=setosa").json()
    assert body["matched"] == 50
    assert body["total"] == 150
    assert all(r["species"] == "setosa" for r in body["rows"])


def test_filter_greater_than_on_a_number(loaded):
    body = loaded.get("/filter_data?column=petal_length&op=gt&value=5.0").json()
    assert body["matched"] == 42
    assert all(r["petal_length"] > 5.0 for r in body["rows"])


def test_filter_value_is_coerced_for_numeric_columns(loaded):
    """The query string is text; '5' has to compare as a number."""
    as_int = loaded.get("/filter_data?column=petal_length&op=gt&value=5").json()
    as_float = loaded.get(
        "/filter_data?column=petal_length&op=gt&value=5.0").json()
    assert as_int["matched"] == as_float["matched"] == 42


def test_filter_operators(loaded):
    cases = {"lt": 5.0, "lte": 5.0, "gte": 5.0, "ne": 1.4}
    for op, value in cases.items():
        body = loaded.get(
            f"/filter_data?column=petal_length&op={op}&value={value}").json()
        assert body["matched"] > 0, op


def test_filter_contains_is_case_insensitive(loaded):
    body = loaded.get(
        "/filter_data?column=species&op=contains&value=VIRGIN").json()
    assert body["matched"] == 50


def test_filter_limit_caps_the_rows_but_not_the_count(loaded):
    body = loaded.get(
        "/filter_data?column=species&op=eq&value=setosa&limit=3").json()
    assert body["matched"] == 50
    assert body["returned"] == 3
    assert len(body["rows"]) == 3


def test_filter_with_no_matches_is_still_a_200(loaded):
    response = loaded.get("/filter_data?column=species&op=eq&value=nope")
    assert response.status_code == 200
    assert response.json()["matched"] == 0


def test_filter_unknown_column_is_404(loaded):
    response = loaded.get("/filter_data?column=nope&op=eq&value=1")
    assert response.status_code == 404
    assert response.json()["error"] == "column_error"
    assert "petal_length" in response.json()["message"]


def test_filter_unknown_operator_is_422(loaded):
    """op is a Literal, so FastAPI rejects it before the endpoint runs."""
    assert loaded.get(
        "/filter_data?column=species&op=wat&value=x").status_code == 422


def test_filter_non_numeric_value_on_numeric_column_is_400(loaded):
    response = loaded.get("/filter_data?column=petal_length&op=gt&value=big")
    assert response.status_code == 400
    assert response.json()["error"] == "filter_error"


def test_filter_contains_on_a_numeric_column_is_400(loaded):
    assert loaded.get(
        "/filter_data?column=petal_length&op=contains&value=5"
    ).status_code == 400


def test_filter_limit_is_validated(loaded):
    assert loaded.get(
        "/filter_data?column=species&value=setosa&limit=0").status_code == 422
    assert loaded.get(
        "/filter_data?column=species&value=setosa&limit=999").status_code == 422


# ---------------------------------------------------------------------- stats
def test_stats_matches_known_values(loaded):
    body = loaded.get("/stats/petal_length").json()
    assert body["count"] == 150
    assert round(body["mean"], 3) == 3.758
    assert body["median"] == 4.35
    assert round(body["std"], 3) == 1.765
    assert body["min"] == 1.0
    assert body["max"] == 6.9
    assert round(body["range"], 1) == 5.9


def test_stats_quartiles_and_iqr_agree(loaded):
    body = loaded.get("/stats/petal_length").json()
    assert round(body["iqr"], 4) == round(body["q3"] - body["q1"], 4)


def test_stats_outlier_bounds_are_tukey_fences(loaded):
    body = loaded.get("/stats/sepal_width").json()
    expected_low = body["q1"] - 1.5 * body["iqr"]
    assert round(body["outlier_bounds"]["lower"], 4) == round(expected_low, 4)
    for value in body["outliers"]:
        assert (value < body["outlier_bounds"]["lower"]
                or value > body["outlier_bounds"]["upper"])


def test_stats_unknown_column_is_404(loaded):
    response = loaded.get("/stats/nope")
    assert response.status_code == 404
    assert response.json()["error"] == "column_error"


def test_stats_on_a_text_column_is_404(loaded):
    response = loaded.get("/stats/species")
    assert response.status_code == 404
    assert "not numeric" in response.json()["message"]


# ------------------------------------------------------------------- group_by
def test_group_by_species(loaded):
    body = loaded.get("/group_by?by=species&column=petal_length").json()
    assert body["agg"] == "mean"
    assert len(body["groups"]) == 3
    setosa = next(g for g in body["groups"] if g["species"] == "setosa")
    assert setosa["count"] == 50
    assert round(setosa["mean"], 3) == 1.462


def test_group_by_other_aggregations(loaded):
    for agg in ("median", "sum", "min", "max", "std", "count"):
        body = loaded.get(
            f"/group_by?by=species&column=petal_length&agg={agg}").json()
        assert len(body["groups"]) == 3, agg
        assert agg in body["groups"][0] or agg == "count"


def test_group_by_unknown_column_is_404(loaded):
    assert loaded.get(
        "/group_by?by=nope&column=petal_length").status_code == 404
    assert loaded.get("/group_by?by=species&column=nope").status_code == 404


def test_group_by_text_aggregate_is_404(loaded):
    assert loaded.get(
        "/group_by?by=species&column=species").status_code == 404


# ---------------------------------------------------------------- correlation
def test_correlation_shape_and_diagonal(loaded):
    body = loaded.get("/correlation").json()
    assert body["columns"] == NUMERIC
    for name in NUMERIC:
        assert body["matrix"][name][name] == 1.0


def test_correlation_is_symmetric_and_known(loaded):
    matrix = loaded.get("/correlation").json()["matrix"]
    assert matrix["petal_length"]["petal_width"] == \
        matrix["petal_width"]["petal_length"]
    # Petal length and width are famously almost collinear in this dataset.
    assert round(matrix["petal_length"]["petal_width"], 3) == 0.963


# ----------------------------------------------------------- generated schema
def test_openapi_document_lists_every_endpoint(client):
    paths = client.get("/openapi.json").json()["paths"]
    for path in ["/load_data", "/describe_data", "/filter_data", "/columns",
                 "/stats/{column}", "/group_by", "/correlation", "/health"]:
        assert path in paths, path


def test_openapi_documents_the_error_responses(client):
    spec = client.get("/openapi.json").json()
    filter_op = spec["paths"]["/filter_data"]["get"]["responses"]
    for status in ("409", "404", "400"):
        assert status in filter_op, status


def test_swagger_ui_and_redoc_are_served(client):
    assert client.get("/docs").status_code == 200
    assert client.get("/redoc").status_code == 200
