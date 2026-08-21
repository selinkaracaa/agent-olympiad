import math
import sys


def solve(data: str) -> str:
    tokens = iter(data.split())
    rows = []
    case = 0
    while True:
        try:
            degree = int(next(tokens))
        except StopIteration:
            break
        coefficients = [float(next(tokens)) for _ in range(degree + 1)]
        low = float(next(tokens))
        high = float(next(tokens))
        increment = int(next(tokens))
        case += 1

        squared = [0.0] * (2 * degree + 1)
        for left, left_value in enumerate(coefficients):
            for right, right_value in enumerate(coefficients):
                squared[left + right] += left_value * right_value

        def volume(at: float) -> float:
            integral = sum(
                coefficient
                * (at ** (power + 1) - low ** (power + 1))
                / (power + 1)
                for power, coefficient in enumerate(squared)
            )
            return math.pi * integral

        total = volume(high)
        rows.append(f"Case {case}: {total:.2f}")
        marks = []
        for number in range(1, 9):
            target = number * increment
            if target >= total:
                break
            left, right = low, high
            for _ in range(100):
                middle = (left + right) / 2
                if volume(middle) < target:
                    left = middle
                else:
                    right = middle
            marks.append(f"{(left + right) / 2 - low:.2f}")
        rows.append(" ".join(marks) if marks else "insufficient volume")
    return "\n".join(rows)


if __name__ == "__main__":
    print(solve(sys.stdin.read()))
