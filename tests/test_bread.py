import io
import unittest

from bread import BreadRuntimeError, BreadSyntaxError, run_source


def b(n: int) -> str:
    return " ".join(["bread"] * n)


def program(*lines: int) -> str:
    return "\n".join(b(n) for n in lines) + "\n"


class BreadTests(unittest.TestCase):
    def run_program(self, source: str, input_values=None):
        output = io.StringIO()
        values = iter(input_values or [])
        result = run_source(
            source,
            input_func=lambda prompt: next(values),
            output=output,
        )
        return result, output.getvalue()

    def test_only_bread_source_is_valid(self):
        self.assertEqual(run_source(program(0)), None)
        with self.assertRaises(BreadSyntaxError):
            run_source("bread chicken\n")

    def test_ascii_character(self):
        _, output = self.run_program(program(1, 65, 10, 0))
        self.assertEqual(output, "A")

    def test_number_output(self):
        _, output = self.run_program(program(1, 42, 11, 0))
        self.assertEqual(output, "42")

    def test_arithmetic(self):
        # (20 + 5) * 2 - 10 = 40
        source = program(1, 20, 1, 5, 2, 1, 2, 4, 1, 10, 3, 11, 0)
        _, output = self.run_program(source)
        self.assertEqual(output, "40")

    def test_division_and_modulo(self):
        source = program(1, 20, 1, 6, 5, 11, 0)
        _, output = self.run_program(source)
        self.assertEqual(output, "3.3333333333333335")

        source = program(1, 20, 1, 6, 6, 11, 0)
        _, output = self.run_program(source)
        self.assertEqual(output, "2")

    def test_comparisons_and_boolean_logic(self):
        source = program(
            1, 7, 1, 7, 7,
            1, 9, 1, 3, 9,
            21,
            1, 0, 23,
            22,
            11, 0,
        )
        _, output = self.run_program(source)
        self.assertEqual(output, "true")

    def test_stack_operations(self):
        source = program(1, 3, 18, 1, 4, 19, 11, 0)
        _, output = self.run_program(source)
        self.assertEqual(output, "3")

    def test_memory(self):
        source = program(1, 99, 17, 12, 16, 12, 11, 0)
        _, output = self.run_program(source)
        self.assertEqual(output, "99")

    def test_if_false(self):
        source = program(
            1, 7, 1, 8, 7,
            14, 3,
            1, 89, 10,
            0,
        )
        _, output = self.run_program(source)
        self.assertEqual(output, "")

    def test_loop(self):
        source = program(
            1, 3, 17, 0,
            16, 0, 11, 29,
            16, 0, 1, 1, 3, 17, 0,
            16, 0, 1, 0, 9, 14, 3,
            15, 236, 0,
        )
        _, output = self.run_program(source)
        self.assertEqual(output, "3\n2\n1\n")

    def test_input_line(self):
        _, output = self.run_program(program(12, 28, 0), ["hello"])
        self.assertEqual(output, "hello")

    def test_input_char_buffer(self):
        _, output = self.run_program(
            program(13, 10, 13, 10, 13, 10, 0), ["ABC"]
        )
        self.assertEqual(output, "ABC")

    def test_runtime_errors(self):
        with self.assertRaises(BreadRuntimeError):
            run_source(program(2, 0))
        with self.assertRaises(BreadRuntimeError):
            run_source(program(1, 10, 1, 0, 5, 0))


if __name__ == "__main__":
    unittest.main()
