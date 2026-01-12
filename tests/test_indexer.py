"""Tests for claude-memory/scripts/indexer.py"""

import pytest
from pathlib import Path
import sys

# Add scripts directory to path so we can import indexer
scripts_dir = Path(__file__).parent.parent / "claude-memory" / "scripts"
sys.path.insert(0, str(scripts_dir))

from indexer import parse_frontmatter, extract_keywords, fuzzy_match


class TestParseFrontmatter:
    """Tests for parse_frontmatter function"""

    def test_empty_content_returns_empty_frontmatter_and_content(self):
        """Empty content returns empty dict and empty string"""
        frontmatter, body = parse_frontmatter("")
        assert frontmatter == {}
        assert body == ""

    def test_content_without_frontmatter_returns_empty_dict(self):
        """Content without --- prefix returns empty dict and full content"""
        content = "This is just regular content"
        frontmatter, body = parse_frontmatter(content)
        assert frontmatter == {}
        assert body == content

    def test_incomplete_frontmatter_ignored(self):
        """Content with only opening --- is treated as regular content"""
        content = "---\nNo closing delimiter"
        frontmatter, body = parse_frontmatter(content)
        assert frontmatter == {}
        # Body should be the original content since we need 3+ parts when splitting by ---
        assert body == content

    def test_simple_key_value_pair(self):
        """Parses single key-value pair from frontmatter"""
        content = "---\ntitle: My Document\n---\nBody content"
        frontmatter, body = parse_frontmatter(content)
        assert frontmatter["title"] == "My Document"
        assert body == "Body content"

    def test_multiple_key_value_pairs(self):
        """Parses multiple key-value pairs"""
        content = "---\ntitle: My Doc\ncategory: notes\n---\nBody"
        frontmatter, body = parse_frontmatter(content)
        assert frontmatter["title"] == "My Doc"
        assert frontmatter["category"] == "notes"
        assert body == "Body"

    def test_key_with_colon_in_value(self):
        """Handles values containing colons"""
        content = "---\nurl: https://example.com\n---\nBody"
        frontmatter, body = parse_frontmatter(content)
        assert frontmatter["url"] == "https://example.com"

    def test_array_value_simple(self):
        """Parses array values like [item1, item2]"""
        content = "---\ntags: [python, testing]\n---\nBody"
        frontmatter, body = parse_frontmatter(content)
        assert frontmatter["tags"] == ["python", "testing"]

    def test_array_value_with_spaces(self):
        """Parses arrays with extra whitespace"""
        content = "---\ntags: [ python , testing , code ]\n---\nBody"
        frontmatter, body = parse_frontmatter(content)
        assert frontmatter["tags"] == ["python", "testing", "code"]

    def test_array_value_with_quotes(self):
        """Parses arrays with quoted items"""
        content = "---\ntags: ['python', \"testing\"]\n---\nBody"
        frontmatter, body = parse_frontmatter(content)
        assert frontmatter["tags"] == ["python", "testing"]

    def test_empty_array(self):
        """Handles empty arrays"""
        content = "---\ntags: []\n---\nBody"
        frontmatter, body = parse_frontmatter(content)
        assert frontmatter["tags"] == [""]

    def test_whitespace_handling(self):
        """Strips leading/trailing whitespace from keys and values"""
        content = "---\n  title  :  My Doc  \n---\nBody"
        frontmatter, body = parse_frontmatter(content)
        assert frontmatter["title"] == "My Doc"

    def test_empty_value(self):
        """Handles empty values"""
        content = "---\ntitle:\n---\nBody"
        frontmatter, body = parse_frontmatter(content)
        assert frontmatter["title"] == ""

    def test_body_preserves_formatting(self):
        """Body content formatting is preserved"""
        content = "---\ntitle: Doc\n---\n# Heading\n\nParagraph\n\n- List item"
        frontmatter, body = parse_frontmatter(content)
        assert body == "# Heading\n\nParagraph\n\n- List item"

    def test_ignores_malformed_lines_in_frontmatter(self):
        """Lines without colons in frontmatter are ignored"""
        content = "---\ntitle: Doc\nno colon here\nvalue: test\n---\nBody"
        frontmatter, body = parse_frontmatter(content)
        assert frontmatter["title"] == "Doc"
        assert frontmatter["value"] == "test"
        # The "no colon here" line is ignored
        assert "no colon here" not in str(frontmatter)


class TestFuzzyMatch:
    """Tests for fuzzy_match function"""

    def test_exact_match_returns_one(self):
        """Exact matches return 1.0"""
        assert fuzzy_match("test", "test") == pytest.approx(1.0)

    def test_case_insensitive_match(self):
        """Matching is case-insensitive"""
        assert fuzzy_match("Test", "test") == pytest.approx(1.0)

    def test_substring_match(self):
        """Substring matches return 0.8"""
        assert fuzzy_match("test", "testing") == pytest.approx(0.8)

    def test_target_substring_match(self):
        """When target is substring of query, returns 0.6"""
        assert fuzzy_match("testing", "test") == pytest.approx(0.6)

    def test_no_match_returns_zero(self):
        """No match returns 0.0"""
        assert fuzzy_match("apple", "banana") == pytest.approx(0.0)


class TestExtractKeywords:
    """Tests for extract_keywords function"""

    def test_empty_content_returns_keywords_from_frontmatter(self):
        """With empty content, returns only frontmatter tags"""
        frontmatter = {"tags": ["python", "testing"]}
        keywords = extract_keywords("", frontmatter)
        assert "python" in keywords
        assert "testing" in keywords

    def test_title_words_extracted(self):
        """Words from title are added to keywords"""
        frontmatter = {"title": "Python Testing Guide"}
        keywords = extract_keywords("", frontmatter)
        assert "python" in keywords
        assert "testing" in keywords
        assert "guide" in keywords
