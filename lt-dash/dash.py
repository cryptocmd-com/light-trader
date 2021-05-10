import pandas as pandas
import streamlit as st
import requests
from utils import read_config
from lt_comm import get_last_candle_info, get_strategy_info, get_general_positions_info, get_server_status, get_candle_history, get_all_coin_list
import altair as alt
import plotly.graph_objects as go


def main(key):
    ## Pre-load ##
    strategies = get_general_positions_info(key)

    ## Sidebar ##
    st.sidebar.image(image='images/sidebar.logo.png')
    st.sidebar.text('Server status: {}.'.format(get_server_status(key)))
    positions_flag = st.sidebar.checkbox(label='General Strategies Info', value=True)
    strategie_flag = st.sidebar.checkbox(label='Detail Strategy Information', value=True)
    candle_chart_flag = st.sidebar.checkbox(label='Candle Chart', value=True)
    st.sidebar.image(image='images/ccmd.logo.png', width=250)

    if strategies.empty:
        ## Main ##
        st.title(body="Light Trader Dashboard")        

        if positions_flag:
            st.subheader('Strategies list:')
            st.text(body='Light Trader has no active strategies right now.')

        if strategie_flag:
            st.subheader('Strategy details:')
            st.text(body='Light Trader has no active strategies right now.')

        if candle_chart_flag:
            coin_list = get_all_coin_list()
            coin_symbol = st.selectbox(label='Select symbol for information:', options=coin_list)

            df = get_candle_history(coin_symbol)

            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']))
            st.plotly_chart(fig)

            st.dataframe(df)      

    else:
        ## Main ##
        st.title(body="Light Trader Dashboard")        

        if positions_flag:
            st.subheader('Strategies list:')
            st.dataframe(data=strategies)

        if strategie_flag:
            st.subheader('Strategy details:')
            strategie = st.selectbox(label='Select Strategy ID:', options=strategies['strategy_id'])
            s_info = get_strategy_info(key, strategie)
            candle_info = get_last_candle_info(s_info['symbol'].iloc[0])
            st.dataframe(s_info)
            st.dataframe(candle_info)

        if candle_chart_flag:
            df = get_candle_history(s_info['symbol'].iloc[0])

            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']))
            st.plotly_chart(fig)

            st.dataframe(df)




if __name__ == '__main__':
    config  = read_config()
    user_password = list((config.get('user_passwords', {})).items())[0]

    main(user_password)



