class FlatIterator:

    def __init__(self, list_of_list):
        self.list_of_list = list_of_list
        self.flat_list = []
        self.index = 0
        self._flatten(self.list_of_list)

    def _flatten(self, lst):
        for item in lst:
            if isinstance(item, list):
                self._flatten(item)
            else:
                self.flat_list.append(item)

    def __iter__(self):
        return self

    def __next__(self):
        if self.index < len(self.flat_list):
            item = self.flat_list[self.index]
            self.index += 1
            return item
        else:
            raise StopIteration


def test_3():
    list_of_lists_2 = [
        [['a'], ['b', 'c']],
        ['d', 'e', [['f'], 'h'], False],
        [1, 2, None, [[[[['!']]]]], []]
    ]

    for flat_iterator_item, check_item in zip(
            FlatIterator(list_of_lists_2),
            ['a', 'b', 'c', 'd', 'e', 'f', 'h', False, 1, 2, None, '!']
    ):
        assert flat_iterator_item == check_item

    assert list(FlatIterator(list_of_lists_2)) == ['a', 'b', 'c',
                                                     'd',
                                                     'e',
                                                     'f',
                                                     'h',
                                                     False,
                                                     1,
                                                     2,
                                                     None,
                                                     '!']

if __name__ == '__main__':
    test_3()