# Laboratory Work 2: Regular Expression 

**Author:** Cretu Dumitru  
**Course:** Formal Languages & Finite Automata  
**Date:** March 24, 2026  
**Student:** Bulimar Rodion  
**Group:** FAF-242  

---

## 1. Introduction

Regular expressions are a compact notation for describing sets of strings, widely used in lexical analysis, text processing, and compiler design. A regular expression is built from an alphabet of symbols combined with operators such as concatenation, alternation (`|`), and repetition (`*`, `+`, `?`). This laboratory work focuses on dynamically parsing and interpreting regular expressions, then generating valid strings that conform to them — without hardcoding any generation logic for specific patterns.

---

## 2. Objectives

- Understand what regular expressions are and what they are used for.
- Implement a program that dynamically parses a given regular expression and generates valid strings from it.
- Handle all standard operators: alternation `|`, Kleene star `*`, one-or-more `+`, optional `?`, grouping `()`, and exact repetition `^N`.
- Limit repetition to a maximum of 5 iterations to avoid excessively long output.
- Implement a bonus processing-steps feature that traces every decision made during generation.

---

## 3. Regular Expressions for Variant 1

The three regular expressions assigned to Variant 1 are:

| # | Regular Expression | Description |
|---|-------------------|-------------|
| 1 | `(a\|b)(c\|d)E+G?` | One of {a,b}, then one of {c,d}, then one or more E's, then optionally G |
| 2 | `P(Q\|R\|S)T(UV\|W\|X)*Z+` | P, one of {Q,R,S}, T, zero or more of {UV,W,X}, one or more Z's |
| 3 | `1(0\|1)*2(3\|4)^5 36` | 1, zero or more binary digits, 2, exactly five of {3,4}, then 36 |

**Notation clarification:**  
The superscript `+` (written as `+` after a symbol) means *one or more repetitions*, exactly like the standard regex `+` operator. The superscript `^N` (e.g. `^5`) means *repeat exactly N times* — analogous to "to the power of N" in mathematics, but applied to string repetition.

**Expected example outputs:**

- Expression 1: `{acEG, bdE, adEEG, bcEEEEE, ...}`
- Expression 2: `{PQTUVUVZ, PRTWWWWZ, PSTZZZZ, ...}`
- Expression 3: `{1023333336, 1124444436, 10101343436, ...}`

---

## 4. Implementation

### 4.1 Architecture Overview

The program is built around a single `RegexGenerator` class that performs two phases: **parsing** and **generation**.

```
Input regex string
       │
       ▼
 _parse_expression()   ←── _parse_group() for group internals
       │
       ▼
   AST (list of tuples)
       │
       ▼
 _generate_from_parsed()  ←── _generate_repeated() for repetitions
       │
       ▼
 Generated string + processing steps log
```

The parser builds an Abstract Syntax Tree (AST) made of nested tuples:

| Tuple | Meaning |
|-------|---------|
| `('alternation', left, right)` | Pick left or right branch |
| `('star', value)` | Repeat 0 to `limit` times |
| `('plus', value)` | Repeat 1 to `limit` times |
| `('optional', value)` | Include or skip |
| `('repeat', value, N)` | Repeat exactly N times |
| `('group', content)` | Parenthesised sub-expression |
| `'x'` (plain string) | Literal character |

### 4.2 Parsing

The parser is split into two cooperating methods:

**`_parse_expression`** handles the top-level expression. It walks character by character, building the AST. When it encounters `(`, it delegates the group's interior to `_parse_group`. When it sees `|`, it collects the right side recursively and wraps both sides into an `('alternation', ...)` node.

```python
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
        # ... (other operators handled similarly)
```

**`_parse_group`** handles the interior of a `(...)` group. The key fix over a naive implementation is that it correctly handles multiple `|` alternatives by collecting each branch into a list and building a left-associative `('alternation', ...)` tree:

```python
def _parse_group(self, regex: str, pos: int) -> Tuple[List[Any], int]:
    alternatives = []
    current = []
    i = pos

    while i < len(regex) and regex[i] != ')':
        if regex[i] == '|':
            alternatives.append(current)
            current = []
            i += 1
        else:
            # parse char/quantifier/nested group into current
            ...

    alternatives.append(current)

    if len(alternatives) == 1:
        return alternatives[0], end

    # Build left-associative alternation tree
    tree = alternatives[0]
    for alt in alternatives[1:]:
        tree = [('alternation', tree, alt)]
    return tree, end
```

This correctly handles `(Q|R|S)` — three alternatives — producing a nested alternation that picks exactly one of them at generation time.

### 4.3 Generation

`_generate_from_parsed` walks the AST and produces a string by recursively resolving each node:

