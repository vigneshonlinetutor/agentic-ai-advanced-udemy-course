"""
Driver for Greeting Generator
"""
from pprint import pprint
from src.graph.greeting_generator.graph import build_graph

def main():
    print(" Greeting Generator Graph\n")

    # Build graph
    app = build_graph()

    # Test 1: Valid name
    print("Test 1: Valid name")
    result = app.invoke({
        "name": "Alice",
        "is_valid": False,
        "greeting": "",
        "timestamp": ""
    })
    pprint(result)
    print()

    # Test 2: Name with spaces
    print("Test 2: Name with spaces")
    result = app.invoke({
        "name": "  Bob  ",
        "is_valid": False,
        "greeting": "",
        "timestamp": ""
    })
    pprint(result)
    print()

    # Test 3: Empty name
    print("Test 3: Empty name (validation fails)")
    result = app.invoke({
        "name": "",
        "is_valid": False,
        "greeting": "",
        "timestamp": ""
    })
    pprint(result)

if __name__ == "__main__":
    main()