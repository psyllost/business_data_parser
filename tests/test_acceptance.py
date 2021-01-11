import ast
import pytest

def test_e2e():
    with open('demo_data.txt', 'r') as reader:
        demo_data = ast.literal_eval(reader.read())

    with open('test_data.txt', 'r') as reader:
        test_data = ast.literal_eval(reader.read())
    assert test_data == demo_data

# print("Data is correct")