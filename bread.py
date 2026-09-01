#!/usr/bin/env python3
"""
BREAD - a bread-only implementation of the Chicken esoteric language.

A .bread source file contains only the token "bread", spaces, and newlines.
The number of breads on each line is an instruction/opcode.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import Any


class BreadError(Exception):
    """Base class for BREAD errors."""


class BreadSyntaxError(BreadError):
    """Raised when source contains invalid characters/tokens."""


class BreadRuntimeError(BreadError):
    """Raised when execution cannot continue."""


# Chicken/BREAD opcode table.
EXIT = 0       # axe
BREAD = 1      # chicken
ADD = 2
SUB = 3
MUL = 4
CMP = 5
LOAD = 6
STORE = 7
JUMP = 8
CHAR = 9       # BBQ
LITERAL_BASE = 10


def compile_source(source: str) -> list[int]:
    """Compile BREAD source into numeric instructions.

    Every physical line is significant. A blank line is opcode 0 (EXIT).
    Only lowercase ``bread`` separated by literal spaces is accepted.
    """
    lines = source.split("\n")
    program: list[int] = []

    for line_no, line in enumerate(lines, start=1):
        if "\t" in line or "\r" in line:
            raise BreadSyntaxError(
                f"invalid whitespace on line {line_no}; use spaces only"
            )

        parts = line.split(" ")
        bad = [part for part in parts if part and part != "bread"]
        if bad:
            raise BreadSyntaxError(
                f"invalid token on line {line_no}: {bad[0]!r}; expected 'bread'"
            )

        program.append(sum(part == "bread" for part in parts))

    return program


def _js_number(value: Any) -> int | float:
    """Numeric conversion for the primitive values BREAD can create."""
    if value is None:
        return 0
    if value is True:
        return 1
    if value is False:
        return 0
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if stripped == "":
            return 0
        try:
            number = float(stripped)
        except ValueError as exc:
            raise BreadRuntimeError(
                f"cannot convert {value!r} to a number"
            ) from exc
        return int(number) if number.is_integer() else number
    raise BreadRuntimeError(f"cannot convert {value!r} to a number")


def _js_add(a: Any, b: Any) -> Any:
    """Match Chicken's JavaScript-style + behavior for strings/numbers."""
    if isinstance(a, str) or isinstance(b, str):
        return f"{a}{b}"
    return _js_number(a) + _js_number(b)


def _truthy(value: Any) -> bool:
    """Truthiness for values used by the Chicken semantics."""
    if value is None or value is False:
        return False
    if isinstance(value, (int, float)) and value == 0:
        return False
    if isinstance(value, str) and value == "":
        return False
    return True


@dataclass
class VM:
    """Shared-stack virtual machine matching the documented Chicken model."""

    program: list[int]
    user_input: str = ""
    trace: bool = False

    def __post_init__(self) -> None:
        # Three non-isolated stack segments:
        #   [0] reference to the complete VM stack
        #   [1] user input
        #   [2:] code, followed by a terminating EXIT
        self.stack: list[Any] = []
        self.stack.append(self.stack)
        self.stack.append(self.user_input)
        self.stack.extend(self.program)
        self.stack.append(EXIT)

        self.ip = 2
        self.data_start = len(self.stack)
        self.halted = False

    @property
    def data_stack(self) -> list[Any]:
        return self.stack[self.data_start :]

    def push(self, value: Any) -> None:
        self.stack.append(value)

    def pop(self) -> Any:
        if not self.stack:
            raise BreadRuntimeError("stack underflow")
        return self.stack.pop()

    def next_token(self) -> Any:
        if self.ip < 0 or self.ip >= len(self.stack):
            raise BreadRuntimeError(
                f"instruction pointer out of range: {self.ip}"
            )
        token = self.stack[self.ip]
        self.ip += 1
        return token

    def dispatch(self, op: Any) -> None:
        if op == EXIT:
            self.halted = True

        elif op == BREAD:
            self.push("bread")

        elif op == ADD:
            b = self.pop()
            a = self.pop()
            self.push(_js_add(a, b))

        elif op == SUB:
            b = self.pop()
            a = self.pop()
            self.push(_js_number(a) - _js_number(b))

        elif op == MUL:
            b = self.pop()
            a = self.pop()
            self.push(_js_number(a) * _js_number(b))

        elif op == CMP:
            b = self.pop()
            a = self.pop()
            self.push(a == b)

        elif op == LOAD:
            # Double-wide instruction. The next instruction selects source:
            # 0 = complete VM stack, 1 = user input.
            source_id = self.next_token()
            if source_id not in (0, 1):
                raise BreadRuntimeError(
                    f"LOAD source must be 0 or 1, got {source_id!r}"
                )

            index_value = self.pop()
            index = int(_js_number(index_value))
            source = self.stack[source_id]
            try:
                self.push(source[index])
            except (IndexError, TypeError) as exc:
                raise BreadRuntimeError(
                    f"invalid LOAD index {index} from source {source_id}"
                ) from exc

        elif op == STORE:
            address_value = self.pop()
            value = self.pop()
            address = int(_js_number(address_value))
            if address < 0 or address >= len(self.stack):
                raise BreadRuntimeError(
                    f"STORE address out of range: {address}"
                )
            self.stack[address] = value

        elif op == JUMP:
            offset_value = self.pop()
            condition = self.pop()
            if _truthy(condition):
                self.ip += int(_js_number(offset_value))

        elif op == CHAR:
            value = int(_js_number(self.pop()))
            if not 0 <= value <= 127:
                raise BreadRuntimeError(
                    f"ASCII value out of range for BBQ: {value}"
                )
            self.push(chr(value))

        elif isinstance(op, int) and op >= LITERAL_BASE:
            # n >= 10 pushes literal n-10.
            self.push(op - LITERAL_BASE)

        else:
            raise BreadRuntimeError(f"invalid opcode/token: {op!r}")

    def run(self) -> Any:
        """Execute until EXIT and return the top value on the data stack."""
        while not self.halted:
            if self.ip < 0 or self.ip >= len(self.stack):
                raise BreadRuntimeError(
                    f"instruction pointer out of range: {self.ip}"
                )

            op = self.next_token()
            if self.trace:
                print(
                    f"[trace] ip={self.ip - 1} op={op!r} "
                    f"stack={self.data_stack!r}",
                    file=sys.stderr,
                )
            self.dispatch(op)

        return self.data_stack[-1] if self.data_stack else ""


def run_source(source: str, user_input: str = "", trace: bool = False) -> Any:
    """Compile and execute BREAD source."""
    return VM(compile_source(source), user_input=user_input, trace=trace).run()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="bread.py",
        description="Interpret a .bread program.",
    )
    parser.add_argument("file", help="path to a .bread source file")
    parser.add_argument(
        "-i",
        "--input",
        default="",
        help="value supplied as BREAD's input register",
    )
    parser.add_argument(
        "--trace",
        action="store_true",
        help="show VM execution details on stderr",
    )
    args = parser.parse_args(argv)

    try:
        with open(args.file, "r", encoding="utf-8", newline="") as handle:
            source = handle.read()
        result = run_source(source, args.input, args.trace)
    except (OSError, BreadError) as exc:
        print(f"BREAD error: {exc}", file=sys.stderr)
        return 1

    # The browser Chicken implementation exposes the final VM value.
    # CHAR turns an ASCII value into printable character data.
    if isinstance(result, str):
        sys.stdout.write(result)
    elif isinstance(result, bool):
        sys.stdout.write("true" if result else "false")
    else:
        sys.stdout.write(str(result))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
