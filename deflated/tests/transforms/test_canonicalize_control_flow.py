"""Tests for the `cfg-canon` transform (CanonicalizeControlFlow)."""

from __future__ import annotations

import pytest

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

    def test_dead_goto_before_several_labels_removed(self) -> None:
        # `goto A;` falls through to `A:` even with another label in between.
        out = CanonicalizeControlFlow().apply("goto A; B: A: x = 1;")
        assert "goto" not in out and ":" not in out and "x = 1;" in out

    def test_chain_of_dead_gotos_removed(self) -> None:
        # Once `goto B;` is gone, `goto A;` is directly followed by `B: A:` and is dead too.
        out = CanonicalizeControlFlow().apply("goto A; goto B; B: A: x = 1;")
        assert "goto" not in out and ":" not in out and "x = 1;" in out

    def test_every_unused_label_removed(self) -> None:
        # `B:` is unused even though it is not the first label of its statement.
        out = CanonicalizeControlFlow().apply("A: B: y = 1; goto A;")
        assert "B:" not in out and "A: y = 1;" in out

    def test_goto_to_later_label_kept(self) -> None:
        # `A:` is not in front of the next statement, so the goto skips `x = 1;` and must stay.
        out = CanonicalizeControlFlow().apply("goto A; B: x = 1; A: y = 2;")
        assert "goto A;" in out and "A:" in out

    @pytest.mark.parametrize(
        "src",
        [
            "void f(void) {\n  goto A;\nB:\nA:\n  x = 1;\n}\n",
            "void f(void) {\n  goto A;\n  goto B;\nB:\nA:\n  x = 1;\n}\n",
            "void f(void) {\n  goto A;\nB:\n  goto C;\nC:\nA:\n  x = 1;\n}\n",
        ],
    )
    def test_one_pass_reaches_fixed_point(self, src) -> None:
        once = CanonicalizeControlFlow().apply(src)
        assert CanonicalizeControlFlow().apply(once) == once
