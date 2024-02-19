# Collective self consumption group techno economic simulator

This software is designed to run techno-economic simulations of CSGs accordingly to the italian regulation. 

## How to use (TL;DR version)
1) Clone repository.
2) Run 
```pip install -r requirements.txt'```.
3) Modify files in the Input folder according to your specification. 
4) Run form the working directory
```'python main.py'```
5) Results will be saved in Output folder. 


## Files:

### Main.py 
This Python script is designed to perform a comprehensive analysis and simulation of energy consumption, production, and economic aspects for a community utilizing photovoltaic (PV) systems and battery energy storage systems (BESS). The main functionalities of this script include:

Parameter Loading: The script starts by loading necessary parameters such as geographical coordinates (latitude and longitude), loss factors, and other predefined parameters from a file. This is crucial for tailoring the simulation to specific conditions and configurations.

File Handling: It establishes directories for input and output data, ensuring that output data is stored in a structured manner. If the output directory does not exist, it is created.

Data Importation:

PUN Data: The script imports Price of Unbalance (PUN) data from an Excel file, which is essential for calculating energy costs.
Load Profiles: It also imports load profiles for Utilities from another Excel file. These profiles are fundamental for understanding energy consumption patterns.
Data Processing: The script processes the imported data to create month, day, and hour columns for each DataFrame. This temporal information is necessary for merging with production data and conducting time-specific analyses.

Scenario Evaluation: It evaluates various combinations of PV and BESS sizes to understand their impact on energy production, consumption, and storage. This step involves generating a list of all possible sizing scenarios based on predefined PV and BESS options.

Simulation: For each scenario, the script simulates energy consumption, production, and storage dynamics. It adjusts for factors such as incentives and tariff components, and calculates energy flows among the community, the BESS, and the grid.

Economic Evaluation: Utilizing the simulation results, the script performs an economic analysis to evaluate the financial feasibility of each PV-BESS combination. This includes calculations of costs and savings related to energy consumption, production, and storage.

Output Generation: The script writes the simulation and economic evaluation results to Excel files for each scenario. It ensures that if an output file already exists, it is replaced with the updated version. The output files include detailed data on energy consumption, production, storage, and economic metrics on a monthly and annual basis.

Aggregation and Analysis: Finally, the script aggregates the annual data across all scenarios and provides a comprehensive overview of the performance and economic viability of different PV-BESS configurations.

This script is a powerful tool for communities, energy managers, and policymakers to assess the potential benefits and costs of adopting PV and BESS technologies. It leverages detailed data and sophisticated simulations to inform decisions regarding sustainable energy solutions.

### parametri.py
Include parameters of the simulation.

- Latitude
- Longitude
- PV System Losses: Set at 16%, accounting for inefficiencies.
- Dimensioning: Evaluates combinations of electricity prices (PUN_list), PV system sizes (listaPV), and BESS capacities (listaBESS).
- Economic Parameters: Includes costs for PV and BESS installation, labor, infrastructure, management, insurance, discount rate, and annual performance degradation of PV systems.
- Incentives: Features incentives for energy production and storage, including a new tiered scheme (incentiviT1, incentiviT2, incentiviT3) based on system capacity.
- Bill Components: Details the percentages of transportation, management costs, taxes, and the impact of energy matter on the total bill, with energy matter calculated by deducting taxes and management costs from 100%.

### functions.py
Include funcitons used in the main.py script. 
Description of the function is provided inside the file.

## How to setup and run: 
1) Clone repository. Optionally in a virtual environment.
2) Run 
```pip install -r requirements.txt'```.
3) Inside the Input folder there are several files: 
    - 'Carichi_utenze_AUC.xlsx': the sheet 'Aggregato' contains the load profile of all the apartments in the CSG. The sheet 'Utenze Comuni' is the load profile of the common utilites of the building. These sheets can be modified accordingly to the requirements of the user. 
    - 'PUN.xlsx': file containing the energy price. 
4) Run form the working directory
```'python main.py'```
5) Results will be saved in "Output" folder. 


## License

[GPL-3.0](https://github.com/RiccTrev/CSGSimulator/blob/main/license.txt)
