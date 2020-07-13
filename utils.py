import os
import numpy as np
import pandas as pd
import argparse
import yaml


def get_args():
    # Store all parameters for easy retrieval
    parser = argparse.ArgumentParser(
        description='nys-cem')
    parser.add_argument('--params_filename',
                        type=str,
                        default='params.yaml',
                        help='Loads model parameters')
    args = parser.parse_args()
    config = yaml.load(open(args.params_filename), Loader=yaml.FullLoader)
    for k, v in config.items():
        args.__dict__[k] = v

    return args


def annualization_rate(i, years):
    return (i*(1+i)**years)/((1+i)**years-1)

def load_timeseries(args):
    wind_file       = pd.read_csv(os.path.join(args.data_dir, 'SEM_TEMOA_wind.csv'), header=1)
    solar_file      = pd.read_csv(os.path.join(args.data_dir, 'SEM_TEMOA_solar.csv'), header=1)
    demand_n1_file  = pd.read_csv(os.path.join(args.data_dir, 'SEM_TEMOA_demand_node1.csv'), header=1)
    demand_n2_file  = pd.read_csv(os.path.join(args.data_dir, 'SEM_TEMOA_demand_node2.csv'), header=1)

    demand_n1_hourly = demand_n1_file['demand']
    demand_n2_hourly = demand_n2_file['demand']
    solar_hourly     = solar_file['solar capacity']
    wind_hourly      = wind_file['wind capacity']

    return wind_hourly, solar_hourly, demand_n1_hourly, demand_n2_hourly

def get_raw_columns():

    # Define columns for raw results export
    columns = ['gt_cap_1', 'gt_cap_2', 'nuc_cap_1', 'nuc_cap_2',
               'solar_cap_1','bat_cap_1_mwh',
               'wind_cap_2',
               'trans_cap_12','trans_cap_21']

    ts_columns = ['demand_1', 'demand_2',
                  'solar_util_1', 'gt_1', 'nuc_1', 'bat_discharge', 'bat_charge', 'bat_level_1',
                  'wind_util_2', 'gt_2', 'nuc_2',
                  'trans_12', 'trans_21']

    return columns, ts_columns


def raw_results_retrieval(args, m):
    T = args.num_hours

    wind_hourly, solar_hourly, demand_n1_hourly, demand_n2_hourly = load_timeseries(args)

    results = np.zeros(9)
    results_ts = np.zeros((T, 13))

    results[0] = np.round(m.getVarByName('gt_cap_1').X)
    results[1] = np.round(m.getVarByName('gt_cap_2').X)
    results[2] = np.round(m.getVarByName('nuc_cap_1').X)
    results[3] = np.round(m.getVarByName('nuc_cap_2').X)
    results[4] = np.round(m.getVarByName('solar_cap_1').X)
    results[5] = np.round(m.getVarByName('bat_cap_1').X)
    results[6] = np.round(m.getVarByName('wind_cap_2').X)
    results[7] = np.round(m.getVarByName('trans_cap_12').X)
    results[8] = np.round(m.getVarByName('trans_cap_21').X)

    results_ts[:, 0] = demand_n1_hourly
    results_ts[:, 1] = demand_n2_hourly

    for j in range(T):
        results_ts[j, 2] = m.getVarByName('solar_util_1[{}]'.format(j)).X
        results_ts[j, 3] = m.getVarByName('gt_util_1[{}]'.format(j)).X
        results_ts[j, 4] = m.getVarByName('nuc_util_1[{}]'.format(j)).X
        results_ts[j, 5] = m.getVarByName('bat_1_discharge[{}]'.format(j)).X
        results_ts[j, 6] = m.getVarByName('bat_1_charge[{}]'.format(j)).X
        results_ts[j, 7] = m.getVarByName('batt_1_level[{}]'.format(j)).X
        results_ts[j, 8] = m.getVarByName('wind_util_2[{}]'.format(j)).X
        results_ts[j, 9] = m.getVarByName('gt_util_2[{}]'.format(j)).X
        results_ts[j, 10] = m.getVarByName('nuc_util_2[{}]'.format(j)).X
        results_ts[j, 11] = m.getVarByName('trans_flow_12[{}]'.format(j)).X
        results_ts[j, 12] = m.getVarByName('trans_flow_21[{}]'.format(j)).X

    return results, results_ts