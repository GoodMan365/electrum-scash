import ast
import sys

with open('blockchain.py', 'r') as f:
    content = f.read()
    
tree = ast.parse(content)

# Find the Blockchain class
for node in ast.walk(tree):
    if isinstance(node, ast.ClassDef) and node.name == 'Blockchain':
        print(f"Found Blockchain class")
        # Look for __init__ method
        for item in node.body:
            if isinstance(item, ast.FunctionDef) and item.name == '__init__':
                print(f"\nFound __init__ method:")
                # Print the source
                import inspect
                print(ast.unparse(item))
                break
        break
