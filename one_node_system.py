import numpy as np
import pandas as pd
from gurobipy import *

# load data: demand; solar; wind
demand_full = pd.read_csv('SEM_TEMOA_demand.csv', header=1)
solar_full = pd.read_csv('SEM_TEMOA_solar.csv', header=1)
wind_full = pd.read_csv('SEM_TEMOA_wind.csv', header=1)

# time period 1 year
n_year = 1
T = 8784

# sort out kwh data
load = demand_full['demand'][0:T]
solar_po = solar_full['solar capacity'][0:T]
wind_po = wind_full['wind capacity'][0:T]

# generator type True | False to choose the generator types in the model
solar_on   = True
wind_on    = True
ccgt_on    = True
nuclear_on = True
bat_on     = True

# ------------------ Cost Assumptions ------------------ #
# ------------------------------------------------------ #
# capital: $/kW | cap_rate - ar | Fix_OM: $/kW-yr | var_OM: $/kWh | Fuel: $/kWh | life: yr

# Solar
solar_capital = 788
solar_ar     = 0.0806
solar_fix_om = 22.02
solar_var_om = 0
solar_fuel   = 0
solar_yr     = 30

# Wind
wind_capital = 1095
wind_ar     = 0.0806
wind_fix_om = 47.47
wind_var_om = 0
wind_fuel   = 0
wind_yr     = 30

# CCGT
ccgt_capital = 982
ccgt_ar     = 0.0944
ccgt_fix_om = 11.11
ccgt_var_om = 0.00354
ccgt_fuel   = 0.0191
ccgt_ce     = 0.54
ccgt_yr     = 20

# Nuclear
nuclear_capital = 1027
nuclear_ar     = 0.075
nuclear_fix_om = 101.28
nuclear_var_om = 0.00232
nuclear_fuel   = 0.0075
nuclear_ce     = 0.33
nuclear_yr     = 40

# Battery cost and performance
bat_capital = 26  # $/kWh
bat_ar     = 0.1424
bat_fix_om = 0
bat_var_om = 0
bat_fuel   = 0
bat_yr     = 10
bat_eff    = np.sqrt(0.9)      # for both charge and discharge (single-way)
bat_dec    = 1.14e-6           # decay each hour ()
bat_e_to_p = 6.008             # energy/power ratio
bat_ini    = 0.5               # at the beginning, battery initial storage

# cost consumption: *** in total ***
#                   *1000 -> MWh | *yr -> time period
fix_cost_solar   = (solar_capital * solar_ar + solar_fix_om) * 1000 * n_year
fix_cost_wind    = (wind_capital * wind_ar + wind_fix_om) * 1000 * n_year
fix_cost_ccgt    = (ccgt_capital * ccgt_ar + ccgt_fix_om) * 1000 * n_year
fix_cost_nuclear = (nuclear_capital * nuclear_ar + nuclear_fix_om) * 1000 * n_year
fix_cost_bat     = (bat_capital * bat_ar + bat_fix_om) * 1000 * n_year

variable_cost_solar   = solar_var_om * 1000
variable_cost_wind    = wind_var_om * 1000
variable_cost_ccgt    = (ccgt_fuel / ccgt_ce + ccgt_var_om) * 1000
variable_cost_nuclear = (nuclear_fuel / nuclear_ce + nuclear_var_om) * 1000
variable_cost_bat     = bat_var_om * 1000



# ------------ object: capital and utilization ------------ #
# --------------------------------------------------------- #
m = Model("simple model")
t_range = range(T)

wind_cap = m.addVar(obj = fix_cost_wind, name = 'Wind Capacity')
solar_cap = m.addVar(obj = fix_cost_solar, name = 'Solar Capacity')
ccgt_cap = m.addVar(obj = fix_cost_ccgt, name = 'CCGT Capacity')
nuclear_cap = m.addVar(obj = fix_cost_nuclear, name = 'Nuclear Capacity')
bat_cap = m.addVar(obj = fix_cost_bat, name = 'Battery Capacity')

solar_util = m.addVars(t_range, obj=0)
wind_util = m.addVars(t_range, obj=0)
ccgt_util = m.addVars(t_range, obj=variable_cost_ccgt)
nuclear_util = m.addVars(t_range, obj=variable_cost_nuclear)
sto_bat = m.addVars(range(T + 1), obj=0)
bat_cha = m.addVars(range(T), obj=0)
bat_dis = m.addVars(range(T), obj=0)


