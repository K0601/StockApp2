import numpy as np
import pandas as pd


class MTFTradingEnv:

    def __init__(self, df_dict, initial_cash=1_000_000, window=60):

        """
        df_dict = {
            "1m": df_1m,
            "5m": df_5m,
            "15m": df_15m
        }
        """

        self.window = window
        self.initial_cash = initial_cash

        # 足ごとに正規化特徴生成
        self.df_1m  = self._prepare_features(df_dict["1m"])
        self.df_5m  = self._prepare_features(df_dict["5m"])
        self.df_15m = self._prepare_features(df_dict["15m"])

        # datetime index化
        for df in [self.df_1m, self.df_5m, self.df_15m]:
            df["datetime"] = pd.to_datetime(df["datetime"])
            df.set_index("datetime", inplace=True)

        # 1分足基準同期
        self.df_5m_sync  = self.df_5m.reindex(self.df_1m.index, method="ffill")
        self.df_15m_sync = self.df_15m.reindex(self.df_1m.index, method="ffill")

        self.reset()

    # =====================================================
    # 🔥 完全無次元化特徴量生成
    # =====================================================

    def _prepare_features(self, df):

        df = df.copy()

        # ===== 価格系 =====
        df["log_return"] = np.log(df["close"] / df["close"].shift(1))

        # ===== ボラ =====
        df["tr"] = df["high"] - df["low"]
        df["atr"] = df["tr"].rolling(14).mean()

        df["norm_return"] = df["log_return"] / (df["atr"] + 1e-8)

        # ===== Volume Z =====
        df["vol_z"] = (
            df["volume"] - df["volume"].rolling(60).mean()
        ) / (df["volume"].rolling(60).std() + 1e-8)

        # ===== RSI =====
        delta = df["close"].diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = -delta.clip(upper=0).rolling(14).mean()
        rs = gain / (loss + 1e-8)
        df["rsi"] = 100 - (100 / (1 + rs))
        df["rsi"] = df["rsi"] / 100.0

        # ===== MACD Z正規化 =====
        ema12 = df["close"].ewm(span=12).mean()
        ema26 = df["close"].ewm(span=26).mean()
        macd = ema12 - ema26
        df["macd_z"] = (
            macd - macd.rolling(100).mean()
        ) / (macd.rolling(100).std() + 1e-8)

        # ===== BB位置 =====
        mid = df["close"].rolling(20).mean()
        std = df["close"].rolling(20).std()
        df["bb_pos"] = (
            df["close"] - mid
        ) / (std + 1e-8)

        df = df.dropna().reset_index()

        return df[[
            "datetime",
            "norm_return",
            "vol_z",
            "rsi",
            "macd_z",
            "bb_pos"
        ]]

    # =====================================================
    # リセット
    # =====================================================

    def reset(self):

        self.step_index = self.window
        self.cash = self.initial_cash
        self.position = 0
        self.entry_price = 0

        return self._get_state()

    # =====================================================
    # 状態生成（MTF融合）
    # =====================================================

    def _get_state(self):

        w = self.window

        win_1m  = self.df_1m.iloc[self.step_index-w:self.step_index]
        win_5m  = self.df_5m_sync.iloc[self.step_index-w:self.step_index]
        win_15m = self.df_15m_sync.iloc[self.step_index-w:self.step_index]

        state = np.concatenate([
            win_1m.values.flatten(),
            win_5m.values.flatten(),
            win_15m.values.flatten(),
            [self.position]
        ])

        return state.astype(np.float32)

    # =====================================================
    # ステップ
    # =====================================================

    def step(self, action):

        # ===== 1. まずポジション更新 =====
        if action == 0: #Short
            self.position = -1
        elif action == 2: #Long
            self.position = 1
        else:#Flat
            self.position = 0

        # ===== 2. 次のバーのリターンで報酬計算 =====
        next_return = self.df_1m.iloc[self.step_index]["norm_return"]

        reward = next_return * self.position

        # ===== 3. 進める =====
        self.step_index += 1

        done = self.step_index >= len(self.df_1m) - 1

        return self._get_state(), reward, done

