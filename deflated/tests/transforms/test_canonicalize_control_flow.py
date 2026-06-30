"""Tests for the `cfg-canon` transform (CanonicalizeControlFlow)."""

from __future__ import annotations

from deflated.transforms import CanonicalizeControlFlow


class TestCanonicalizeControlFlow:
    def test_dead_forward_goto_removed(self) -> None:
        c = CanonicalizeControlFlow()
        out = c.apply("x = 1; goto L; L: y = 2;")
        assert "goto" not in out and "y = 2;" in out

    def test_unreferenced_label_dropped(self) -> None:
        c = CanonicalizeControlFlow()
        out = c.apply("L: x = 1;")
        assert "L:" not in out and "x = 1;" in out

    def test_referenced_label_and_goto_kept(self) -> None:
        c = CanonicalizeControlFlow()
        out = c.apply("if (c) goto L; x = 1; L: y = 2;")
        assert "L:" in out and "goto L;" in out

    def test_default_label_never_dropped(self) -> None:
        c = CanonicalizeControlFlow()
        out = c.apply("switch (x) { default: y = 1; }")
        assert "default:" in out

    def test_case_label_never_dropped(self) -> None:
        c = CanonicalizeControlFlow()
        out = c.apply("switch (x) { case 1: y = 1; }")
        assert "case" in out

    def test_dead_goto_and_now_unreferenced_label_both_removed(self) -> None:
        # After the dead goto is dropped, L has no remaining references and
        # must be stripped by the second (unreferenced-label) phase.
        c = CanonicalizeControlFlow()
        out = c.apply("x = 1; goto L; L: y = 2;")
        assert "goto" not in out and "L:" not in out and "y = 2;" in out

    def test_goto_inside_string_not_counted_as_reference(self) -> None:
        # A "goto L" buried in a string literal must not protect label L.
        c = CanonicalizeControlFlow()
        out = c.apply('s = "goto L"; L: y = 2;')
        assert "L:" not in out and '"goto L"' in out

    def test_computed_goto_label_address_keeps_label(self) -> None:
        # A label referenced by GCC's label-address operator `&&L` (for a computed
        # `goto *p`) must NOT be dropped, or the `&&L` reference dangles (invalid C).
        c = CanonicalizeControlFlow()
        out = c.apply("void *p = &&L1; L1: x = 1; goto *p;")
        assert "L1:" in out
