import random
from typing import List, Any, Tuple


class RegexGenerator:
    def __init__(self, limit: int = 5):
        self.limit = limit
        self.generation_steps = []

    def clear_steps(self):
        self.generation_steps = []

    def generate(self, regex: str, num_examples: int = 5) -> List[str]:
        self.clear_steps()
        regex = regex.replace(' ', '')
        examples = []
        for i in range(num_examples):
            self.generation_steps.append(f"\n--- Generation {i + 1} ---")
            parsed = self._parse_expression(regex, 0)[0]
            result = self._generate_from_parsed(parsed)
            examples.append(result)
        return examples

    def _parse_expression(self, regex: str, pos: int) -> Tuple[List[Any], int]:
        result = []
        i = pos

        while i < len(regex):
            char = regex[i]

            if char == '|':
                i += 1
                right_side, i = self._parse_expression(regex, i)
                result = [('alternation', result, right_side)]
                break  

            elif char == '*':
                if result:
                    last = result.pop()
                    result.append(('star', last))
                i += 1

            elif char == '+':
                if result:
                    last = result.pop()
                    result.append(('plus', last))
                i += 1

            elif char == '?':
                if result:
                    last = result.pop()
                    result.append(('optional', last))
                i += 1

            elif char == '^':
                if i + 1 < len(regex) and regex[i + 1].isdigit():
                    count = int(regex[i + 1])
                    i += 2
                    if result:
                        last = result.pop()
                        result.append(('repeat', last, count))
                else:
                    result.append('^')
                    i += 1

            elif char == '(':
                group_content, i = self._parse_group(regex, i + 1)
                if i < len(regex) and regex[i] in ['*', '+', '?']:
                    quantifier = regex[i]
                    group = ('group', group_content)
                    if quantifier == '*':
                        result.append(('star', group))
                    elif quantifier == '+':
                        result.append(('plus', group))
                    elif quantifier == '?':
                        result.append(('optional', group))
                    i += 1
                elif i < len(regex) and regex[i] == '^' and i + 1 < len(regex) and regex[i + 1].isdigit():
                    count = int(regex[i + 1])
                    i += 2
                    result.append(('repeat', ('group', group_content), count))
                else:
                    result.append(('group', group_content))

            elif char == ')':
                break

            else:
                result.append(char)
                i += 1

        return result, i

    def _parse_group(self, regex: str, pos: int) -> Tuple[List[Any], int]:
        alternatives: List[List[Any]] = []
        current: List[Any] = []
        i = pos

        while i < len(regex) and regex[i] != ')':
            char = regex[i]

            if char == '|':
                alternatives.append(current)
                current = []
                i += 1

            elif char == '*':
                if current:
                    last = current.pop()
                    current.append(('star', last))
                i += 1

            elif char == '+':
                if current:
                    last = current.pop()
                    current.append(('plus', last))
                i += 1

            elif char == '?':
                if current:
                    last = current.pop()
                    current.append(('optional', last))
                i += 1

            elif char == '^':
                if i + 1 < len(regex) and regex[i + 1].isdigit():
                    count = int(regex[i + 1])
                    i += 2
                    if current:
                        last = current.pop()
                        current.append(('repeat', last, count))
                else:
                    current.append('^')
                    i += 1

            elif char == '(':
                nested_content, i = self._parse_group(regex, i + 1)
                if i < len(regex) and regex[i] in ['*', '+', '?']:
                    quantifier = regex[i]
                    group = ('group', nested_content)
                    if quantifier == '*':
                        current.append(('star', group))
                    elif quantifier == '+':
                        current.append(('plus', group))
                    elif quantifier == '?':
                        current.append(('optional', group))
                    i += 1
                elif i < len(regex) and regex[i] == '^' and i + 1 < len(regex) and regex[i + 1].isdigit():
                    count = int(regex[i + 1])
                    i += 2
                    current.append(('repeat', ('group', nested_content), count))
                else:
                    current.append(('group', nested_content))

            else:
                current.append(char)
                i += 1

        alternatives.append(current)
        end = i + 1 if i < len(regex) else i  

        if len(alternatives) == 1:
            return alternatives[0], end

        tree: Any = alternatives[0]
        for alt in alternatives[1:]:
            tree = [('alternation', tree, alt)]
        return tree, end

    def _generate_from_parsed(self, parsed: List[Any]) -> str:
        result = []

        for element in parsed:
            if isinstance(element, str):
                result.append(element)
                self.generation_steps.append(f"  Add literal: '{element}'")

            elif isinstance(element, tuple):
                op = element[0]

                if op == 'alternation':
                    _, left, right = element
                    choice = random.choice([left, right])
                    generated = self._generate_from_parsed(
                        choice if isinstance(choice, list) else [choice]
                    )
                    result.append(generated)
                    self.generation_steps.append(
                        f"  Choose: {self._format_element(left)} OR "
                        f"{self._format_element(right)} -> '{generated}'"
                    )

                elif op == 'star':
                    _, value = element
                    count = random.randint(0, self.limit)
                    if count > 0:
                        generated = self._generate_repeated(value, count)
                        result.append(generated)
                        self.generation_steps.append(
                            f"  Repeat (0–{self.limit}×) '{self._format_element(value)}' "
                            f"-> {count} time(s): '{generated}'"
                        )
                    else:
                        self.generation_steps.append(
                            f"  Skip (0×) '{self._format_element(value)}'"
                        )

                elif op == 'plus':
                    _, value = element
                    count = random.randint(1, self.limit)
                    generated = self._generate_repeated(value, count)
                    result.append(generated)
                    self.generation_steps.append(
                        f"  Repeat (1–{self.limit}×) '{self._format_element(value)}' "
                        f"-> {count} time(s): '{generated}'"
                    )

                elif op == 'optional':
                    _, value = element
                    if random.choice([True, False]):
                        generated = self._generate_from_parsed(
                            value if isinstance(value, list) else [value]
                        )
                        result.append(generated)
                        self.generation_steps.append(
                            f"  Include optional '{self._format_element(value)}' -> '{generated}'"
                        )
                    else:
                        self.generation_steps.append(
                            f"  Skip optional '{self._format_element(value)}'"
                        )

                elif op == 'repeat':
                    _, value, count = element
                    generated = self._generate_repeated(value, count)
                    result.append(generated)
                    self.generation_steps.append(
                        f"  Repeat exactly {count}× '{self._format_element(value)}' -> '{generated}'"
                    )

                elif op == 'group':
                    _, content = element
                    generated = self._generate_from_parsed(
                        content if isinstance(content, list) else [content]
                    )
                    result.append(generated)
                    self.generation_steps.append(f"  Group -> '{generated}'")

        return ''.join(result)

    def _generate_repeated(self, element: Any, count: int) -> str:
        parts = []
        for _ in range(count):
            if isinstance(element, str):
                parts.append(element)
            elif isinstance(element, tuple):
                if element[0] == 'alternation':
                    _, left, right = element
                    choice = random.choice([left, right])
                    parts.append(self._generate_from_parsed(
                        choice if isinstance(choice, list) else [choice]
                    ))
                elif element[0] == 'group':
                    _, content = element
                    parts.append(self._generate_from_parsed(
                        content if isinstance(content, list) else [content]
                    ))
                else:
                    parts.append(self._generate_from_parsed([element]))
            elif isinstance(element, list):
                parts.append(self._generate_from_parsed(element))
        return ''.join(parts)

    def _format_element(self, element: Any) -> str:
        if isinstance(element, str):
            return element
        elif isinstance(element, tuple):
            op = element[0]
            if op == 'group':
                return f"({self._format_element(element[1])})"
            elif op == 'alternation':
                return f"({self._format_element(element[1])}|{self._format_element(element[2])})"
            elif op == 'repeat':
                return f"{self._format_element(element[1])}^{element[2]}"
            else:
                symbols = {'star': '*', 'plus': '+', 'optional': '?'}
                return f"{self._format_element(element[1])}{symbols.get(op, op)}"
        elif isinstance(element, list):
            return ''.join(self._format_element(e) for e in element)
        return str(element)

    def show_processing_steps(self) -> None:
        print("\n" + "=" * 60)
        print("PROCESSING STEPS:")
        print("=" * 60)
        for step in self.generation_steps:
            print(step)
        print("=" * 60)

def main():
    regexes = [
        "(a|b)(c|d)E+G?",
        "P(Q|R|S)T(UV|W|X)*Z+",
        "1(0|1)*2(3|4)^536",
    ]

    generator = RegexGenerator(limit=5)

    for idx, regex in enumerate(regexes, 1):
        print(f"\n{'=' * 70}")
        print(f"REGULAR EXPRESSION {idx}: {regex}")
        print('=' * 70)

        examples = generator.generate(regex, num_examples=5)

        print("\nGenerated strings:")
        for i, example in enumerate(examples, 1):
            print(f"   {i}. {example}")

        print("\nProcessing steps (last generation):")
        generator.show_processing_steps()

    print(f"\n{'=' * 70}")


if __name__ == "__main__":
    print("=" * 70)
    print("REGULAR EXPRESSION STRING GENERATOR")
    print("Generating valid strings from given regex patterns")
    print("=" * 70)
    main()