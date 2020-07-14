# SELCEM 
Sustainable Engineering Lab Clean Energy Model (SELCEM) is an energy system capacity expansion model, using Gurobi optimizer and coding in Python. 
This repository includes two different versions, one-node and two-node. 
The formulation can access through [SELCEM_FORMULATION.pdf](https://github.com/SEL-Columbia/SELCEM/blob/master/SELCEM_FORMULATION.pdf)


## One-Node System
The basic easy-to-use model, includes the parameters, variables, and constraints in the single file. <br />

**File**: <br />
[one_node_system.py](https://github.com/SEL-Columbia/SELCEM/blob/master/one_node_system.py) - 
At once the input data set up, the file can be run individually. 


## Two-Nodes System  
Two-Nodes System Model is built as an expandable structure for broad use, where the transmission system is added to the system, 
although the current setting is for the model-comparison study only. 
Except for the transmission, the basic formulations are the same as the One-Node System. <br />

**Files**:  <br />
[model.py](https://github.com/SEL-Columbia/SELCEM/blob/master/model.py) - The variables, constraints, objective function are sitting here; <br />
[utils.py](https://github.com/SEL-Columbia/SELCEM/blob/master/utils.py) - Functions used in the model, including output results extracting and more; <br /> 
[params.yaml](https://github.com/SEL-Columbia/SELCEM/blob/master/params.yaml) - Parameters are stored; <br /> 
[main.py](https://github.com/SEL-Columbia/SELCEM/blob/master/main.py) - Once the model is set up, we can run this file.
