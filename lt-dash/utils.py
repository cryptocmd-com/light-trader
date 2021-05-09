import os
import toml
import altair as alt
import pandas as pd


def read_config():
    config_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), 'config.toml')
    return toml.load(config_path)


# from typing import Tuple    

# def build_candle_chart(df: pd.DataFrame) -> Tuple[alt.Chart, alt.Chart, alt.Chart]:
#     open_close_color = alt.condition("datum.Open < datum.Close", alt.value("#03652d"), alt.value("#ae1325"))

#     base = alt.Chart(df).encode(x='Date')

#     rule = base.mark_rule().encode(
#         y=alt.Y(
#             'Low',
#             scale=alt.Scale(zero=False),
#             axis=alt.Axis(title='Price')
#         ),
#         y2=alt.Y2('High'),
#         color=open_close_color
#     )

#     bar = base.mark_bar().encode(
#         y='Open',
#         y2='Close',
#         color=open_close_color
#     )

#     volume: alt.Chart = base.properties(hight=100).mark_bar().encode(
#         y=alt.Y(
#             'Volume',
#             scale=alt.Scale(zero=False)
#         )
#     )

#     return rule, bar, volume