def flat_generator(list_of_lists):
    for element in list_of_lists:
        if isinstance(element, list):
            yield from flat_generator(element)
        else:
            yield element


def test_4():
    list_of_lists_2 = [
        [['a'], ['b', 'c']],
        ['d', 'e', [['f'], 'h'], False],
        [1, 2, None, [[[[['!']]]]], []]
    ]

    for flat_iterator_item, check_item in zip(
            flat_generator(list_of_lists_2),
            ['a','b','c','d','e','f','h',
             False,
             1,
             2,
             None,
             '!']
     ):
         assert flat_iterator_item == check_item

     assert list(flat_generator(list_of_lists_2)) == ['a','b','c','d','e','f','h',
                                                       False,
                                                       1,
                                                       2,
                                                       None,
                                                       '!']

     assert isinstance(flat_generator(list_of_lists_2), types.GeneratorType)


if __name__ == '__main__':
     test_4()