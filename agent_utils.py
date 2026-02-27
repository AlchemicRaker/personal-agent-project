def multiply_then_add(a, b, c):
    """
    Multiplies two inputs together, then adds a third input.
    
    Args:
        a (int/float): First number
        b (int/float): Second number
        c (int/float): Number to add
    
    Returns:
        int/float: Result of a * b + c
    """
    return a * b + c


# Test the function
if __name__ == "__main__":
    result = multiply_then_add(3, 4, 5)
    print(f"Test result for 3, 4, 5: {result}")  # Expected: 17