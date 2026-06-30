"""Tests for the `strip-i18n` transform (StripTranslationWrappers)."""

from __future__ import annotations

import pytest

from deflated.transforms import StripTranslationWrappers


class TestStripTranslationWrappers:
    @pytest.mark.parametrize(
        "src,expected",
        [
            ('x = dcgettext(0, "msg", 5);', 'x = "msg";'),
            ('x = gettext("hi");', 'x = "hi";'),
            ('x = dgettext(dom, "y");', 'x = "y";'),
            # The message id may be a non-literal expression; it is just unwrapped.
            ("x = dcgettext(0, names[i], 5);", "x = names[i];"),
        ],
    )
    def test_unwrapped(self, src, expected) -> None:
        assert StripTranslationWrappers().apply(src) == expected

    def test_message_string_bytes_preserved(self) -> None:
        # Significant whitespace / delimiters inside the kept literal are verbatim.
        out = StripTranslationWrappers().apply('p = dcgettext(0, "a  {b};  c", 5);')
        assert '"a  {b};  c"' in out

    def test_nested_call_unwrapped(self) -> None:
        out = StripTranslationWrappers().apply('f(dcgettext(0, gettext("x"), 5));')
        assert out == 'f("x");'

    @pytest.mark.parametrize(
        "src",
        [
            'x = my_dcgettext(0, "m", 5);',  # longer identifier, not the wrapper
            "x = dcgettext(0, a);",  # wrong arity (2, not 3) -> left alone
            'x = p->gettext("m");',  # member access, not the free function
            'x = "dcgettext(0, m, 5)";',  # inside a string literal
            # Regression: a gettext-family *prototype/definition* header is a
            # declarator, not a call, and must never be unwrapped (the args are
            # parameter declarations whose arity coincidentally matches).
            "char *dcgettext(const char *domainname, const char *msgid, int category) {",
            "char *dcgettext(const char *a, const char *b, int c);",
            "char *gettext(const char *m);",
        ],
    )
    def test_kept(self, src) -> None:
        assert StripTranslationWrappers().apply(src) == src

    @pytest.mark.parametrize(
        "src,expected",
        [
            # Genuine calls (incl. statement, return, and nested) still unwrap.
            ('y = dcgettext(0, "msg", 5);', 'y = "msg";'),
            ('dcgettext(0, "bare", 5);', '"bare";'),
            ('return dcgettext(0, "x", 5);', 'return "x";'),
        ],
    )
    def test_genuine_calls_still_unwrapped(self, src, expected) -> None:
        assert StripTranslationWrappers().apply(src) == expected
