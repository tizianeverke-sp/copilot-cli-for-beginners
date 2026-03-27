import sys
import os
import datetime
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


class TestAddBookYearValidation:
    """Tests for year validation in BookCollection.add_book."""

    def test_valid_year(self):
        c = BookCollection()
        book = c.add_book("Dune", "Frank Herbert", 1965)
        assert book.year == 1965

    def test_blank_year_stored_as_zero(self):
        c = BookCollection()
        book = c.add_book("Unknown Year Book", "Some Author", 0)
        assert book.year == 0

    def test_current_year_is_valid(self):
        c = BookCollection()
        current_year = datetime.date.today().year
        book = c.add_book("New Book", "New Author", current_year)
        assert book.year == current_year

    def test_year_one_is_valid(self):
        c = BookCollection()
        book = c.add_book("Ancient Text", "Unknown", 1)
        assert book.year == 1

    def test_negative_year_raises(self):
        c = BookCollection()
        with pytest.raises(ValueError, match="Year must be between"):
            c.add_book("Bad Book", "Author", -100)

    def test_zero_is_not_rejected(self):
        """Explicit 0 means unknown — must be allowed."""
        c = BookCollection()
        book = c.add_book("No Year", "Author", 0)
        assert book.year == 0

    def test_future_year_raises(self):
        c = BookCollection()
        future_year = datetime.date.today().year + 1
        with pytest.raises(ValueError, match="Year must be between"):
            c.add_book("Future Book", "Author", future_year)

    @pytest.mark.parametrize("bad_year", [-1, -999, 9999])
    def test_out_of_range_years_raise(self, bad_year):
        c = BookCollection()
        with pytest.raises(ValueError, match="Year must be between"):
            c.add_book("Bad Book", "Author", bad_year)


class TestGetUnreadBooks:
    """Tests for BookCollection.get_unread_books."""

    # --- Happy path ---

    def test_returns_only_unread(self):
        c = BookCollection()
        c.add_book("1984", "George Orwell", 1949)
        c.add_book("Dune", "Frank Herbert", 1965)
        c.add_book("The Hobbit", "J.R.R. Tolkien", 1937)
        c.mark_as_read("1984")
        unread = c.get_unread_books()
        titles = [b.title for b in unread]
        assert "1984" not in titles
        assert "Dune" in titles
        assert "The Hobbit" in titles

    def test_excludes_all_read_books(self):
        c = BookCollection()
        c.add_book("1984", "George Orwell", 1949)
        c.add_book("Dune", "Frank Herbert", 1965)
        c.mark_as_read("1984")
        c.mark_as_read("Dune")
        unread = c.get_unread_books()
        assert unread == []

    def test_includes_newly_added_book(self):
        c = BookCollection()
        c.add_book("New Book", "Author", 2020)
        unread = c.get_unread_books()
        assert len(unread) == 1
        assert unread[0].title == "New Book"

    # --- Edge cases ---

    def test_empty_collection_returns_empty_list(self):
        c = BookCollection()
        assert c.get_unread_books() == []

    def test_all_books_read_returns_empty_list(self):
        c = BookCollection()
        c.add_book("Book A", "Author", 2000)
        c.add_book("Book B", "Author", 2001)
        c.mark_as_read("Book A")
        c.mark_as_read("Book B")
        assert c.get_unread_books() == []

    def test_no_books_read_returns_all(self):
        c = BookCollection()
        c.add_book("Book A", "Author", 2000)
        c.add_book("Book B", "Author", 2001)
        c.add_book("Book C", "Author", 2002)
        unread = c.get_unread_books()
        assert len(unread) == 3

    def test_single_unread_book(self):
        c = BookCollection()
        c.add_book("Solo", "Author", 2010)
        unread = c.get_unread_books()
        assert len(unread) == 1
        assert unread[0].title == "Solo"

    # --- Parametrized: varying read/unread ratios ---

    @pytest.mark.parametrize("total,num_read,expected_unread", [
        (1, 0, 1),
        (1, 1, 0),
        (3, 1, 2),
        (3, 3, 0),
        (5, 2, 3),
    ])
    def test_unread_count_ratios(self, total, num_read, expected_unread):
        c = BookCollection()
        titles = [f"Book {i}" for i in range(total)]
        for title in titles:
            c.add_book(title, "Author", 2000)
        for title in titles[:num_read]:
            c.mark_as_read(title)
        assert len(c.get_unread_books()) == expected_unread

    # --- Integration ---

    def test_mark_as_read_removes_from_unread(self):
        c = BookCollection()
        c.add_book("Dune", "Frank Herbert", 1965)
        assert len(c.get_unread_books()) == 1
        c.mark_as_read("Dune")
        assert len(c.get_unread_books()) == 0

    def test_remove_book_removes_from_unread(self):
        c = BookCollection()
        c.add_book("Dune", "Frank Herbert", 1965)
        c.add_book("1984", "George Orwell", 1949)
        c.remove_book("Dune")
        unread = c.get_unread_books()
        assert len(unread) == 1
        assert unread[0].title == "1984"

    def test_add_book_appears_in_unread(self):
        c = BookCollection()
        c.add_book("Brand New", "Author", 2024)
        titles = [b.title for b in c.get_unread_books()]
        assert "Brand New" in titles

    def test_unread_results_are_book_instances(self):
        from books import Book
        c = BookCollection()
        c.add_book("Dune", "Frank Herbert", 1965)
        unread = c.get_unread_books()
        assert all(isinstance(b, Book) for b in unread)
