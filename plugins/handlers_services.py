from pyrogram import filters

"""
Handle multiple callback queries data and return filter for each
"""


def dynamic_data_filter(data):
    return filters.create(
        lambda flt, _, query: query.data.startswith(flt.data), data=data
        # "data" kwarg is accessed with "flt.data" above
    )
