# 🍞 BREAD

BREAD is a standalone esoteric programming language where the only word allowed in source code is **`bread`**.

Every physical line is a number: the number of `bread` tokens on that line. That number is either an opcode or, immediately after an opcode that takes an operand, a literal value.

The important rule is simple:

> **The repetition count is the value.**

That makes ASCII programs especially fun: `65` breads means the number `65`, and `10` breads is the `PRINT_CHAR` instruction.

## Run it

```bash
python3 bread.py examples/hello.bread
```

An input program can ask for normal user input. The user types ordinary text; **you do not type `bread`**:

```bash
python3 bread.py examples/input.bread
```

BREAD converts each entered character into its character-code value internally.

For instruction tracing:

```bash
python3 bread.py examples/hello.bread --trace
```

## Source rules

A `.bread` file may contain only the exact lowercase word `bread`, spaces, and newlines.

The number of `bread` tokens on each line is significant. Blank lines are opcode `0` (`HALT`).

There are no keywords, punctuation marks, quotes, or normal numeric literals in BREAD source.

## Instruction set

| Breads | Instruction | Description |
|---:|---|---|
| 0 | `HALT` | Stop execution. |
| 1 | `PUSH` | Read the next line as a value and push it. |
| 2 | `ADD` | Pop two values and add them. Strings are concatenated. |
| 3 | `SUB` | `a - b`. |
| 4 | `MUL` | Multiply two numeric values. |
| 5 | `DIV` | Divide `a / b`. |
| 6 | `MOD` | Remainder of `a / b`. |
| 7 | `EQ` | Push `true` if two values are equal. |
| 8 | `LT` | Push `true` if `a < b`. |
| 9 | `GT` | Push `true` if `a > b`. |
| 10 | `PRINT_CHAR` | Pop a number and print it as a character. |
| 11 | `PRINT_NUM` | Pop a value and print it as a number. |
| 12 | `INPUT` | Read one line from the user and push its character codes as a list. |
| 13 | `INPUT_CHAR` | Read a line when needed, then return its characters one at a time as character codes. |
| 14 | `IF_FALSE` | Pop a condition. The next line is a relative signed jump offset used only when the condition is false. |
| 15 | `JUMP` | The next line is a relative signed jump offset. |
| 16 | `LOAD` | The next line is a 0-255 memory address; push its value. |
| 17 | `STORE` | The next line is a 0-255 memory address; pop a value and store it there. |
| 18 | `DUP` | Duplicate the top stack value. |
| 19 | `SWAP` | Swap the top two stack values. |
| 20 | `DROP` | Remove the top stack value. |
| 21 | `AND` | Boolean AND. |
| 22 | `OR` | Boolean OR. |
| 23 | `NOT` | Boolean NOT. |
| 24 | `NE` | Not equal. |
| 25 | `LE` | Less than or equal. |
| 26 | `GE` | Greater than or equal. |
| 27 | `CONCAT` | Concatenate two values as text. |
| 28 | `PRINT` | Print a string, list of character codes, number, or boolean. |
| 29 | `NEWLINE` | Print a newline. |
| 30 | `CLEAR` | Clear the data stack. |
| 31 | `STACK_LEN` | Push the current stack length. |
| 32 | `TO_CHAR` | Convert a numeric value to a character without printing it. |
| 33 | `TO_NUM` | Convert a value to a number. |

Opcodes 34-255 are reserved for future BREAD features.

## ASCII and printing

BREAD intentionally makes repetition count the value.

For example, ASCII `A` is `65`.

To print `A`, use `PUSH` (`1 bread`), put `65` breads on the next line, then use `PRINT_CHAR` (`10 breads`):

```text
bread
bread bread bread bread bread ...
bread bread bread bread bread bread bread bread bread bread
```

The middle line must contain exactly 65 repetitions. The `...` above is explanatory and is **not** valid BREAD syntax.

For a whole string, repeat the `PUSH`, ASCII-value, `PRINT_CHAR` pattern for every character.

## IF statements

BREAD has a real conditional jump.

`IF_FALSE` consumes the condition from the stack and then reads the next line as a **signed relative offset**.

Offsets `0-127` are zero or positive. Offsets `128-255` represent negative values by subtracting 256. For example, `3` means jump forward 3 instructions, `255` means jump backward 1 instruction, and `236` means jump backward 20 instructions.

That gives BREAD normal `if`/`else` control flow when combined with `JUMP`.

## User input

`INPUT` is the normal string-input instruction.

When the program reaches `INPUT`, `bread.py` asks the user for a line such as:

```text
bread> hello world
```

The user types **`hello world`**, not a BREAD program.

The interpreter converts each entered character into its character-code value and pushes the resulting list onto the stack. `PRINT` can print the entire list back as text.

`INPUT_CHAR` keeps an internal input buffer, so multiple `INPUT_CHAR` instructions consume the same line one character at a time before another prompt appears.

## Memory and variables

BREAD has 256 memory cells, addressed `0` through `255`.

`STORE` writes the top stack value to an address supplied by its next line. `LOAD` retrieves the value from an address supplied by its next line.

This gives BREAD reusable variables without adding variable names to the one-word syntax.

## Loops

There is no separate `WHILE` keyword. Loops are built from comparisons, `IF_FALSE`, `JUMP`, and memory. This keeps the language tiny while still allowing finite loops and programs that run indefinitely.

## Example programs

- `examples/hello.bread` prints `Hello, bread!`
- `examples/input.bread` reads and echoes a line of user input
- `examples/if.bread` demonstrates a conditional
- `examples/countdown.bread` demonstrates memory plus a loop

## Testing

Run the test suite with:

```bash
python3 -m unittest discover -s tests
```

## Interpreter

`bread.py` is a standalone interpreter. It does not translate BREAD into another language and needs only Python 3.10+ from the standard library.

## License

Use, modify, and experiment with it however you like.
