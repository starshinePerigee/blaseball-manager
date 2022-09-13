import pandas as pd
import inspect
import timeit
import functools
import copy

from typing import Callable

df = pd.DataFrame(
    data={
        'col1': [1, 2, 3, 4, 5],
        'col2': [6, 7, 8, 9, 10],
        'cola': ['a', 'b', 'c', 'd', 'e'],
        'col3': [0.1, 0.2, 0.3, 0.4, 0.5],
    },
    index=[10, 11, 12, 13, 14]
)


def f1(col1, col3):
    return col1 + col3


print(f"raw call: {timeit.timeit(lambda: f1(2, 0.2), number=10000):.5f}")


# wrapped f1 should be:
def f1_goal(i):
    return df.at[i, 'col1'] + df.at[i, 'col3']


print(f"goal call: {timeit.timeit(lambda: f1_goal(11), number=10000):.5f}")


def f1_manual(i):
    return f1(df.at[i, 'col1'], df.at[i, 'col3'])


print(f"manual: {timeit.timeit(lambda: f1_manual(11), number=10000):.5f}")


def df_wrap_basic(f: Callable) -> Callable:
    # this works, but it has two issues:
    # it inspects *every time* which is slow
    # it drops any info from the function (ref functools wrapped)
    def wrapped_fn(i):
        new_args = []
        for p in inspect.signature(f).parameters:
            new_arg = df.at[i, p]
            new_args += [new_arg]
        return f(*new_args)
    return wrapped_fn


f1_wrapped = df_wrap_basic(f1)
print(f"wrapped basic: {timeit.timeit(lambda: f1_wrapped(11), number=10000):.5f}")


def df_wrap_partial(f: Callable) -> Callable:
    new_args = []
    for p in inspect.signature(f).parameters:
        nf = lambda i, np: df.at[i, np]
        new_arg = functools.partial(nf, np=p)
        new_args += [new_arg]

    def wrapped_fn(i, wf: Callable, largs):
        fn_args = (arg(i) for arg in largs)
        return wf(*fn_args)

    partial_wrapped = functools.partial(wrapped_fn, wf=f, largs=new_args)
    return partial_wrapped


f1_wrapped_partial = df_wrap_partial(f1)
print(f"wrapped partial: {timeit.timeit(lambda: f1_wrapped_partial(11), number=10000):.5f}")


def df_wrap_cleaner(f: Callable) -> Callable:
    new_args = [functools.partial(lambda i, np: df.at[i, np], np=p) for p in inspect.signature(f).parameters]

    def wrapped_fn(i, wf: Callable, largs):
        return wf(*(arg(i) for arg in largs))

    return functools.partial(wrapped_fn, wf=f, largs=new_args)


f1_wrapped_partial_2 = df_wrap_cleaner(f1)
print(f"wrapped partial: {timeit.timeit(lambda: f1_wrapped_partial_2(11), number=10000):.5f}")