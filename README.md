# 🍞 BREAD

A programming language consisting of the repetitive use of one word: **`bread`**.

BREAD is essentially Chicken with its vocabulary changed from `chicken` to `bread`. The implementation in `bread.py` is an independent reimplementation of Chicken's documented stack-machine behavior rather than a copy of another interpreter's source.

## Run it

```bash
python3 bread.py examples/hello.bread
```

Give the program a value in its input register:

```bash
python3 bread.py examples/input.bread --input "Hello"
```

For VM tracing:

```bash
python3 bread.py examples/hello.bread --trace
```

## The language

A `.bread` file contains only the word `bread`, spaces, and newlines. The number of `bread` tokens on each line becomes one opcode. Blank lines are significant and act as opcode `0` / exit.

| Breads | Instruction | Meaning |
|---:|---|---|
| 0 | axe / exit | Stop execution. |
| 1 | bread / chicken | Push the string `bread`. |
| 2 | add | Add the top two values; strings concatenate. |
| 3 | fox / subtract | Subtract the top value from the next value. |
| 4 | rooster / multiply | Multiply the top two numeric values. |
| 5 | compare | Push whether the top two values are equal. |
| 6 | pick / load | Double-wide: next instruction selects source `0` = VM stack or `1` = input; the top value is the index. |
| 7 | peck / store | Store the value below the top at the address on top. |
| 8 | fr / jump | Pop an offset and condition; move the instruction pointer when the condition is truthy. |
| 9 | BBQ / char | Convert the top numeric value to its ASCII character. |
| 10+ | literal | Push `breads - 10`. |

## Printing

There is no dedicated `print` instruction. In Chicken/BREAD, a number is converted into a character with opcode `9`, so ASCII output is built from repetition counts.

For example, ASCII `A` is `65`. The instruction that pushes `65` is therefore a line containing **75 breads**, followed by a line containing **9 breads** to convert it to `A`.

The interpreter writes the final value left on the data stack to standard output. Using opcode `1` repeatedly and `2` (`add`) lets programs construct strings such as `bread`, while opcode `9` turns ASCII values into characters.

## VM model

The VM uses one shared underlying stack. It starts with a self-reference to that stack and the user input, then stores the program directly in the same structure, followed by an automatic exit cell. Because code and data share storage, `STORE` can modify instructions and `LOAD` can inspect program memory, preserving Chicken's self-modifying design.

## Files

- `bread.py` — interpreter
- `examples/hello.bread` — Hello World example
- `examples/input.bread` — reads the first character of the supplied input

## Reference

The instruction set and VM model follow the published Chicken specification and the original implementation's documented behavior. Chicken was created by Torbjörn Söderstedt and is a Turing-complete, stack-based esoteric language.
