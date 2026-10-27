def calculate(a: float, b: float, operation: str) -> float:
    """Perform arithmetic on two numbers.

    Args:
        a: First number.
        b: Second number.
        operation: One of add, subtract, multiply, divide.
    """
    if operation == "add":
        return a + b

    elif operation == "subtract":
        return a - b

    elif operation == "multiply":
        return a * b

    elif operation == "divide":
        if b == 0:
            raise ValueError("Cannot divide by zero.")
        return a / b

    else:
        raise ValueError(f"Unsupported operation: {operation}")
