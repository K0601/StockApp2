#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import streamlit as st
import mplfinance as mpf
import pandas as pd
import sqlite3
from datetime import datetime

from models.train import train_model
from models.walkforward import create_walk_forward_splits
from data.loader import load_price_data

from env.mtf_env import MTFTradingEnv
from fetch_data import main

# =====================
# 初期設定
# =====================
st.set_page_config(layout="wide")

# =====================
# DB関数
# =====================
def get_connection(db_path):
    return sqlite3.connect(db_path, check_same_thread=False)

def load_from_db(db_path, ticker, from_date, to_date, interval):
    conn = get_connection(db_path)
    query = """
        SELECT *
        FROM price_data
        WHERE ticker = ?
          AND interval = ?
          AND datetime BETWEEN ? AND ?
        ORDER BY datetime
    """
    df = pd.read_sql_query(
        query, conn,
        params=(ticker, interval, from_date, to_date)
    )
    conn.close()

    if df.empty:
        return df

    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.set_index("datetime")
    df = df.sort_index()

    numeric_cols = df.columns.drop(["ticker", "interval"])
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")

    return df


def save_training_log(db_path, ticker, interval, rewards):
    conn = get_connection(db_path)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for ep, reward in enumerate(rewards):
        conn.execute(
            "INSERT INTO training_log (ticker, interval, episode, reward, created_at) VALUES (?, ?, ?, ?, ?)",
            (ticker, interval, ep, reward, now)
        )
    conn.commit()
    conn.close()


def save_trade_log(db_path, ticker, trade_history):
    conn = get_connection(db_path)
    for trade in trade_history:
        conn.execute(
            "INSERT INTO trade_log (ticker, datetime, action, price) VALUES (?, ?, ?, ?)",
            (ticker, trade["date"], trade["action"], trade["price"])
        )
    conn.commit()
    conn.close()


# =====================
# Session State
# =====================
for key in ["df", "trade_history", "cash_history", "asset_history"]:
    if key not in st.session_state:
        st.session_state[key] = [] if "history" in key else pd.DataFrame()


# =====================
# UI
# =====================
st.sidebar.header("Yahoo Financeからデータベース更新")
db_path   = st.sidebar.text_input("DBパス", "stock.db")
SQL_btn  = st.sidebar.button("データ収集")

st.sidebar.header("株価データのグラフ化")
ticker    = st.sidebar.text_input("銘柄コード", "7203.T")
from_date = st.sidebar.text_input("開始日", "2026-02-01")
to_date   = st.sidebar.text_input("終了日", "2026-02-06")
interval  = st.sidebar.selectbox("足種", ("1m","5m","15m","1h","1d","1w"))
load_btn  = st.sidebar.button("ローソク足を表示")

st.sidebar.header("学習")
initial_balance = st.sidebar.number_input("初期所持金",1000000)
episodes  = st.sidebar.slider("エピソード数", 50, 1000, 50)
step_size  = st.sidebar.number_input("Step size",1000)
train_btn = st.sidebar.button("🚀 学習開始")


# =====================
# チャート描画
# =====================
def show_chart(df, trade_history=None):
    if df.empty:
        st.warning("データなし")
        return

    apds = []

    # ボリンジャー
    if "bb_upper" in df.columns:
        apds += [
            mpf.make_addplot(df["bb_upper"]),
            mpf.make_addplot(df["bb_lower"])
        ]

    # MACD
    macd_panel = []
    if "macd" in df.columns:
        macd_panel = [
            mpf.make_addplot(df["macd"], panel=1),
            mpf.make_addplot(df["macd_signal"], panel=1)
        ]

    fig, axes = mpf.plot(
        df,
        type="candle",
        volume=True,
        addplot=apds + macd_panel,
        panel_ratios=(3,1),
        style="yahoo",
        returnfig=True
    )

    ax = axes[0]

    if trade_history:
        print(trade_history)
        for trade in trade_history:
            d = pd.to_datetime(trade["date"])
            
            if d in df.index:
                x = df.index.get_loc(d)
                if trade["action"] == "BUY":
                    ax.annotate("▲",(x, df.loc[d,"high"]))
                else:
                    ax.annotate("▼",(x, df.loc[d,"low"]))

    st.pyplot(fig)

# =====================
# Yahoo Financeからデータ取得
# =====================
if SQL_btn:
    main()

# =====================
# DBデータ取得
# =====================
if load_btn:
    df = load_from_db(db_path, ticker, from_date, to_date, interval)

    if df.empty:
        st.error("データなし")
        st.stop()

    st.session_state.df = df
    show_chart(df)

# =====================
# 強化学習
# =====================
if train_btn:

    # ===== データ読み込み =====
    df_1m  = load_price_data(db_path, ticker, "1m")
    df_5m  = load_price_data(db_path, ticker, "5m")
    df_15m = load_price_data(db_path, ticker, "15m")

    common_index = df_1m.index
    df_5m  = df_5m.reindex(common_index, method="ffill")
    df_15m = df_15m.reindex(common_index, method="ffill")

    df_dict_all = {"1m": df_1m, "5m": df_5m, "15m": df_15m}

    splits = create_walk_forward_splits(
        df_1m,
        train_size=800,
        test_size=200,
        step_size=1000
    )

    st.write(f"Total Folds: {len(splits)}")

    fold_results = []

    for fold_idx, (train_idx, test_idx) in enumerate(splits):

        st.write(f"===== Fold {fold_idx+1} =====")

        # ===== データ分割 =====
        train_dict = {k: v.iloc[train_idx] for k, v in df_dict_all.items()}
        test_dict  = {k: v.iloc[test_idx]  for k, v in df_dict_all.items()}

        # ===== Train =====
        train_env = MTFTradingEnv(train_dict)
        input_dim = len(train_env.reset())

        model, rewards = train_model(
            train_env,
            input_dim,
            episodes=episodes
        )

        # ===== Test =====
        test_env = MTFTradingEnv(test_dict)

        state = test_env.reset()
        done = False

        
        balance = initial_balance

        equity_curve = [balance]
        trade_history = []
        prev_position = 0

        while not done:

            action = model.act(state)

            current_index = test_dict["1m"].index[test_env.step_index]
            current_price = test_dict["1m"].iloc[test_env.step_index]["close"]

            state, reward, done = test_env.step(action)

            balance *= (1 + reward)
            equity_curve.append(balance)

            # ===== ポジション変化時のみ記録 =====
            if test_env.position != prev_position:

                if test_env.position == 1:
                    action_type = "BUY"
                elif test_env.position == -1:
                    action_type = "SELL"
                else:
                    action_type = "CLOSE"

                trade_history.append({
                    "date": current_index,
                    "action": action_type,
                    "price": current_price
                })

            prev_position = test_env.position

        # ===== Fold結果表示（ループ外）=====
        final_return = (balance / initial_balance - 1) * 100
        fold_results.append(final_return)

        st.write(f"Final Balance: {balance:,.0f}")
        st.write(f"Return: {final_return:.2f}%")

        # ===== エクイティ曲線 =====
        equity_df = pd.DataFrame({"Equity": equity_curve})
        st.line_chart(equity_df)

        # ===== ローソク足 + 売買タイミング =====
        st.write("### 📈 Trade Chart")
        show_chart(test_dict["1m"], trade_history)

    # ===== 全Foldまとめ =====
    st.success("✅ Walk Forward Complete")

    st.write("### 📊 Fold Results")
    st.write(fold_results)
    st.line_chart(fold_results)
