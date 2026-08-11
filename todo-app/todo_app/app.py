"""Flask routes for the To-Do List app."""
from __future__ import annotations

import os

from flask import Flask, redirect, render_template, request, session, url_for

from .storage import TaskStore
from .tasks import (
    add_task,
    clear_completed,
    counts,
    delete_task,
    toggle_task,
    visible_tasks,
    TaskError,
)

DEFAULT_DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tasks.json")
VIEWS = ("all", "active", "done")


def create_app(db_path: str | None = None) -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("TODO_SECRET_KEY", "dev-key-change-me")
    app.config["DB_PATH"] = db_path or os.environ.get("TODO_DB", DEFAULT_DB)

    def get_store() -> TaskStore:
        return TaskStore(app.config["DB_PATH"])

    @app.get("/")
    def index():
        store = get_store()
        view = request.args.get("view", "all")
        if view not in VIEWS:
            view = "all"
        return render_template(
            "index.html",
            tasks=visible_tasks(store, view),
            stats=counts(store),
            view=view,
            error=session.pop("error", None),
        )

    @app.post("/add")
    def add():
        store = get_store()
        try:
            add_task(store, request.form.get("title", ""))
        except TaskError as exc:
            session["error"] = str(exc)
        return redirect(url_for("index", view=request.form.get("view", "all")))

    @app.post("/toggle/<int:task_id>")
    def toggle(task_id: int):
        store = get_store()
        try:
            toggle_task(store, task_id)
        except TaskError as exc:
            session["error"] = str(exc)
        return redirect(url_for("index", view=request.form.get("view", "all")))

    @app.post("/delete/<int:task_id>")
    def delete(task_id: int):
        store = get_store()
        try:
            delete_task(store, task_id)
        except TaskError as exc:
            session["error"] = str(exc)
        return redirect(url_for("index", view=request.form.get("view", "all")))

    @app.post("/clear-completed")
    def clear():
        store = get_store()
        clear_completed(store)
        return redirect(url_for("index", view=request.form.get("view", "all")))

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
