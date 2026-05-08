

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import PPoly, interp1d
import logging
import scipy.io


class DataProcessor:

    def __init__(
        self,
        V_dis_raw,
        Q_dis_raw,
        V_sides=[3.0, 4.25],
        V_set_zero=[3.6, 0],
        charge_or_discharge=True,
        smooth=0.999998,
    ):
        self.V_dis_raw = pd.Series(V_dis_raw)
        self.Q_dis_raw = pd.Series(Q_dis_raw)
        self.V_sides = V_sides
        self.V_set_zero = V_set_zero
        self.smooth = smooth
        self.saving = False
        self.charge_or_discharge = (
            charge_or_discharge  
        )

    def arg_sort_usrdef(self):
        if self.charge_or_discharge == False:
            if len(self.V_dis_raw) > 10:
                voltage_threshold = 3.0
                capacity_threshold = 5.0  

                
                
                voltage_indices = self.V_dis_raw[
                    self.V_dis_raw < voltage_threshold
                ].index
                capacity_indices = self.Q_dis_raw[
                    self.Q_dis_raw < capacity_threshold
                ].index

                
                index_to_delete = voltage_indices.intersection(capacity_indices)

                
                self.V_dis_raw = self.V_dis_raw.drop(index_to_delete).reset_index(
                    drop=True
                )
                self.Q_dis_raw = self.Q_dis_raw.drop(index_to_delete).reset_index(
                    drop=True
                )

            
            self.q_largest = self.Q_dis_raw.max()
            self.q_second_largest = self.Q_dis_raw.nlargest(2).iloc[-1]
            self.v_largest = self.V_dis_raw.max()
            self.v_second_largest = self.V_dis_raw.nlargest(2).iloc[-1]
            
            
            Q_threshold = 0.5
            
            if len(self.V_dis_raw) > 10:
                index_below_threshold = self.Q_dis_raw[
                    self.Q_dis_raw < Q_threshold
                ].index
                voltage_zero = self.V_dis_raw[index_below_threshold]
                if len(voltage_zero) < 20:
                    print("Add some points of capacity 0 for better fitting..")
                    additional_series_v = pd.Series(
                        np.linspace(voltage_zero.min(), voltage_zero.max(), 100)
                    )
                    self.V_dis_raw = pd.concat(
                        [self.V_dis_raw, additional_series_v], ignore_index=True
                    )
                    additional_series_q = pd.Series([0] * 100)
                    self.Q_dis_raw = pd.concat(
                        [self.Q_dis_raw, additional_series_q], ignore_index=True
                    )
                    
                    if (
                        self.V_dis_raw[self.V_dis_raw < voltage_zero.min()].max()
                        < voltage_zero.min() - 0.1
                    ):
                        additional_series_v = pd.Series(
                            np.linspace(
                                self.V_dis_raw[
                                    self.V_dis_raw < voltage_zero.min()
                                ].max()
                                + 0.01,
                                voltage_zero.min(),
                                100,
                            )
                        )
                        
                        self.V_dis_raw = pd.concat(
                            [self.V_dis_raw, additional_series_v], ignore_index=True
                        )
                        additional_series_q = pd.Series([0] * 100)
                        self.Q_dis_raw = pd.concat(
                            [self.Q_dis_raw, additional_series_q], ignore_index=True
                        )
            

            
            
            if self.V_dis_raw.max() < self.V_sides[1]:
                
                additional_series_v = pd.Series(
                    np.linspace(self.V_dis_raw.max(), self.V_sides[1], 200)
                )
                self.V_dis_raw = pd.concat(
                    [self.V_dis_raw, additional_series_v], ignore_index=True
                )
                additional_series_q = pd.Series([0] * 200)
                self.Q_dis_raw = pd.concat(
                    [self.Q_dis_raw, additional_series_q], ignore_index=True
                )

            elif self.V_dis_raw.max() > self.V_sides[1]:
                
                
                index_to_delete = self.V_dis_raw[self.V_dis_raw > self.V_sides[1]].index
                
                self.V_dis_raw = self.V_dis_raw.drop(index_to_delete).reset_index(
                    drop=True
                )
                self.Q_dis_raw = self.Q_dis_raw.drop(index_to_delete).reset_index(
                    drop=True
                )
            else:
                pass

            
            
            

            
            
            
            
            
            
            
            
            
            
            
            
            

            if self.V_dis_raw.min() < self.V_sides[0]:
                
                
                index_to_delete = self.V_dis_raw[self.V_dis_raw < self.V_sides[0]].index
                
                self.V_dis_raw = self.V_dis_raw.drop(index_to_delete).reset_index(
                    drop=True
                )
                self.Q_dis_raw = self.Q_dis_raw.drop(index_to_delete).reset_index(
                    drop=True
                )

                print("add points for the begin of discharge curve!")
                additional_series_v = pd.Series(self.V_sides[0])
                self.V_dis_raw = pd.concat(
                    [additional_series_v, self.V_dis_raw], ignore_index=True
                )
                additional_series_q = pd.Series(self.Q_dis_raw.max())
                self.Q_dis_raw = pd.concat(
                    [additional_series_q, self.Q_dis_raw], ignore_index=True
                )

            elif self.V_dis_raw.min() > self.V_sides[0]:
                pass
                
            else:
                pass

            
            if (
                self.V_dis_raw.min() > self.V_sides[0]
                and self.V_dis_raw.min() < self.V_sides[0] + 0.2
            ):
                print("add points for the begin of discharge curve!")
                additional_series_v = pd.Series(self.V_sides[0])
                self.V_dis_raw = pd.concat(
                    [additional_series_v, self.V_dis_raw], ignore_index=True
                )
                additional_series_q = pd.Series(self.Q_dis_raw.max())
                self.Q_dis_raw = pd.concat(
                    [additional_series_q, self.Q_dis_raw], ignore_index=True
                )
            if self.V_dis_raw.min() > self.V_sides[0] + 0.2:
                print("Warning,may get a largely modified curve!!!")
        
        
        
        
        

        
        if self.charge_or_discharge == True:
            self.V_charge_raw = self.V_dis_raw
            self.Q_charge_raw = self.Q_dis_raw

            if len(self.V_charge_raw) > 10:
                voltage_threshold = 3.7  
                capacity_threshold = 5.0  

                
                voltage_indices = self.V_charge_raw[
                    self.V_charge_raw > voltage_threshold
                ].index
                capacity_indices = self.Q_charge_raw[
                    self.Q_charge_raw < capacity_threshold
                ].index

                
                index_to_delete = voltage_indices.intersection(capacity_indices)

                
                self.V_charge_raw = self.V_charge_raw.drop(index_to_delete).reset_index(
                    drop=True
                )
                self.Q_charge_raw = self.Q_charge_raw.drop(index_to_delete).reset_index(
                    drop=True
                )

            self.q_largest = self.Q_charge_raw.max()
            self.q_second_largest = self.Q_charge_raw.nlargest(2).iloc[-1]
            self.v_largest = self.V_charge_raw.max()
            self.v_second_largest = self.V_charge_raw.nlargest(2).iloc[-1]

            
            
            if len(self.V_charge_raw) > 10:
                Q_threshold = 0.5  
                index_below_threshold = self.Q_charge_raw[
                    self.Q_charge_raw < Q_threshold
                ].index
                
                
                voltage_zero = self.V_charge_raw[index_below_threshold]
                if len(voltage_zero) < 20:
                    
                    
                    
                    additional_series_v = pd.Series(
                        np.linspace(voltage_zero.min(), voltage_zero.max(), 100)
                    )
                    self.V_charge_raw = pd.concat(
                        [self.V_charge_raw, additional_series_v], ignore_index=True
                    )

                    additional_series_q = pd.Series([0] * 100)
                    self.Q_charge_raw = pd.concat(
                        [self.Q_charge_raw, additional_series_q], ignore_index=True
                    )

                    
                    if (
                        self.V_charge_raw[self.V_charge_raw > voltage_zero.max()].min()
                        > voltage_zero.max() + 0.1
                    ):
                        
                        additional_series_v = pd.Series(
                            np.linspace(
                                self.V_charge_raw[self.V_charge_raw > voltage_zero.max()].min()
                                - 0.01,
                                voltage_zero.max(),
                                100,
                            )
                        )
                        
                        self.V_charge_raw = pd.concat(
                            [self.V_charge_raw, additional_series_v], ignore_index=True
                        )
                        additional_series_q = pd.Series([0] * 100)
                        self.Q_charge_raw = pd.concat(
                            [self.Q_charge_raw, additional_series_q], ignore_index=True
                        )

            if self.V_charge_raw.min() > self.V_sides[0]:
                
                additional_series_v = pd.Series(
                    np.linspace(self.V_sides[0], self.V_charge_raw.min(), 200)
                )
                self.V_charge_raw = pd.concat(
                    [additional_series_v, self.V_charge_raw], ignore_index=True
                )

                additional_series_q = pd.Series([0] * 200)
                self.Q_charge_raw = pd.concat(
                    [additional_series_q, self.Q_charge_raw], ignore_index=True
                )

            elif self.V_charge_raw.max() < self.V_sides[0]:
                
                
                index_to_delete = self.V_charge_raw[
                    self.V_charge_raw < self.V_sides[0]
                ].index
                
                self.V_charge_raw = self.V_charge_raw.drop(index_to_delete).reset_index(
                    drop=True
                )
                self.Q_charge_raw = self.Q_charge_raw.drop(index_to_delete).reset_index(
                    drop=True
                )
            else:
                pass

            
            
            
            
            

            
            

            if self.V_charge_raw.max() > self.V_sides[1]:
                
                index_to_delete = self.V_charge_raw[
                    self.V_charge_raw > self.V_sides[1]
                ].index
                self.V_charge_raw = self.V_charge_raw.drop(index_to_delete).reset_index(
                    drop=True
                )
                self.Q_charge_raw = self.Q_charge_raw.drop(index_to_delete).reset_index(
                    drop=True
                )

                
                additional_series_v = pd.Series(self.V_sides[1])
                self.V_charge_raw = pd.concat(
                    [additional_series_v, self.V_charge_raw], ignore_index=True
                )
                additional_series_q = pd.Series(self.Q_charge_raw.max())
                self.Q_charge_raw = pd.concat(
                    [additional_series_q, self.Q_charge_raw], ignore_index=True
                )
            elif self.V_charge_raw.max() < self.V_sides[1]:
                pass
                
            else:
                pass
            if (
                self.V_charge_raw.max() < self.V_sides[1]
                and self.V_charge_raw.max() > self.V_sides[1] - 0.2
            ):
                
                additional_series_v = pd.Series(self.V_sides[1])
                self.V_charge_raw = pd.concat(
                    [additional_series_v, self.V_charge_raw], ignore_index=True
                )
                additional_series_q = pd.Series(self.Q_charge_raw.max())
                self.Q_charge_raw = pd.concat(
                    [additional_series_q, self.Q_charge_raw], ignore_index=True
                )
            if self.Q_charge_raw.max() < self.V_sides[1] - 0.2:
                print("Warning,may get a largely modified curve!!!")

            if self.V_charge_raw.max() < self.V_sides[1] - 0.2:
                print("Warning, may get a largely modified curve!!!")
            pass

        if self.charge_or_discharge == False:
            
            aux_array = [(value, idx) for idx, value in enumerate(self.V_dis_raw)]
            
            
            aux_sorted = sorted(aux_array, key=lambda x: (x[0], x[1]))

            unique_sorted = []
            last_val = None
            for val, idx in aux_sorted:
                if val != last_val:
                    unique_sorted.append((val, idx))
                    last_val = val
            
            unique_indices = [index for _, index in unique_sorted]
            logging.info(f"unique_indices: {unique_indices}")
            
            self.V_dis_raw = self.V_dis_raw.iloc[unique_indices].tolist()
            self.Q_dis_raw = self.Q_dis_raw.iloc[unique_indices].tolist()
        else:
            
            aux_array = [(value, idx) for idx, value in enumerate(self.V_charge_raw)]
            
            
            aux_sorted = sorted(aux_array, key=lambda x: (x[0], x[1]))

            unique_sorted = []
            last_val = None
            for val, idx in aux_sorted:
                if val != last_val:
                    unique_sorted.append((val, idx))
                    last_val = val
            
            unique_indices = [index for _, index in unique_sorted]
            logging.info(f"unique_indices: {unique_indices}")
            
            self.V_charge_raw = self.V_charge_raw.iloc[unique_indices].tolist()
            self.Q_charge_raw = self.Q_charge_raw.iloc[unique_indices].tolist()

    def get_derivative(self, sp):
        pp_form = sp.spline
        coeffs = pp_form.c.reshape((4, -1), order="F")
        breakpoints = pp_form.x
        pp = PPoly.construct_fast(coeffs, breakpoints, extrapolate=None)
        pp_derivative = pp.derivative()
        xs = np.linspace(self.V_sides[0], self.V_sides[1], 1000)
        y_derivative = pp_derivative(xs)
        
        return y_derivative

    @staticmethod
    def check_descending(V_dis_raw):
        for i in range(1, len(V_dis_raw)):
            if V_dis_raw[i - 1] > V_dis_raw[i]:
                print(f"第一次出现前一个数大于等于后一个数的现象的索引是: {i}")
                return

    def get_Qdlin_usrdef(self):
        self.arg_sort_usrdef()
        if self.charge_or_discharge == False:
            self.check_descending(self.V_dis_raw)
        else:
            self.check_descending(self.V_charge_raw)

        if self.charge_or_discharge == False:
            plt.scatter(self.V_dis_raw, self.Q_dis_raw, s=5, color="blue")
        else:
            plt.scatter(self.V_charge_raw, self.Q_charge_raw, s=5, color="blue")
        
        if self.saving:
            data = {"x": self.V_dis_raw, "y": self.Q_dis_raw}
            scipy.io.savemat("data.mat", data)
        
        
        xs = np.linspace(self.V_sides[0], self.V_sides[1], 1000)
        if self.charge_or_discharge == False:
            try:
                sp = interp1d(self.V_dis_raw, self.Q_dis_raw, kind='linear', fill_value='extrapolate')
            except:
                print("fail in generating interpolation!")
                return xs, xs
        else:
            try:
                sp = interp1d(self.V_charge_raw, self.Q_charge_raw, kind='linear', fill_value='extrapolate')
            except:
                print("fail in generating interpolation!")
                return xs, xs
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        

        
        y_sample = sp(xs)
        dy_values = np.gradient(y_sample, xs)  

        
        d2y_values = np.gradient(dy_values, xs)  


        
        
        threshold = min(d2y_values) + 1000
        window_length = 0.15
        exceeding_regions = []

        
        count_derivative_exceed = 0
        window_length_idx = int(1000 * 0.15)
        
        for i in range(0, len(d2y_values) - window_length_idx, window_length_idx):
            window = d2y_values[i : i + window_length_idx]
            if np.any(window > 1000):
                exceeding_regions.append((xs[i], xs[i + window_length_idx]))
                count_derivative_exceed += 1
        
        

        
        
        if (
            np.any(d2y_values > 10000) and np.any(d2y_values < -10000)
        ) or count_derivative_exceed >= 2:
            
            print("smooth penalty used!")
            if self.charge_or_discharge == False:
                sp = interp1d(self.V_dis_raw, self.Q_dis_raw, kind='cubic', fill_value='extrapolate')
            else:
                sp = interp1d(self.V_charge_raw, self.Q_charge_raw, kind='cubic', fill_value='extrapolate')

        
        xs = np.linspace(self.V_sides[0], self.V_sides[1], 1000)
        ys = sp(xs)

        
        if self.V_set_zero[1] == 0:
            index_to_set_zero = np.where(xs < self.V_set_zero[0])[0]
        
        elif self.V_set_zero[1] == 1:
            index_to_set_zero = np.where(xs > self.V_set_zero[0])[0]

        ys[index_to_set_zero] = 0

        index_to_set_zero = np.where(ys < 0)[0]
        
        ys[index_to_set_zero] = 0
        return xs, ys



"""
V_dis_raw = np.array([3, 3.5, 3.6, 4.2, 3.8, 4.5, 3.45, 4.25, 3.8])
Q_dis_raw = np.array([30, 50, 55, 20, 80, 50, 55, 20, 80])
processor = DataProcessor(
    V_dis_raw, Q_dis_raw, [3.0, 4.25], [3.6, 0], charge_or_discharge=False
)
xs, ys = processor.get_Qdlin_usrdef()
plt.plot(xs, ys)
plt.show()
"""

from scipy.stats import skew, kurtosis


def calc_list_properties(Qd_diff):
    return {
        "Var": np.var(Qd_diff, ddof=0),
        "Ske": skew(Qd_diff),
        "Kur": kurtosis(Qd_diff),
        "Min": np.min(Qd_diff),
    }
