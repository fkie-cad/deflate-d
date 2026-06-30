"""Tests for the `compound-assign` transform (CompoundAssignment)."""

from __future__ import annotations

import pytest

from deflated.transforms import CompoundAssignment


class TestCompoundAssignment:
    @pytest.mark.parametrize(
        "src,expected",
        [
            ("iVar1 = iVar1 + iVar4;", "iVar1 += iVar4;"),
            ("uVar3 = uVar3 - 1;", "uVar3 -= 1;"),
            ("x = x << 2;", "x <<= 2;"),
            ("flags = flags | 4;", "flags |= 4;"),
            ("*(int *)(p + i * 4) = *(int *)(p + i * 4) + 1;", "*(int *)(p + i * 4) += 1;"),
            # Remainder whose only top-level operator binds tighter than the fold
            # op still folds: `a + (b*c)` == `a += b*c`, and parens/calls are atomic.
            ("a = a + b * c;", "a += b * c;"),
            ("a = a << b + c;", "a <<= b + c;"),  # '+' binds tighter than '<<'
            ("a = a + f(x, y);", "a += f(x, y);"),
            ("a = a + (b - c);", "a += (b - c);"),
            ("a = a + -b;", "a += -b;"),  # unary minus is not an infix operator
        ],
    )
    def test_folded(self, src, expected) -> None:
        assert CompoundAssignment().apply(src) == expected

    @pytest.mark.parametrize(
        "src",
        [
            "a = b + c;",  # lhs != first rhs operand
            "a = a->b;",  # not a binary op form
            "a = a < b;",  # comparison has no compound form
            "a = a && b;",  # logical has no compound form
            "*p++ = *p++ + 1;",  # impure lvalue (side effect)
            "f(x) = f(x) + 1;",  # call in lvalue
            "a += b;",  # already compound
            "a = ab + c;",  # lhs is a prefix of rhs operand, not identical
            # Multi-term RHS whose second top-level operator binds looser-or-equal
            # to the fold op: folding would re-associate and change the result, so
            # it must be left expanded. (`a = a - b + c` is (a-b)+c, not a-(b+c).)
            "a = a - b + c;",
            "a = a * b + c;",
            "a = a / b / c;",
            "a = a & b | c;",
            "a = a + b << c;",
            "a = a + b == c;",
            "a = a + b, c;",  # comma is looser than any compound op
        ],
    )
    def test_not_folded(self, src) -> None:
        assert CompoundAssignment().apply(src) == src

    @pytest.mark.parametrize(
        "src",
        [
            "a = a - b - c;",  # a -= b - c would mean a - (b - c) = a - b + c
            "a = a / b / c;",  # a /= b / c would mean a / (b / c)
            "a = a - b + c;",  # a -= b + c would mean a - (b + c) = a - b - c
            "a = a % b % c;",  # non-associative
            "a = a << b << c;",  # non-associative
            "a = a >> b >> c;",  # non-associative
            "a = a * b + c;",  # a *= b + c would mean a * (b + c), not (a * b) + c
            "a = a & b | c;",  # a &= b | c would mean a & (b | c), not (a & b) | c
        ],
    )
    def test_non_associative_remainder_not_folded(self, src) -> None:
        # Folding `a = a OP <rest>` to `a OP= <rest>` re-groups the expression as
        # `a OP (rest)`. That only preserves meaning when the remainder binds
        # tighter than OP (or repeats an associative OP), so these must be left
        # alone rather than silently miscompiled.
        assert CompoundAssignment().apply(src) == src

    @pytest.mark.parametrize(
        "src,expected",
        [
            ("a = a + b * c;", "a += b * c;"),  # remainder binds tighter than +
            ("a = a | b & c;", "a |= b & c;"),  # & binds tighter than |
            ("a = a + p->next;", "a += p->next;"),  # -> is part of one operand
            ("a = a & b & c;", "a &= b & c;"),  # bitwise: integer-only, truly associative
            ("a = a | b | c;", "a |= b | c;"),  # bitwise associative
        ],
    )
    def test_safe_multi_operand_folded(self, src, expected) -> None:
        assert CompoundAssignment().apply(src) == expected

    @pytest.mark.parametrize(
        "src",
        [
            "a = a + b + c;",  # + is associative on ints but NOT on floats
            "a = a * b * c;",  # * likewise; a *= b * c would reassociate
        ],
    )
    def test_additive_chain_not_folded_for_float_safety(self, src) -> None:
        # `+`/`*` are associative on integers (mod 2^n) but not on floating point,
        # where reassociating `(a+b)+c` into `a+(b+c)` changes the rounded result.
        # This text-local pass cannot tell a float lvalue from an int one, so it
        # must refuse the same-precedence chain to stay lossless. (Single-term and
        # tighter-binding remainders still fold; see test above.)
        assert CompoundAssignment().apply(src) == src

    @pytest.mark.parametrize(
        "src,expected",
        [
            ("x = x >> 3;", "x >>= 3;"),
            ("n = n % m;", "n %= m;"),
            ("arr[i] = arr[i] + 1;", "arr[i] += 1;"),
            ("*p = *p + val;", "*p += val;"),
        ],
    )
    def test_additional_operators_and_lvalues(self, src, expected) -> None:
        assert CompoundAssignment().apply(src) == expected

    @pytest.mark.parametrize(
        "src,expected",
        [
            # A struct/union member access is a pure lvalue (no call, no ++/--), so
            # evaluating it once (compound form) matches the original.
            ("a.b = a.b + 1;", "a.b += 1;"),
            ("p->n = p->n | 4;", "p->n |= 4;"),
            ("s.f.g = s.f.g - 1;", "s.f.g -= 1;"),
            # Pointer difference: `p = p - q` is a pure lvalue fold, not the
            # `a = a` no-op or an `a = b - a` mismatch.
            ("p = p - q;", "p -= q;"),
            # A unary operator immediately after the fold op is part of the operand
            # and never re-associates: `a - (-b)` == `a -= -b`.
            ("a = a - -b;", "a -= -b;"),
        ],
    )
    def test_pure_member_and_pointer_lvalues_folded(self, src, expected) -> None:
        assert CompoundAssignment().apply(src) == expected

    def test_goto_label_before_assignment_folded(self) -> None:
        # A leading goto-label must not block the compound-assign rewrite.
        out = CompoundAssignment().apply("LAB: a = a + 1;")
        assert "a += 1;" in out and "LAB:" in out

    def test_string_and_comment_safety(self) -> None:
        # A foldable pattern inside a string or comment is left intact; real
        # code outside still folds.
        t = CompoundAssignment()
        assert t.apply('p = "a = a + 1;";') == 'p = "a = a + 1;";'
        assert t.apply("i = i + 1; /* a = a + 1; */") == "i += 1; /* a = a + 1; */"
