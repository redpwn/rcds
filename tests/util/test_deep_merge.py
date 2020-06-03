from rcds.util.deep_merge import deep_merge


def test_basic_merge():
    a = {1: {1: 1, 2: 2}}
    b = {1: {1: 2, 3: 3}}
    expected = {1: {1: 2, 2: 2, 3: 3}}
    assert deep_merge(a, b) == expected
    assert a == expected
    assert b == {1: {1: 2, 3: 3}}


def test_override_dict_with_other_type():
    a = {1: {1: 1}}
    b = {1: 2}
    expected = {1: 2}
    assert deep_merge(a, b) == expected
    assert a == expected
    assert b == {1: 2}


def test_override_other_type_with_dict():
    a = {1: 2}
    b = {1: {1: 1}}
    expected = {1: {1: 1}}
    assert deep_merge(a, b) == expected
    assert a == expected
    assert b == {1: {1: 1}}


def test_merge_multiple():
    a = {1: {1: 1}}
    b = {1: {1: 2, 2: 2}}
    c = {1: {1: 3, 3: 3}}
    expected = {1: {1: 3, 2: 2, 3: 3}}
    assert deep_merge(a, b, c) == expected
    assert a == expected
    assert b == {1: {1: 2, 2: 2}}
    assert c == {1: {1: 3, 3: 3}}


def test_nonmutating_merge():
    a = {1: {1: 1}}
    b = {1: {1: 2, 2: {3: 3}}}
    c = {1: {1: 3, 2: {3: 4}}}
    expected = {1: {1: 3, 2: {3: 4}}}
    assert deep_merge(dict(), a, b, c) == expected
    assert a == {1: {1: 1}}
    assert b == {1: {1: 2, 2: {3: 3}}}
    assert c == {1: {1: 3, 2: {3: 4}}}
