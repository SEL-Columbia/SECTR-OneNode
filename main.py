from model import create_model
from utils import *
import numpy as np


if __name__ == '__main__':
    args    = get_args()
    raw_export_columns, ts_export_columns = get_raw_columns()

    # Create the model
    m = create_model(args)

    # Set model solver parameters
    m.setParam("FeasibilityTol", args.feasibility_tol)
    m.setParam("Method", 2)
    m.setParam("BarConvTol", 0)
    m.setParam("BarOrder", 0)
    m.setParam("Crossover", 0)

    # Solve the model
    m.optimize()

    # Retrieve the model solution
    allvars = m.getVars()

    # Process the model solution
    results    = []
    results_ts = []
    raw_export_columns, ts_export_columns = get_raw_columns()
    results_t, results_ts = raw_results_retrieval(args, m)

    ## Save raw results
    results.append(results_t)
    df_results_raw = pd.DataFrame(np.array(results), columns=raw_export_columns)
    df_results_raw.to_excel(os.path.join(args.results_dir, 'alt_results_notrans.xlsx'))

    df_results_ts = pd.DataFrame(np.array(results_ts), columns=ts_export_columns)
    df_results_ts.to_csv(os.path.join(args.results_dir, 'alt_results_ts_notrans.csv'),
                                     index = False)
