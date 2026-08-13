"""In-memory storage for books.

Kept in memory on purpose: the assignment is about the API design, and a
dictionary keeps the endpoint code short enough to read.
"""
from __future__ import annotations

from typing import Dict, Iterator, List, Optional

SEED = [
    {"title": "Nineteen Eighty-Four", "author": "George Orwell", "year": 1949},
    {"title": "Brave New World", "author": "Aldous Huxley", "year": 1932},
]


class BookStore:
    def __init__(self, seed: bool = True) -> None:
        self._books: Dict[int, dict] = {}
        self._next_id = 1
        if seed:
            for book in SEED:
                self.add(dict(book))

    def __iter__(self) -> Iterator[dict]:
        return iter(self._books.values())

    def __len__(self) -> int:
        return len(self._books)

    def add(self, data: dict) -> dict:
        book = {
            "id": self._next_id,
            "title": data["title"],
            "author": data["author"],
            "year": data.get("year"),
            "available": data.get("available", True),
        }
        self._books[book["id"]] = book
        self._next_id += 1
        return book

    def get(self, book_id: int) -> Optional[dict]:
        return self._books.get(book_id)

    def remove(self, book_id: int) -> bool:
        return self._books.pop(book_id, None) is not None

    def find_duplicate(self, title: str, author: str,
                       ignore_id: int | None = None) -> Optional[dict]:
        """A book counts as the same one if title and author both match."""
        key = (title.casefold(), author.casefold())
        for book in self._books.values():
            if book["id"] == ignore_id:
                continue
            if (book["title"].casefold(), book["author"].casefold()) == key:
                return book
        return None

    def search(self, author: str | None = None) -> List[dict]:
        books = list(self._books.values())
        if author:
            needle = author.casefold()
            books = [b for b in books if needle in b["author"].casefold()]
        return books
