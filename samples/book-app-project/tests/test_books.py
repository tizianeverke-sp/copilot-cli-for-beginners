import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import books
from books import BookCollection


@pytest.fixture(autouse=True)
def use_temp_data_file(tmp_path, monkeypatch):
    """Use a temporary data file for each test."""
    temp_file = tmp_path / "data.json"
    temp_file.write_text("[]")
    monkeypatch.setattr(books, "DATA_FILE", str(temp_file))


def test_add_book():
    collection = BookCollection()
    initial_count = len(collection.books)
    collection.add_book("1984", "George Orwell", 1949)
    assert len(collection.books) == initial_count + 1
    book = collection.find_book_by_title("1984")
    assert book is not None
    assert book.author == "George Orwell"
    assert book.year == 1949
    assert book.read is False

def test_mark_book_as_read():
    collection = BookCollection()
    collection.add_book("Dune", "Frank Herbert", 1965)
    result = collection.mark_as_read("Dune")
    assert result is True
    book = collection.find_book_by_title("Dune")
    assert book.read is True

def test_mark_book_as_read_invalid():
    collection = BookCollection()
    result = collection.mark_as_read("Nonexistent Book")
    assert result is False

def test_remove_book():
    collection = BookCollection()
    collection.add_book("The Hobbit", "J.R.R. Tolkien", 1937)
    result = collection.remove_book("The Hobbit")
    assert result is True
    book = collection.find_book_by_title("The Hobbit")
    assert book is None

def test_remove_book_invalid():
    collection = BookCollection()
    result = collection.remove_book("Nonexistent Book")
    assert result is False


class TestFindByAuthor:
    """Tests for BookCollection.find_by_author."""

    @pytest.fixture
    def collection(self):
        c = BookCollection()
        c.add_book("The Hobbit", "J.R.R. Tolkien", 1937)
        c.add_book("The Lord of the Rings", "J.R.R. Tolkien", 1954)
        c.add_book("1984", "George Orwell", 1949)
        c.add_book("Dune", "Frank Herbert", 1965)
        return c

    def test_full_name_match(self, collection):
        results = collection.find_by_author("J.R.R. Tolkien")
        assert len(results) == 2
        titles = [b.title for b in results]
        assert "The Hobbit" in titles
        assert "The Lord of the Rings" in titles

    def test_partial_last_name(self, collection):
        results = collection.find_by_author("Tolkien")
        assert len(results) == 2

    def test_partial_first_name(self, collection):
        results = collection.find_by_author("Frank")
        assert len(results) == 1
        assert results[0].title == "Dune"

    def test_partial_substring(self, collection):
        results = collection.find_by_author("herb")
        assert len(results) == 1
        assert results[0].author == "Frank Herbert"

    @pytest.mark.parametrize("query", [
        "george orwell",
        "George Orwell",
        "GEORGE ORWELL",
        "OrWeLl",
        "orwell",
    ])
    def test_case_insensitive(self, collection, query):
        results = collection.find_by_author(query)
        assert len(results) == 1
        assert results[0].title == "1984"

    def test_author_not_found(self, collection):
        results = collection.find_by_author("Isaac Asimov")
        assert results == []

    def test_empty_string_returns_all(self, collection):
        """Empty query matches every author (substring of everything)."""
        results = collection.find_by_author("")
        assert len(results) == 4

    def test_whitespace_only_stripped(self, collection):
        results = collection.find_by_author("  Orwell  ")
        assert len(results) == 1

    def test_empty_collection(self):
        c = BookCollection()
        assert c.find_by_author("anyone") == []
