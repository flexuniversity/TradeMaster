import numpy as np
from typing import List, Any
from sklearn.preprocessing import StandardScaler
import random
import gym

from pm.registry import ENVIRONMENT

@ENVIRONMENT.register_module()
class EnvironmentRET(gym.Env):
    def __init__(self,
                 mode: str = "train",
                 dataset: Any = None,
                 if_norm: bool = True,
                 if_norm_temporal: bool = True,
                 scaler: List[StandardScaler] = None,
                 days: int = 10,
                 start_date: str = None,
                 end_date: str = None,
                 initial_amount: int = 1e3,
                 transaction_cost_pct: float = 1e-3
                 ):
        super(EnvironmentRET, self).__init__()

        self.mode = mode
        self.dataset = dataset
        self.if_norm = if_norm
        self.if_norm_temporal = if_norm_temporal
        self.scaler = scaler
        self.days = days
        self.start_date = start_date
        self.end_date = end_date
        self.initial_amount = initial_amount
        self.transaction_cost_pct = transaction_cost_pct

        if end_date is not None:
            assert end_date > start_date, "start date {}, end date {}, end date should be greater than start date".format(start_date, end_date)

        self.stocks = self.dataset.stocks
        self.stocks2id = self.dataset.stocks2id
        self.id2stocks = self.dataset.id2stocks
        self.aux_stocks = self.dataset.aux_stocks

        self.features_name = self.dataset.features_name
        self.prices_name = ['OPEN', 'HIGH', 'LOW', 'CLOSE']
        self.temporals_name = self.dataset.temporals_name
        self.labels_name = self.dataset.labels_name
        self.stocks_df = []


        if if_norm:
            print("normalize datasets")

            if self.mode == "train":
                self.scaler = []
                for df in self.dataset.stocks_df:

                    if end_date is not None:
                        df = df.loc[start_date:end_date]
                    else:
                        df = df.loc[start_date:]

                    df[self.prices_name] = df[[name.lower() for name in self.prices_name]]
                    price_df = df[self.prices_name]
                    prices.append(price_df.values)

                    scaler = StandardScaler()
                    if self.if_norm_temporal:
                        df[self.features_name + self.temporals_name] = scaler.fit_transform(df[self.features_name + self.temporals_name])
                    else:
                        df[self.features_name] = scaler.fit_transform(df[self.features_name])

                    self.scaler.append(scaler)
                    self.stocks_df.append(df)
            else:
                assert self.scaler is not None, "val mode or test mode is not None."

                for index, df in enumerate(self.dataset.stocks_df):

                    if end_date is not None:
                        df = df.loc[start_date:end_date]
                    else:
                        df = df.loc[start_date:]

                    df[self.prices_name] = df[[name.lower() for name in self.prices_name]]
                    price_df = df[self.prices_name]
                    prices.append(price_df.values)

                    scaler = self.scaler[index]

                    if self.if_norm_temporal:
                        df[self.features_name + self.temporals_name] = scaler.transform(df[self.features_name + self.temporals_name])
                    else:
                        df[self.features_name] = scaler.transform(df[self.features_name])

                    self.stocks_df.append(df)
        else:
            print("no normalize datasets")

        self.features = []
        for df in self.stocks_df:
            df = df[self.features_name + self.temporals_name]
            self.features.append(df.values)
        self.features = np.stack(self.features)

        self.prices = np.stack(prices)

        self.labels = []
        for df in self.stocks_df:
            df = df[self.labels_name]
            self.labels.append(df.values)
        self.labels = np.stack(self.labels)

        print("features shape {}, prices shape {}, labels shape {}, num days {}".format(self.features.shape,
                                                                                        self.prices.shape,
                                                                                        self.labels.shape, self.features.shape[1]))

        self.num_days = self.features.shape[1]

        if self.mode == "train":
            self.day = random.randint(0, 3 * (self.num_days // 4))
        else:
            self.day = 0

    def get_current_date(self):
        return self.stocks_df[0].index[self.day]

    def reset(self):
        if self.mode == "train":
            self.day = random.randint(0, 3 * (self.num_days // 4))
        else:
            self.day = 0

        state = self.features[:, self.day: self.day + self.days, :]

        self.state = state

        return state

    def step(self,
             action: np.array = None):
        state = self.state

        weights = action.flatten()

        labels_ret = self.labels[:, self.day + self.days - 1, 0].flatten()

        portfolio_ret = np.sum(weights[1:] * labels_ret)
        reward = portfolio_ret

        self.day = self.day + 1
        if self.day + self.days < self.num_days:
            done = False
        else:
            done = True

        info = {
            "state":state,
            "action":action,
            "portfolio_ret":portfolio_ret,
        }

        next_state = self.features[:, self.day: self.day + self.days, :]
        self.state = next_state

        return next_state, reward, done, info