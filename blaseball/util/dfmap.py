"""
As part of Stats, we define certain stats which are based on other stats.

To make this easier, we can define those functions such that their arguments are sensible text, like "runs",
and then dataframe_map them to the playerbase so the lookup happens automagically.

Honestly, this whole thing is a little silly - it would probably make more sense to make a function
use defined stats directly, and just call those stat's accessors instead of doing this two-step. merp 🙃
"""

import pandas as pd
from inspect import signature
from functools import partial
from typing import Callable


def dataframe_map(function: Callable, dataframe: pd.DataFrame) -> Callable:
    """Wraps a function such that it takes a single argument (dataframe index) and embeds the relevant columns
    inside the function."""

    function_parameters = signature(function).parameters
    wrapped_arguments = [
        partial(lambda i, df, new_parameter: df.at[i, str(new_parameter).replace("_", " ")], df=dataframe, new_parameter=parameter)
        for parameter in function_parameters
    ]

    def wrapped_function(i, function_to_wrap, arguments):
        return function_to_wrap(*(argument(i) for argument in arguments))

    return partial(wrapped_function, function_to_wrap=function, arguments=wrapped_arguments)
