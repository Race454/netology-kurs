import pytest
def test_solve_pairs():
    assert solve(['Миша', 'Саша'], ['Катя', 'Оля']) == "Миша и Катя, Саша и Оля"
    assert solve(['Миша'], ['Катя']) == "Миша и Катя"
    assert solve(['Миша', 'Саша'], ['Катя']) == "Кто-то может остаться без пары!"
    assert solve([], []) == ""

def test_solve_palindromes():
    assert solve(['А роза упала на лапу Азора', 'Привет', 'Кот', 'Лёша на полке клопа нашёл']) == [
        'А роза упала на лапу Азора',
        'Кот',
        'Лёша на полке клопа нашёл'
    ]
    assert solve(['Тест', 'Радар', '12321']) == ['Радар', '12321']
    assert solve(['Не палиндром', 'Еще один']) == []

def test_solve_shopping_list():
    cook_book = [
        ('Борщ', [('Картошка', 3, 'шт'), ('Свекла', 2, 'шт')]),
        ('Салат', [('Помидор', 2, 'шт'), ('Огурец', 1, 'шт')])
    ]
    
    expected_result_for_one = [
        "Борщ: Картошка 3 шт, Свекла 2 шт",
        "Салат: Помидор 2 шт, Огурец 1 шт"
    ]
    
    expected_result_for_two = [
        "Борщ: Картошка 6 шт, Свекла 4 шт",
        "Салат: Помидор 4 шт, Огурец 2 шт"
    ]
    
    assert solve(cook_book, 1) == expected_result_for_one
    assert solve(cook_book, 2) == expected_result_for_two

if __name__ == "__main__":
    pytest.main()