```python
def _generate_from_parsed(self, parsed: List[Any]) -> str:
    result = []

    for element in parsed:
        if isinstance(element, str):
            result.append(element)

        elif element[0] == 'alternation':
            _, left, right = element
            choice = random.choice([left, right])
            result.append(self._generate_from_parsed(
                choice if isinstance(choice, list) else [choice]
            ))

        elif element[0] == 'star':
            count = random.randint(0, self.limit)   # 0 to 5
            if count > 0:
                result.append(self._generate_repeated(element[1], count))

        elif element[0] == 'plus':
            count = random.randint(1, self.limit)   # 1 to 5
            result.append(self._generate_repeated(element[1], count))

        elif element[0] == 'repeat':
            _, value, count = element               # exactly N
            result.append(self._generate_repeated(value, count))

        elif element[0] == 'optional':
            if random.choice([True, False]):
                result.append(self._generate_from_parsed(...))

        elif element[0] == 'group':
            result.append(self._generate_from_parsed(element[1]))

    return ''.join(result)
```

### 4.4 Repetition Limit

Per the task requirements, any operator that implies an unbounded number of repetitions (`*` and `+`) is capped at 5. This is controlled by `self.limit = 5` passed to the constructor, so it can be adjusted without touching the generation logic.

### 4.5 Processing Steps (Bonus)

Every decision made during generation is recorded in `self.generation_steps` as a human-readable log entry. The log is printed after generation via `show_processing_steps()`. Example output for `(a|b)(c|d)E+G?`:

```
--- Generation 1 ---
  Add literal: 'a'
  Choose: a OR b -> 'a'
  Group -> 'a'
  Add literal: 'd'
  Choose: c OR d -> 'd'
  Group -> 'd'
  Repeat (1-5x) 'E' -> 3 time(s): 'EEE'
  Skip optional 'G'
```

### 4.6 Space Stripping

The third expression is written as `1(0|1)*2(3|4)^5 36` with a space that is purely visual formatting from the task description. The `generate()` method strips all spaces from the input before parsing, so this is handled automatically.

---

## 5. Results

### 5.1 Expression 1 — `(a|b)(c|d)E+G?`

```
Generated strings:
   1. adEEEEE
   2. bcEEE
   3. bcEEEEEG
   4. acEG
   5. bcEEEG
```

All strings correctly start with one of {a,b}, followed by one of {c,d}, followed by one or more E's (1–5), followed by an optional G.

### 5.2 Expression 2 — `P(Q|R|S)T(UV|W|X)*Z+`

```
Generated strings:
   1. PQTXXXXUVZ
   2. PSTXXZZZZ
   3. PSTXXWZZZ
   4. PQTZZZZ
   5. PRTZZZZ
```

All strings correctly begin with P, pick exactly one of {Q, R, S}, then T, then zero or more of {UV, W, X} repeated, then one or more Z's.

### 5.3 Expression 3 — `1(0|1)*2(3|4)^536`

```
Generated strings:
   1. 1023433436
   2. 1024334336
   3. 11111124343336
   4. 101024333336
   5. 1123343436
```

All strings start with 1, contain zero or more binary digits, then 2, then **exactly five** digits each being 3 or 4, then the literal suffix 36. The `^5` constraint is always respected.

---

## 6. Conclusions

All objectives were completed successfully. The program dynamically parses any regular expression using the operators defined in the task, with no hardcoded generation logic for specific patterns. Alternation inside groups is handled correctly by collecting all `|`-separated branches and building a proper alternation tree, the `^N` exact-repeat operator is parsed by detecting a digit immediately after `^`, the repetition limit of 5 is enforced for both `*` and `+`, and the processing-steps bonus feature traces every decision made during generation in plain English. The main difficulty encountered was correctly parsing alternation inside groups with more than two alternatives, such as `(Q|R|S)`. A naive approach that simply skips `|` produces concatenation instead of selection. The solution was to accumulate each branch as a separate list and then chain them into a left-associative `('alternation', left, right)` tree, which the generator resolves by randomly picking one branch at generation time.

---

## 7. References

1. Drumea, V. and Cojuhari, I. *Formal Languages and Finite Automata*. Technical University of Moldova, 2026.  
2. Hopcroft, J. E., Motwani, R., and Ullman, J. D. *Introduction to Automata Theory, Languages, and Computation*. 3rd ed., Addison-Wesley, 2006.  
3. Sipser, M. *Introduction to the Theory of Computation*. 3rd ed., Cengage Learning, 2012.  

---

## 8. Declaration

I hereby declare that this laboratory work is my own original work and has been completed in accordance with the academic integrity policy of the Technical University of Moldova.

**Student:** Bulimar Rodion  
**Group:** FAF-242  
**Date:** March 24, 2026  

---

*End of Report*
