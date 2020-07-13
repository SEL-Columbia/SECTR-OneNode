import numpy as np
from gurobipy import *
from utils import annualization_rate, load_timeseries
import pandas as pd

def create_model(args):
    # Set up model parameters
    m = Model("capacity_optimization_renewable_targets")
    T = args.num_hours
    trange = range(T)

    # Load in time-series data
    wind_hourly, solar_hourly, demand_n1_hourly, demand_n2_hourly = load_timeseries(args)

    ### NEW GENERATION COST ###
    solar_cap_cost = annualization_rate(args.i_rate, args.n_year_solar) * float(args.solar_cost_mw)
    solar_fom_cost = float(args.solar_cost_om_mw_yr)

    wind_cap_cost  = annualization_rate(args.i_rate, args.n_year_wind) * float(args.wind_cost_mw)
    wind_fom_cost = float(args.wind_cost_om_mw_yr)

    gt_cap_cost = annualization_rate(args.i_rate, args.n_year_gt) * float(args.gt_cost_mw)
    gt_fom_cost = float(args.gt_cost_om_mw_yr)
    gt_op_cost = float(args.gt_cost_om_mwh) + float(args.gt_cost_fuel_mwh / args.gt_effi)

    nuc_cap_cost = annualization_rate(args.i_rate, args.n_year_nuc) * float(args.nuc_cost_mw)
    nuc_fom_cost = float(args.nuc_cost_om_mw_yr)
    nuc_op_cost = float(args.nuc_cost_om_mwh) + float(args.nuc_cost_fuel_mwh / args.nuc_effi)

    bat_cap_cost = annualization_rate(args.i_rate, args.n_year_bat) * float(args.bat_cost_mwh)

    trans_cap_mw_cost = annualization_rate(args.i_rate, args.n_year_trans) * float(args.trans_cost_mw)

    ### Generation & Battery & Transmission Variables ###
    solar_cap_1 = m.addVar(obj=solar_cap_cost + solar_fom_cost, name='solar_cap_1')
    wind_cap_2  = m.addVar(obj=wind_cap_cost + wind_fom_cost, name='wind_cap_2')
    gt_cap_1    = m.addVar(obj=gt_cap_cost + gt_fom_cost, name='gt_cap_1')
    gt_cap_2    = m.addVar(obj=gt_cap_cost + gt_fom_cost, name='gt_cap_2')
    nuc_cap_1   = m.addVar(obj=nuc_cap_cost + nuc_fom_cost, name='nuc_cap_1')
    nuc_cap_2   = m.addVar(obj=nuc_cap_cost + nuc_fom_cost, name='nuc_cap_2')
    bat_cap_1   = m.addVar(obj=bat_cap_cost, name='bat_cap_1')
    trans_cap_12 = m.addVar(obj=trans_cap_mw_cost/2, name='trans_cap_12')
    trans_cap_21 = m.addVar(obj=trans_cap_mw_cost/2, name='trans_cap_21')
    m.addConstr(trans_cap_12 + trans_cap_21 == 0)

    ### Utilization Variables ###
    solar_util_1  = m.addVars(trange, obj=0, name='solar_util_1')
    wind_util_2   = m.addVars(trange, obj=0, name='wind_util_2')
    gt_util_1     = m.addVars(trange, obj=gt_op_cost, name='gt_util_1')
    gt_util_2     = m.addVars(trange, obj=gt_op_cost, name='gt_util_2')
    nuc_util_1    = m.addVars(trange, obj=nuc_op_cost, name='nuc_util_1')
    nuc_util_2    = m.addVars(trange, obj=nuc_op_cost, name='nuc_util_2')
    bat_1_level   = m.addVars(trange, name='batt_1_level')
    bat_1_charge  = m.addVars(trange, obj=0, name='bat_1_charge')
    bat_1_discharge  = m.addVars(trange, obj=0, name='bat_1_discharge')
    trans_flow_12 = m.addVars(trange, obj=0, name='trans_flow_12')
    trans_flow_21 = m.addVars(trange, obj=0, name='trans_flow_21')

    ### other assumption set ###
    bat_effi = math.sqrt(float(args.bat_effi))

    m.update()

    for j in trange:
        # transmission limit
        m.addConstr(trans_flow_12[j] <= trans_cap_12)
        m.addConstr(trans_flow_21[j] <= trans_cap_21)

        #####  -------------- Node 1 constraints --------------  #####
        m.addConstr(solar_util_1[j] - (solar_cap_1 * solar_hourly[j]) <= 0)
        m.addConstr(gt_util_1[j] - gt_cap_1 <= 0)
        m.addConstr(nuc_util_1[j] - nuc_cap_1 <= 0)

        m.addConstr(solar_util_1[j] + gt_util_1[j] + nuc_util_1[j] - bat_1_charge[j] + bat_1_discharge[j] +
                    trans_flow_21[j] * (1 - args.trans_losses) - trans_flow_12[j] - demand_n1_hourly[j] == 0)

        # Battery operation
        if j == 0:
            m.addConstr(bat_1_discharge[j] / bat_effi - bat_effi * bat_1_charge[j] ==
                        (args.bat_st_end_mwh * bat_cap_1 * (1 - args.bat_decay) - bat_1_level[j]))
        if j > 0:
            m.addConstr(bat_1_discharge[j] / bat_effi - bat_effi * bat_1_charge[j] ==
                        (bat_1_level[j - 1] * (1 - args.bat_decay) - bat_1_level[j]))
        m.addConstr(bat_1_charge[j] - bat_cap_1 / args.bat_etp <= 0)
        m.addConstr(bat_1_discharge[j] - bat_cap_1 / args.bat_etp <= 0)
        m.addConstr(bat_1_level[j] - bat_cap_1 <= 0)


        #####  -------------- Node 2 constraints --------------  #####
        m.addConstr(wind_util_2[j] - (wind_cap_2 * wind_hourly[j]) <= 0)
        m.addConstr(gt_util_2[j] - gt_cap_2 <= 0)
        m.addConstr(nuc_util_2[j] - nuc_cap_2 <= 0)

        m.addConstr(wind_util_2[j] + gt_util_2[j] + nuc_util_2[j] +
                    trans_flow_12[j] * (1 - args.trans_losses) - trans_flow_21[j] - demand_n2_hourly[j] == 0)


    # battery at the end point
    m.addConstr(bat_1_level[args.num_hours-1] == args.bat_st_end_mwh * bat_cap_1)

    m.update()

    return m
