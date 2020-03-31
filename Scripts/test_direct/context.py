import os
import sys

print(__file__)
print(os.path.join(os.path.dirname(__file__), '..'))

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
print(sys.path)
