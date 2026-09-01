#!/usr/bin/env python3
"""BREAD interpreter.

BREAD is a standalone one-word programming language.

A .bread source file contains only the token ``bread``, spaces, and newlines.
The number of ``bread`` tokens on each line is a value. Some values are
instructions; instruction operands are supplied by the following line.

Most importantly, literal values are represented by repetition: 65 breads is
literally the number 65. Opcode 9 converts the top numeric value to a
character and prints it.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from typing import Any, Callable, TextIO


class BreadError(Exception):
    """Base class for BREAD errors."""


class BreadSyntaxError(BreadError):
    """Raised when source contains invalid BREAD syntax."""


class BreadRuntimeError(BreadError):
    """Raised when execution cannot continue."""


HALT = 0
PUSH = 1
ADD = 2
SUB = 3
MUL = 4
DIV = 5
MOD = 6
EQ = 7
LT = 8
PRINT_CHAR = 9
GT = 10
PRINT_NUM = 11
INPUT = 12
INPUT_CHAR = 13
IF_FALSE = 14
JUMP = 15
LOAD = 16
STORE = 17
DUP = 18
SWAP = 19
DROP = 20
AND = 21
OR = 22
NOT = 23
NE = 24
LE = 25
GE = 26
CONCAT = 27
PRINT = 28
NEWLINE = 29
CLEAR = 30
STACK_LEN = 31
TO_CHAR = 32
TO_NUM = 33

OPCODE_NAMES = {
    HALT: "HALT", PUSH: "PUSH", ADD: "ADD", SUB: "SUB", MUL: "MUL",
    DIV: "DIV", MOD: "MOD", EQ: "EQ", LT: "LT", PRINT_CHAR: "PRINT_CHAR",
    GT: "GT", PRINT_NUM: "PRINT_NUM", INPUT: "INPUT", INPUT_CHAR: "INPUT_CHAR",
    IF_FALSE: "IF_FALSE", JUMP: "JUMP", LOAD: "LOAD", STORE: "STORE",
    DUP: "DUP", SWAP: "SWAP", DROP: "DROP", AND: "AND", OR: "OR", NOT: "NOT",
    NE: "NE", LE: "LE", GE: "GE", CONCAT: "CONCAT", PRINT: "PRINT",
    NEWLINE: "NEWLINE", CLEAR: "CLEAR", STACK_LEN: "STACK_LEN", TO_CHAR: "TO_CHAR",
    TO_NUM: "TO_NUM",
}

MAX_LINE_BREADS = 1_000_000


def compile_source(source: str) -> list[int]:
    """Compile source into one integer value per physical line."""
    program: list[int] = []
    for line_no, line in enumerate(source.split("\n"), start=1):
        if "\t" in line or "\r" in line:
            raise BreadSyntaxError(
                f"line {line_no}: only spaces may separate the word 'bread'"
            )
        parts = line.split(" ")
        for token in parts:
            if token and token != "bread":
                raise BreadSyntaxError(
                    f"line {line_no}: invalid token {token!r}; expected only 'bread'"
                )
        count = sum(token == "bread" for token in parts)
        if count > MAX_LINE_BREADS:
            raise BreadSyntaxError(
                f"line {line_no}: too many breads (maximum {MAX_LINE_BREADS})"
            )
        program.append(count)
    return program


def truthy(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, (int, float)) and value == 0:
        return False
    if isinstance(value, str) and value == "":
        return False
    if isinstance(value, (list, tuple, bytes)) and not value:
        return False
    return True


def number(value: Any) -> int | float:
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return 0
        try:
            result = float(text)
        except ValueError as exc:
            raise BreadRuntimeError(f"cannot convert {value!r} to a number") from exc
        return int(result) if result.is_integer() else result
    raise BreadRuntimeError(f"cannot convert {value!r} to a number")


def character_codes(text: str) -> list[int]:
    return [ord(ch) for ch in text]


def char_from_value(value: Any) -> str:
    code = int(number(value))
    if not 0 <= code <= 0x10FFFF:
        raise BreadRuntimeError(f"character value {code} is outside Unicode range")
    if 0xD800 <= code <= 0xDFFF:
        raise BreadRuntimeError(f"character value {code} is a Unicode surrogate")
    return chr(code)


def value_to_text(value: Any) -> str:
    if isinstance(value, list):
        try:
            return "".join(char_from_value(item) for item in value)
        except (TypeError, ValueError, BreadRuntimeError) as exc:
            raise BreadRuntimeError("cannot print that list as text") from exc
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


@dataclass
class VM:
    program: list[int]
    prompt: str = "bread> "
    trace: bool = False
    input_func: Callable[[str], str] = input
    output: TextIO = sys.stdout
    stack: list[Any] = field(default_factory=list)
    memory: list[Any] = field(default_factory=lambda: [0] * 256)
    input_buffer: list[int] = field(default_factory=list)
    ip: int = 0
    halted: bool = False

    def push(self, value: Any) -> None:
        self.stack.append(value)

    def pop(self) -> Any:
        if not self.stack:
            raise BreadRuntimeError("stack underflow")
        return self.stack.pop()

    def operand(self) -> int:
        if self.ip >= len(self.program):
            raise BreadRuntimeError("missing operand at end of program")
        value = self.program[self.ip]
        self.ip += 1
        return value

    def signed_operand(self) -> int:
        value = self.operand()
        return value if value < 128 else value - 256

    def check_target(self, target: int, instruction: str) -> None:
        if target < 0 or target > len(self.program):
            raise BreadRuntimeError(
                f"{instruction} target {target} is outside the program"
            )

    def trace_line(self, op: int) -> None:
        if self.trace:
            name = OPCODE_NAMES.get(op, f"UNKNOWN({op})")
            print(
                f"[trace] ip={self.ip - 1} op={op} ({name}) stack={self.stack!r}",
                file=sys.stderr,
            )

    def dispatch(self, op: int) -> None:
        if op == HALT:
            self.halted = True
        elif op == PUSH:
            self.push(self.operand())
        elif op == ADD:
            b, a = self.pop(), self.pop()
            if isinstance(a, str) or isinstance(b, str):
                self.push(value_to_text(a) + value_to_text(b))
            else:
                self.push(number(a) + number(b))
        elif op == SUB:
            b, a = self.pop(), self.pop()
            self.push(number(a) - number(b))
        elif op == MUL:
            b, a = self.pop(), self.pop()
            self.push(number(a) * number(b))
        elif op == DIV:
            b, a = self.pop(), self.pop()
            divisor = number(b)
            if divisor == 0:
                raise BreadRuntimeError("division by zero")
            result = number(a) / divisor
            self.push(int(result) if isinstance(result, float) and result.is_integer() else result)
        elif op == MOD:
            b, a = self.pop(), self.pop()
            divisor = number(b)
            if divisor == 0:
                raise BreadRuntimeError("modulo by zero")
            self.push(number(a) % divisor)
        elif op in (EQ, NE, LT, GT, LE, GE):
            b, a = self.pop(), self.pop()
            if op == EQ:
                result = a == b
            elif op == NE:
                result = a != b
            elif op == LT:
                result = number(a) < number(b)
            elif op == GT:
                result = number(a) > number(b)
            elif op == LE:
                result = number(a) <= number(b)
            else:
                result = number(a) >= number(b)
            self.push(result)
        elif op == PRINT_CHAR:
            self.output.write(char_from_value(self.pop()))
            self.output.flush()
        elif op == PRINT_NUM:
            self.output.write(str(number(self.pop())))
            self.output.flush()
        elif op == INPUT:
            try:
                text = self.input_func(self.prompt)
            except EOFError:
                text = ""
            self.push(character_codes(text))
        elif op == INPUT_CHAR:
            if not self.input_buffer:
                try:
                    text = self.input_func(self.prompt)
                except EOFError:
                    text = ""
                self.input_buffer = character_codes(text)
            self.push(self.input_buffer.pop(0) if self.input_buffer else -1)
        elif op == IF_FALSE:
            condition = self.pop()
            offset = self.signed_operand()
            if not truthy(condition):
                target = self.ip + offset
                self.check_target(target, "IF_FALSE")
                self.ip = target
        elif op == JUMP:
            offset = self.signed_operand()
            target = self.ip + offset
            self.check_target(target, "JUMP")
            self.ip = target
        elif op == LOAD:
            address = self.operand()
            if not 0 <= address < len(self.memory):
                raise BreadRuntimeError(f"memory address {address} is out of range")
            self.push(self.memory[address])
        elif op == STORE:
            address = self.operand()
            if not 0 <= address < len(self.memory):
                raise BreadRuntimeError(f"memory address {address} is out of range")
            self.memory[address] = self.pop()
        elif op == DUP:
            if not self.stack:
                raise BreadRuntimeError("stack underflow")
            self.push(self.stack[-1])
        elif op == SWAP:
            if len(self.stack) < 2:
                raise BreadRuntimeError("stack underflow")
            self.stack[-1], self.stack[-2] = self.stack[-2], self.stack[-1]
        elif op == DROP:
            self.pop()
        elif op == AND:
            b, a = self.pop(), self.pop()
            self.push(truthy(a) and truthy(b))
        elif op == OR:
            b, a = self.pop(), self.pop()
            self.push(truthy(a) or truthy(b))
        elif op == NOT:
            self.push(not truthy(self.pop()))
        elif op == CONCAT:
            b, a = self.pop(), self.pop()
            self.push(value_to_text(a) + value_to_text(b))
        elif op == PRINT:
            self.output.write(value_to_text(self.pop()))
            self.output.flush()
        elif op == NEWLINE:
            self.output.write("\n")
            self.output.flush()
        elif op == CLEAR:
            self.stack.clear()
        elif op == STACK_LEN:
            self.push(len(self.stack))
        elif op == TO_CHAR:
            self.push(char_from_value(self.pop()))
        elif op == TO_NUM:
            self.push(number(self.pop()))
        else:
            raise BreadRuntimeError(f"unknown opcode {op}")

    def run(self) -> Any:
        while not self.halted:
            if self.ip >= len(self.program):
                raise BreadRuntimeError("program ended without HALT")
            op = self.program[self.ip]
            self.ip += 1
            self.trace_line(op)
            self.dispatch(op)
        return self.stack[-1] if self.stack else None


def run_source(
    source: str,
    *,
    prompt: str = "bread> ",
    trace: bool = False,
    input_func: Callable[[str], str] = input,
    output: TextIO = sys.stdout,
) -> Any:
    return VM(
        compile_source(source),
        prompt=prompt,
        trace=trace,
        input_func=input_func,
        output=output,
    ).run()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a .bread program.")
    parser.add_argument("file", help="path to a .bread source file")
    parser.add_argument(
        "-p", "--prompt", default="bread> ", help="prompt used by INPUT instructions"
    )
    parser.add_argument(
        "--trace", action="store_true", help="show instruction execution on stderr"
    )
    args = parser.parse_args(argv)

    try:
        with open(args.file, "r", encoding="utf-8") as handle:
            source = handle.read()
        run_source(source, prompt=args.prompt, trace=args.trace)
    except (OSError, BreadError) as exc:
        print(f"BREAD error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