# ------------ constraints of the model ------------ #
# -------------------------------------------------- #

# remove designated generators
if not solar_on:
    solar_cap = 0
if not wind_on:
    wind_cap = 0
if not ccgt_on:
    ccgt_cap = 0
if not nuclear_on:
    nuclear_cap = 0
if not bat_on:
    bat_cap = 0

# for the starting/ending point of the battery
m.addConstr(sto_bat[0] == bat_ini * bat_cap)
m.addConstr(sto_bat[T] == bat_ini * bat_cap)

for i in t_range:
    # meet load condition
    m.addConstr(wind_util[i] + solar_util[i] + ccgt_util[i] + nuclear_util[i] + bat_dis[i] - bat_cha[i] - load[i] == 0)

    # generation limits
    m.addConstr(wind_util[i] - (wind_cap * wind_po[i]) <= 0)
    m.addConstr(solar_util[i] - (solar_cap * solar_po[i]) <= 0)
    m.addConstr(ccgt_util[i] - ccgt_cap <= 0)
    m.addConstr(nuclear_util[i] - nuclear_cap <= 0)

    # storage calculation
    m.addConstr(sto_bat[i + 1] - (sto_bat[i] * (1 - bat_dec) + bat_cha[i] * bat_eff - bat_dis[i] / bat_eff) == 0)
    # the charge - discharge rate <= power rate
    m.addConstr(bat_cha[i] - bat_cap / bat_e_to_p <= 0)
    m.addConstr(bat_dis[i] - bat_cap / bat_e_to_p <= 0)
    m.addConstr(sto_bat[i + 1] - bat_cap <= 0)  # the max storage <= cap


# ----- results ----- #
# ------------------- #
# run the model
m.update()
m.optimize()
# find the variables
obj = m.getObjective()
allvars = m.getVars()

# print the capacities
cap_results = pd.DataFrame(np.random.randn(5,2), columns=['Name','Capacity - MW(h)'])
pd.options.mode.chained_assignment = None
for i, j in enumerate(allvars[0:6]):
    cap_results['Name'][i] = j.varName
    cap_results['Capacity - MW(h)'][i] = j.x
print(cap_results)

# save a csv for the time series;
# / 1000 convert the unit into GW
power_util_results = demand_full.copy()

solar_power_util = np.zeros(T)
for i, j in enumerate(allvars[5:(5+T)]):
    solar_power_util[i] = j.x / 1000

wind_power_util = np.zeros(T)
for i, j in enumerate(allvars[(5+1*T):(5+2*T)]):
    wind_power_util[i] = j.x / 1000

ccgt_power_util = np.zeros(T)
for i, j in enumerate(allvars[(5+2*T):(5+3*T)]):
    ccgt_power_util[i] = j.x / 1000

nuclear_power_util = np.zeros(T)
for i, j in enumerate(allvars[(5+3*T):(5+4*T)]):
    nuclear_power_util[i] = j.x / 1000

bat_storage = np.zeros(T)
for i, j in enumerate(allvars[(5+4*T+1):(5+5*T+1)]):
    bat_storage[i] = j.x / 1000

bat_charge = np.zeros(T)
for i, j in enumerate(allvars[(5+5*T+1):(5+6*T+1)]):
    bat_charge[i] = j.x / 1000

bat_discharge = np.zeros(T)
for i, j in enumerate(allvars[(5+6*T+1):(5+7*T+1)]):
    bat_discharge[i] = j.x / 1000

power_util_results['solar_power_util_gwh'] = solar_power_util
power_util_results['wind_power_util_gwh'] = wind_power_util
power_util_results['ccgt_power_util_gwh'] = ccgt_power_util
power_util_results['nuclear_power_util_gwh'] = nuclear_power_util
power_util_results['bat_storage_gwh'] = bat_storage
power_util_results['bat_charge_gwh'] = bat_charge
power_util_results['bat_discharge_gwh'] = bat_discharge


cap_results.to_csv('capacity_solar-bat.csv')
power_util_results.to_csv('power_util_results_solar-bat.csv')


LCOE = m.objVal / (np.mean(load) * T)
print("LCOE:${}/MWh".format(LCOE))
