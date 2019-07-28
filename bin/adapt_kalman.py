# Copyright (c) 2019 Daniel Hammer. All Rights Reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

from kalman import Kalman

class AdaptKalman(Kalman):
    w_k_last = []
    peak = 0
    window_list = ["sig", "exp"]

    # plotting
    plot_r = []

    def __init__(self,ratio=1/3.,window="sig", window_size=5, adapt=True):
        Kalman.__init__(self, ratio)
        self.window = window
        self.window_size = window_size
        self.adapt = adapt

    def filter_step(self, u=None,t=None):
        if u and t:
            if self.adapt:
                self.adapt_covar()
            self.filter_iter(u,t)

    def adapt_covar(self):
        N = self.window_size
        if len(self.plot_u) == N:
            self.w_k_last = self.get_window_avg(N)

        elif len(self.plot_u) >= 2*N:
            w_k = self.get_window_avg(N)
            w_k_last = self.w_k_last

            delta_w_k = abs(w_k - w_k_last)

            c_k = delta_w_k / self.peak * (np.reciprocal(self.r_k) - 1) + 1

            # before first peak detection
            if self.get_peak(delta_w_k) == 0:
                c_k = 1

            # update covariances
            u0_stdev,u1_stdev = self.decomp_fraction(self.r_k * c_k)
            self.Q_k[1][1] = u0_stdev*u0_stdev
            self.R_k[1][1] = u1_stdev*u1_stdev

            # update for next iteration
            self.w_k_last = w_k

            # append for plotting
            self.plot_r.append(self.r_k * c_k)

    def get_window_avg(self, N):
        array = []
        avg = 0
        for i in range(0,N):
            array.append(self.plot_u[-i-1])

        if self.window == "exp":
            avg = self.exp_avg(array)
        elif self.window == "sig":
            avg = self.sig_avg(array)

        return avg

    def get_peak(self, value):
        if value > self.peak:
                self.peak = value
        return self.peak

    def sig_avg(self,array):
        n = len(array)
        newarray = np.zeros(n)
        alpha = 5
        x = np.linspace(-1,1,n)
        w = np.zeros(n)

        # initilise weights
        for i in range(n):
            w[i] = 1 / (1 + np.exp(alpha * x[i]))

        for j in range(n):
            newarray[j] = array[j]*w[j] / np.sum(w)

        return np.sum(newarray)

    def exp_avg(self,array):
        series = pd.Series(array)
        avg = np.average(series.ewm(span=len(array)).mean().values)
        return avg

    def plot_all(self):
        plt.figure(1)

        plt.subplot(511)
        plt.title("Simulated robot velocity")
        plt.xlabel("Time in s")
        plt.ylabel("Velocity in m/s")
        plt.plot(self.t,self.vel)

        plt.subplot(512)
        plt.title("Robot distance")
        plt.xlabel("Time in s")
        plt.ylabel("Distance in m")
        plt.plot(self.plot_t,self.plot_y)

        plt.subplot(513)
        plt.title("Robot velocity post")
        plt.xlabel("Time in s")
        plt.ylabel("Velocity in m/s")
        plt.plot(self.plot_t,self.plot_v)

        plt.subplot(514)
        plt.title("Robot acceleration")
        plt.xlabel("Time in s")
        plt.ylabel("Acceleration in m/s^2")
        plt.plot(self.plot_t, self.plot_a)

        plt.subplot(515)
        plt.title("Ratio")
        fill = len(self.plot_t) - len(self.plot_r)
        full_ratio_array = np.insert(self.plot_r, 0, np.full((fill),self.r_k))
        plt.plot(self.plot_t,full_ratio_array)

        plt.show()
