#Задание 1.
class Stack:
    def __init__(self):
        self.items = []

    def is_empty(self):
        return len(self.items) == 0

    def push(self, item):
        self.items.append(item)

    def pop(self):
        if not self.is_empty():
            return self.items.pop()
        return None

    def peek(self):
        if not self.is_empty():
            return self.items[-1]
        return None  
# Мы можем так же использовать исключение, но я выбрал через None.

    def size(self):
        return len(self.items)

#Задание 2.
def balance(expression):
    stack = Stack()
    opening = "([{"
    closing = ")]}"
    matches = {')': '(', ']': '[', '}': '{'}

    for char in expression:
        if char in opening:
            stack.push(char)
        elif char in closing:
            if stack.is_empty() or stack.pop() != matches[char]:
                return "Несбалансированно"

    return "Сбалансированно" if stack.is_empty() else "Несбалансированно"


input_expression = input("Введите строку со скобками: ")
print(balance(input_expression))
