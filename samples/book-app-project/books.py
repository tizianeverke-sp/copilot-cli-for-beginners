import datetime
import json
from dataclasses import dataclass, asdict
from typing import List, Optional, TypedDict


class BookStats(TypedDict):
    total: int
    read: int
    unread: int
    oldest: Optional["Book"]
    newest: Optional["Book"]

DATA_FILE = "data.json"


@dataclass
class Book:
    title: str
    author: str
    year: int
    read: bool = False


class BookCollection:
    def __init__(self):
        self.books: List[Book] = []
        self.load_books()

    def load_books(self):
        """Load books from the JSON file if it exists."""
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                self.books = [Book(**b) for b in data]
        except FileNotFoundError:
            self.books = []
        except json.JSONDecodeError:
            print("Warning: data.json is corrupted. Starting with empty collection.")
            self.books = []

    def save_books(self):
        """Save the current book collection to JSON."""
        with open(DATA_FILE, "w") as f:
            json.dump([asdict(b) for b in self.books], f, indent=2)

    def add_book(self, title: str, author: str, year: int) -> Book:
        if year != 0:
            current_year = datetime.date.today().year
            if not (1 <= year <= current_year):
                raise ValueError(f"Year must be between 1 and {current_year}, or leave blank for unknown.")
        book = Book(title=title, author=author, year=year)
        self.books.append(book)
        self.save_books()
        return book

    def list_books(self) -> List[Book]:
        return self.books

    def find_book_by_title(self, title: str) -> Optional[Book]:
        for book in self.books:
            if book.title.lower() == title.lower():
                return book
        return None

    def mark_as_read(self, title: str) -> bool:
        book = self.find_book_by_title(title)
        if book:
            book.read = True
            self.save_books()
            return True
        return False

    def remove_book(self, title: str) -> bool:
        """Remove a book by title."""
        book = self.find_book_by_title(title)
        if book:
            self.books.remove(book)
            self.save_books()
            return True
        return False

    def find_by_author(self, author: str) -> List[Book]:
        """Find all books where the author name contains the given string (case-insensitive)."""
        query = author.lower().strip()
        return [b for b in self.books if query in b.author.lower()]

    def get_unread_books(self) -> List[Book]:
        """Return all books that have not been marked as read."""
        return [b for b in self.books if not b.read]

    def get_statistics(self, books: List[Book]) -> BookStats:
        """Return statistics for a given list of books."""
        dated = [b for b in books if b.year and b.year > 0]
        return {
            "total": len(books),
            "read": sum(1 for b in books if b.read),
            "unread": sum(1 for b in books if not b.read),
            "oldest": min(dated, key=lambda b: b.year) if dated else None,
            "newest": max(dated, key=lambda b: b.year) if dated else None,
        }
