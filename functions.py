import requests
import json
import pandas as pd
import datetime
from datetime import timedelta
from dateutil.easter import *
import numpy as np
import numpy_financial as npf
import math
from calendar import weekday, monthrange
from dateutil import tz
import astral
from astral import LocationInfo
from astral.sun import sun
import parametri

########################################################################################################################
#                                       FUNCTIONS USED IN "main.py"                                           #
########################################################################################################################
def CalcolaProduzionePV(Lat, Lon, Potenza, Perdite):
    """
    This Python function calculates the production of a photovoltaic system based on latitude,
    longitude, power, and losses.
    
    :param Lat: Latitude of the location where the PV system is installed
    :param Lon: Longitude of the location where the photovoltaic system is installed
    :param Potenza: Potenza is the power output of a photovoltaic (PV) system, typically measured in
    kilowatts (kW) or watts (W). It represents the maximum amount of power that the PV system can
    generate under ideal conditions
    :param Perdite: Perdite represents the losses in a photovoltaic (PV) system. These losses can occur
    due to various factors such as shading, soiling, temperature, and inverter inefficiencies. The value
    of Perdite is typically expressed as a percentage of the total energy production that is lost in
    """
    response = requests.get("https://re.jrc.ec.europa.eu/api/v5_2/seriescalc?"
                            "lat=" + str(Lat) +
                            "&lon=" + str(Lon) +
                            "&raddatabase=PVGIS-SARAH2"
                            "&usehorizon=1"
                            "&startyear=2020"
                            "&endyear=2020"
                            "&pvcalculation=1"
                            "&peakpower=" + str(Potenza) +
                            "&pvtechchoice=crystSi"
                            "&loss=" + str(Perdite) +
                            "&optimalinclination = 1"
                            "&optimalangles = 1"
                            "&localtime=1"
                            "&outputformat=json")
    todos = json.loads(response.text)
    my_list = []
    df = pd.DataFrame.from_dict(todos['outputs']['hourly'])
    df['DataOra'] = df.apply(lambda x: datetime.datetime.strptime(x['time'], '%Y%m%d:%H%M'), axis=1)
    df['DataOra'] = df['DataOra'] - timedelta(
        minutes=10)  # I remove 10 minutes because pvgis returns my production data to time hh:10
    df['P'] = df['P'] / 1000  # I divide by 1k to get the value in kW and not W
    df = df.drop(columns=['time', 'G(i)', 'H_sun', 'T2m', 'WS10m', 'Int'])  # Removing unused columns
    return df


def SimulaAUC(potenza, c_bess, list_utenti, df_prezzi, membri, Lat, Lon, perdite, incentivo,
              restituzione_componenti_tariffarie,
              PUN_value):
    """
    This function appears to simulate the AUC (Area Under the Curve) based on various input parameters.
    :param potenza: The `potenza` parameter seems to represent the power or energy capacity. If you have
    any specific questions or need assistance with the rest of the function or parameters, feel free to
    ask!
    :param c_bess: The parameter `c_bess` seems to be related to energy storage systems, specifically
    battery energy storage systems (BESS). It is likely used in the context of simulating the Area Under
    the Curve (AUC) for a certain power system scenario. The `c_bess` parameter could represent
    :param list_utenti: The `list_utenti` parameter likely represents a list of users or customers. It
    could be a list of user IDs, names, or any other identifier for the users involved in the simulation
    :param df_prezzi: The parameter `df_prezzi` likely refers to a DataFrame containing price data. It
    is common to use `df` as an abbreviation for DataFrame in Python, so `df_prezzi` could be a
    DataFrame that stores price information
    :param membri: The parameter "membri" seems to represent a list of members or users. It is likely
    used to store or pass information about the members involved in the simulation or calculation
    process. If you need further assistance with this parameter or any other part of the code, feel free
    to ask!
    :param Lat: The parameters in the function `SimulaAUC` are as follows:
    :param Lon: The `Lon` parameter likely represents the longitude coordinate of a location. It is
    commonly used in geographical calculations and mapping applications to specify the east-west
    position of a point on the Earth's surface
    :param perdite: The parameter "perdite" likely refers to losses in the system, such as transmission
    or distribution losses in an electrical grid. These losses can occur due to factors like resistance
    in power lines, transformers, and other equipment, leading to a decrease in the amount of
    electricity delivered to consumers compared to the
    :param incentivo: The parameter "incentivo" likely refers to an incentive or reward provided in a
    certain context, such as a financial incentive or benefit offered to encourage a specific behavior
    or action. It could be a monetary reward, discount, bonus, or any other form of motivation provided
    to achieve a desired outcome
    :param restituzione_componenti_tariffarie: The parameter "restituzione_componenti_tariffarie" seems
    to refer to a function or a flag that determines whether components of the tariff are returned or
    not. It could be a boolean flag indicating whether certain components of the tariff should be
    refunded or returned in a calculation or process
    :param PUN_value: The `PUN_value` parameter seems to represent the Price of Unbalance (PUN) value in
    the function `SimulaAUC`. The PUN value is the price paid by the market operator for the imbalance
    between the energy injected into the grid and the energy withdrawn from the grid. It
    """
    # I set df_PUN which I need to do the merge and the energy expenditure/energy sale calculation
    df_PUN = df_prezzi[['DataOra', 'PUN']].copy()  # Work on copy of original. Does not modify original and suppresses error SettingWithCopyWarning
    df_PUN['DataOra'] = pd.to_datetime(df_PUN['DataOra'], format='%d/%m/%Y %H:%M:%S')
    
    if PUN_value != -1:
        print('Setting new PUN value')
        df_PUN['PUN'] = PUN_value
    
    for membro in list_utenti:  # Iterate on the members and add the consumption of each member.
        if membro == 'Utenze Comuni':
            continue
        membri['AUC']['Consumption'] = membri['AUC']['Consumption'] + membri[membro]['Consumption']
    

    #I need a PUN column in the df members['AUC'] for when I calculate the MASE incentive.
    membri['AUC']['PUN'] = df_PUN['PUN']

    produzione = CalcolaProduzionePV(Lat=Lat, Lon=Lon, Potenza=int(potenza), Perdite=perdite)
    # I reprocess the production df and then merge it with the AUC with the production data for the correct time
    produzione['Month'] = produzione['DataOra'].dt.month
    produzione['Day'] = produzione['DataOra'].dt.day
    produzione['Hour'] = produzione['DataOra'].dt.hour
    produzione = produzione.drop(columns='DataOra')
    membri['AUC'] = pd.merge(membri['AUC'], produzione, on=['Month', 'Day', 'Hour'], how="left")
    # I instantiate the arrays needed for the calculations.
    consumo_utenze_comuni = np.array(membri['Utenze Comuni']['Consumption'])  # consumo delle utenze comuni
    consumo_AUC = np.array(membri['AUC']['Consumption'])  # aggregate consumption of AUC
    produzione = np.array(membri['AUC']['P'])  # PV production
    autoconsumo = np.zeros(len(produzione), dtype=float)  # Instantaneous self-consumption of common utilities
    produzione_residua = 0  # Production net of instantaneous self-consumption of common utilities
    consumo_residuo_utenze_comuni = 0  # Residual consumption of common utilities after consuming all production.
    SOC = np.zeros(len(produzione), dtype=float)  # state of charge del BESS
    condivisa = np.zeros(len(produzione), dtype=float)  # shared energy 
    immissione = np.zeros(len(produzione), dtype=float)  # energy injected
    prelievo = np.zeros(len(produzione),
                        dtype=float)  # Energy taken from the grid by the AUC (including common utilities)
    # Iteration on the length of arrays
    for x in range(len(consumo_AUC)):
        if x == 0:
            initial_SOC = 0  # Always start with an empty battery
        else:
            initial_SOC = SOC[x - 1]  # The initial state of charge for the iteration is equal to the final state of the previous one.
        if consumo_utenze_comuni[x] > produzione[x]:  # if the consumption of common utilities is greater than the production
            autoconsumo[x] = produzione[x]
            if initial_SOC > 0:  # check the battery status (if it's charged)
                consumo_residuo_utenze_comuni = consumo_utenze_comuni[x] - produzione[x]  # calculate the remaining consumption of common utilities
                scarica_SOC = min(initial_SOC, consumo_residuo_utenze_comuni)  # calculate the BESS discharge to meet the remaining consumption of common utilities
                consumo_residuo_utenze_comuni = consumo_residuo_utenze_comuni - scarica_SOC  # recalculate any remaining consumption after the BESS discharge
                SOC[x] = initial_SOC - scarica_SOC  # calculate the BESS charge.
                autoconsumo[x] = autoconsumo[x] + scarica_SOC  # Self-consume the energy also taken from the BESS.
                if consumo_residuo_utenze_comuni > 0:  # if there is still remaining consumption of common utilities => draw from the grid
                    prelievo[x] = consumo_residuo_utenze_comuni
                if SOC[x] >= 0:  # if there is still charge in the BESS, use it to meet the AUC's needs.
                    immissione[x] = min(SOC[x], consumo_AUC[x])
                    SOC[x] = SOC[x] - immissione[x]  # Update the charge in the BESS
                    prelievo[x] = prelievo[x] + consumo_AUC[x]  # To meet the AUC's needs, it is necessary to draw from the grid.
                condivisa[x] = min(immissione[x], prelievo[x])  # Shared energy calculation between the grid and the AUC.

            else:  # if charge is 0
                consumo_residuo_utenze_comuni = consumo_utenze_comuni[x] - autoconsumo[x]
                prelievo[x] = consumo_residuo_utenze_comuni + consumo_AUC[x]
                immissione[x] = 0
                condivisa[x] = min(prelievo[x], immissione[x])
                SOC[x] = initial_SOC
        elif consumo_utenze_comuni[x] < produzione[x]:  # if the consumption of common utilities is lower than the production
            autoconsumo[x] = min(produzione[x], consumo_utenze_comuni[x])
            produzione_residua = produzione[x] - autoconsumo[x]
            if consumo_AUC[x] <= produzione_residua:  # If the AUC consumption is less than the remaining production
                if c_bess > 0:
                    immissione[x] = consumo_AUC[x]  # I feed in as much as consumed
                    SOC[x] = min(initial_SOC + (produzione_residua - immissione[x]),
                                 c_bess)  # increase the BESS charge with the production surplus, can charge up to the max of c_BESS
                    if initial_SOC + (produzione_residua - immissione[x]) > c_bess:  # if initial SOC + (remaining production - feeding) is greater than capacity
                        immissione[x] = immissione[x] + ((produzione[x] - consumo_AUC[x] - autoconsumo[x]) - (c_bess - initial_SOC))  # also feed in the amount that can't be stored in the BESS: first parenthesis: surplus energy, second parenthesis: available battery capacity.
                else:
                    immissione[x] = produzione_residua
                prelievo[x] = consumo_AUC[x]
                condivisa[x] = min(immissione[x], prelievo[x])
            elif consumo_AUC[x] > produzione_residua:  # if the AUC consumption is greater than the remaining production
                consumo_residuo_AUC = consumo_AUC[x] - produzione_residua  # calculate the remaining AUC consumption
                immissione[x] = produzione_residua
                if initial_SOC > 0:  # if there is charge in the BESS
                    scarica_SOC = min(initial_SOC,
                                      consumo_residuo_AUC)  # calculate the maximum BESS discharge to meet the remaining residents' consumption
                    immissione[x] = immissione[x] + scarica_SOC  # The discharge happening from the BESS is fed into the grid
                    consumo_residuo_AUC = consumo_residuo_AUC - scarica_SOC  # recalculate any remaining consumption after the BESS discharge
                    SOC[x] = initial_SOC - scarica_SOC  # calculate the BESS charge.

                prelievo[x] = consumo_AUC[x]
                condivisa[x] = min(prelievo[x], immissione[x])
    membri['AUC']['Prelievo'] = prelievo
    membri['AUC']['Immissione'] = immissione
    membri['AUC']['Condivisa'] = condivisa
    membri['AUC']['Autoconsumo'] = autoconsumo
    membri['AUC']['Utenze Comuni'] = consumo_utenze_comuni
    membri['AUC']['SOC'] = SOC

    # Cost structure
    # Bill cost allocation: the bill is reconstructed using a proportion system from the cost of energy matter calculated as PUN * Energy Withdrawn.
    trasporto_e_gestione = parametri.componenti_bolletta[
        'trasporto_e_gestione']  # (%) Transportation and management costs are 8% of the total bill
    imposte = parametri.componenti_bolletta['imposte']  # (%) Taxes are 10% of the bill
    materia_energia = parametri.componenti_bolletta[
        'materia_energia']  # (%) of the energy matter's impact on the bill
    ###########
    # NB The calculation is made on the sum of withdrawals from common utilities + those from individual utilities.
    ###########
    # I rebuild the components of the bill starting from the expenditure for energy matter (simple proportions, source: https://www.arera.it/it/dati/ees5.htm)

    membri['AUC']['MateriaEnergia'] = membri['AUC']['PUN'] * membri['AUC']['Prelievo']
    membri['AUC']['TrasportoEGestione'] = membri['AUC']['MateriaEnergia'] * (
            trasporto_e_gestione / materia_energia)
    membri['AUC']['Imposte'] = membri['AUC']['MateriaEnergia'] * (imposte / materia_energia)
    membri['AUC']['CostoBolletta'] = membri['AUC']['MateriaEnergia'] + membri['AUC']['TrasportoEGestione'] + membri['AUC']['Imposte']
    membri['AUC']['EntrateCondivisa'] = membri['AUC'].apply(lambda x: CalcolaIncentiviMASE(x['Condivisa'], x['PUN'], potenza), axis=1)
    membri['AUC']['RestituzioneComponentiTariffarie'] = membri['AUC'][
                                                            'Condivisa'] * restituzione_componenti_tariffarie
    membri['AUC']['RID'] = membri['AUC']['Immissione'] * membri['AUC']['PUN']
    membri['AUC']['RisparmioDaAutoconsumo'] = (membri['AUC']['Autoconsumo'] * membri['AUC']['PUN']) * (
            1 + (trasporto_e_gestione / materia_energia) + (imposte / materia_energia))
    membri['AUC']['EntrateTotali'] = membri['AUC']['EntrateCondivisa'] + membri['AUC'][
        'RestituzioneComponentiTariffarie'] + membri['AUC']['RID']


#SimEconomics: returns RevenuesESCOYear1, RevenuesAUCAYear1, VariationCostsAUCAYear1, NPV, IRR, PI, PBT for the various redistribution percentages of the shared energy incentive.
def SimEconomicaAUC(df, CostoPV, CostoBESS, CostoInfrastruttura, CostoManodopera, CostoUnitarioGestione,
                 PercentualeAssicurazione, TassoSconto, CoefficienteRiduzione, PotenzaPV, CapacitaBESS):
    """
    This Python function calculates the economic feasibility of a project involving photovoltaic systems
    and battery energy storage systems.
    
    :param df: It looks like you were about to provide a description of the parameters for the function
    `SimEconomicaAUC`. Please go ahead and provide the descriptions for the remaining parameters so that
    I can assist you further
    :param CostoPV: CostoPV is the cost of the photovoltaic (PV) system
    :param CostoBESS: CostoBESS is the cost of the Battery Energy Storage System (BESS) in the economic
    simulation
    :param CostoInfrastruttura: CostoInfrastruttura is the cost of infrastructure. It is one of the
    parameters required for the function SimEconomicaAUC
    :param CostoManodopera: CostoManodopera is the cost of labor for the economic simulation. It
    represents the expenses related to the workforce required for the project or operation being
    analyzed
    :param CostoUnitarioGestione: CostoUnitarioGestione is the unit cost of management. It represents
    the cost associated with managing the system or project on a per unit basis. This cost could include
    expenses such as monitoring, maintenance, and operational costs
    :param PercentualeAssicurazione: The parameter "PercentualeAssicurazione" represents the percentage
    of insurance cost in the economic simulation. It is used to calculate the insurance cost based on
    the total cost of the project
    :param TassoSconto: The "TassoSconto" parameter in the function "SimEconomicaAUC" represents the
    discount rate or the rate at which future cash flows are discounted to determine their present
    value. It is typically expressed as a percentage and is used to account for the time value of money
    in financial calculations
    :param CoefficienteRiduzione: The parameter "CoefficienteRiduzione" typically refers to a reduction
    coefficient or factor used in economic or financial calculations. It is used to adjust or reduce
    certain values or costs in the model based on specific criteria or assumptions. In the context of
    your function "SimEconomicaAUC", the
    :param PotenzaPV: PotenzaPV represents the power capacity of the photovoltaic (PV) system in
    kilowatts (kW). It is the maximum amount of power that the PV system can generate under ideal
    conditions
    :param CapacitaBESS: It looks like you were about to provide a description for the parameter
    `CapacitaBESS`, but the description is missing. Could you please provide more information or let me
    know if you need help with something specific related to this parameter?
    """
    InvestimentoPV = CostoPV * PotenzaPV
    InvestimentoBESS = CostoBESS * CapacitaBESS
    InvestimentoInfrastruttura = CostoInfrastruttura * (PotenzaPV + CapacitaBESS)
    InvestimentoManodopera = CostoManodopera * PotenzaPV
    CAPEX = InvestimentoPV + InvestimentoBESS + InvestimentoInfrastruttura + InvestimentoManodopera
    CostoGestione = CostoUnitarioGestione * (PotenzaPV + CapacitaBESS)
    CostoAssicurazione = CAPEX * PercentualeAssicurazione
    OPEX = CostoGestione + CostoAssicurazione
    RicaviRID = df['RID']
    RicaviEnergiaCondivisa = df['EntrateCondivisa'] + df['RestituzioneComponentiTariffarie']
    RicaviTotali = RicaviRID + RicaviEnergiaCondivisa
    CostiEnergia = df['CostoBolletta']
    RisparmioDaAutoconsumo = df['RisparmioDaAutoconsumo']
    TAEG = parametri.parametri_economici['TAEG']

    # For each percentage I simulate with Discounted Cashflow methodology.    
    percentuali = np.arange(0, 1.05, 0.5)
    orizzonte_temporale = 20  # Anni
    # Arrays containing the results
    RicaviESCO = np.zeros(len(percentuali))
    RicaviAUC = np.zeros(len(percentuali))
    VariazioneCostiAUC = np.zeros(len(percentuali))
    NPV = np.zeros(len(percentuali))
    TIR = np.zeros(len(percentuali))
    PI = np.zeros(len(percentuali))
    PBT = np.zeros(len(percentuali))
    results = pd.DataFrame(
        columns=['RicaviEscoAnno1', 'RicaviAUCAnno1', 'VariazioneCostiAUC', 'RataMutuoImpianti', 'NPV', 'TIR', 'PI', 'PBT'])
    #Calculation of loan installment for facilities (used only case p = 0, direct users investment)
    temp = (1+(TAEG/12))**(12*orizzonte_temporale)
    rata = (CAPEX*(temp)*(TAEG/12)/(temp-1))
    #Alla esco arriva tutto il RID + percentuale energia condivisa.
    for p in range(len(percentuali)):
        FlussiScontati = np.zeros(orizzonte_temporale)
        FlussiNonScontati = np.zeros(orizzonte_temporale)
        FlussiCumulati = np.zeros(orizzonte_temporale)
        if percentuali[p] == 0: #AUC invests alone 
            RicaviESCO_Anno1 = 0
            RicaviAUC_Anno1 = RicaviRID + RicaviEnergiaCondivisa + RisparmioDaAutoconsumo
            for a in range(orizzonte_temporale):
                if a == 0:
                    FlussiScontati[a] = -CAPEX
                    FlussiNonScontati[a] = -CAPEX
                    FlussiCumulati[a] = -CAPEX
                elif a == 1:
                    FlussiScontati[a] = float(RicaviAUC_Anno1.iloc[0]) / pow((1 + TassoSconto), a)
                    FlussiNonScontati[a] = float(RicaviAUC_Anno1.iloc[0])
                    FlussiCumulati[a] = FlussiCumulati[a - 1] + FlussiScontati[a]
                    #  PBT
                    if FlussiCumulati[a - 1] < 0 and FlussiCumulati[a] > 0:
                        PBT[p] = (a - 1) + (-FlussiCumulati[a - 1] / FlussiScontati[a])
                else:
                    FlussiNonScontati[a] = FlussiNonScontati[a - 1] * (1 - CoefficienteRiduzione)
                    FlussiScontati[a] = FlussiNonScontati[a] / pow((1 + TassoSconto), a)
                    FlussiCumulati[a] = FlussiCumulati[a - 1] + FlussiScontati[a]
                    #  PBT
                    if FlussiCumulati[a - 1] < 0 and FlussiCumulati[a] > 0:
                        PBT[p] = (a - 1) + (-FlussiCumulati[a - 1] / FlussiScontati[a])
            if PBT[p] == 0:
                PBT[p] == 20
            EsborsoNettoAUC = rata + OPEX + CostiEnergia - RicaviAUC_Anno1
            RicaviESCO[p] = 0
            RicaviAUC[p] = float(RicaviAUC_Anno1.iloc[0])
            CostiPrima = CostiEnergia + RisparmioDaAutoconsumo
            VariazioneCostiAUC[p] = ((EsborsoNettoAUC.iloc[0] - CostiPrima.iloc[0]) / CostiPrima.iloc[0])
            NPV[p] = np.sum(FlussiScontati)
            TIR[p] = npf.irr(FlussiNonScontati)
            PI[p] = 1 + (NPV[p] / CAPEX)

        else: #Esco invests and gives part of revenues to AUC
            RicaviESCO_Anno1 = RicaviRID + percentuali[p] * RicaviEnergiaCondivisa 
            RicaviAUC_Anno1 = (1 - percentuali[p]) * RicaviEnergiaCondivisa + RisparmioDaAutoconsumo 
            for a in range(orizzonte_temporale):
                if a == 0:
                    FlussiScontati[a] = -CAPEX
                    FlussiNonScontati[a] = -CAPEX
                    FlussiCumulati[a] = -CAPEX
                elif a == 1:
                    FlussiScontati[a] = float(RicaviESCO_Anno1.iloc[0]) / pow((1 + TassoSconto), a)
                    FlussiNonScontati[a] = float(RicaviESCO_Anno1.iloc[0])
                    FlussiCumulati[a] = FlussiCumulati[a - 1] + FlussiScontati[a]
                    #  PBT
                    if FlussiCumulati[a - 1] < 0 and FlussiCumulati[a] > 0:
                        PBT[p] = (a - 1) + (-FlussiCumulati[a - 1] / FlussiScontati[a])
                else:
                    FlussiNonScontati[a] = FlussiNonScontati[a - 1] * (1 - CoefficienteRiduzione)
                    FlussiScontati[a] = FlussiNonScontati[a] / pow((1 + TassoSconto), a)
                    FlussiCumulati[a] = FlussiCumulati[a - 1] + FlussiScontati[a]
                    #  PBT
                    if FlussiCumulati[a - 1] < 0 and FlussiCumulati[a] > 0:
                        PBT[p] = (a - 1) + (-FlussiCumulati[a - 1] / FlussiScontati[a])
            if PBT[p] == 0:
                PBT[p] == 20
            EsborsoNettoAUC = OPEX + CostiEnergia - RicaviAUC_Anno1
            RicaviESCO[p] = float(RicaviESCO_Anno1.iloc[0])
            RicaviAUC[p] = float(RicaviAUC_Anno1.iloc[0])
            CostiPrima = CostiEnergia + RisparmioDaAutoconsumo
            VariazioneCostiAUC[p] = float((EsborsoNettoAUC.iloc[0] - CostiPrima.iloc[0]) / CostiPrima.iloc[0])
            NPV[p] = np.sum(FlussiScontati)
            TIR[p] = npf.irr(FlussiNonScontati)
            PI[p] = 1 + (NPV[p] / CAPEX)
    # I put the arrays into a df that I return
    results['PercentualeRedistribuzioneEsco'] = pd.Series(percentuali)
    results['CAPEX'] = CAPEX
    results['OPEX'] = OPEX
    results['RicaviEscoAnno1'] = pd.Series(RicaviESCO)
    results['RicaviAUCAnno1'] = pd.Series(RicaviAUC)
    results['RataMutuoImpianti'] = rata
    results['VariazioneCostiAUC'] = pd.Series(VariazioneCostiAUC)
    results['NPV'] = pd.Series(NPV)
    results['TIR'] = pd.Series(TIR)
    results['PI'] = pd.Series(PI)
    results['PBT'] = pd.Series(PBT)
    results['PV'] = PotenzaPV
    results['BESS'] = CapacitaBESS

    return results

def CalcolaIncentiviMASE(x, pz, potenza_totale):
    """
    This function calculates incentives for energy efficiency based on input parameters.
    
    :param x: It looks like you were about to provide some information about the parameter `x`. How can
    I assist you further with this function `CalcolaIncentiviMASE`?
    :param pz: Please provide more information about the parameters so I can assist you better
    :param potenza_totale: It looks like you were about to provide some information about the parameters
    of the function `CalcolaIncentiviMASE`, but the description got cut off. Could you please provide
    more details or let me know how I can assist you further with this function?
    """
    if potenza_totale < 200: # potenza < 200
        return min(parametri.incentiviT1['fissa'] + min(max(0, 0.180-pz), 0.040), parametri.incentiviT1['massimo']) * x
    elif 200 <= potenza_totale < 600: # potenza >=200 & <600
        return min(parametri.incentiviT2['fissa'] + min(max(0, 0.180 - pz), 0.040), parametri.incentiviT2['massimo']) * x
    elif potenza_totale > 600:  # potenza >600
        return min(parametri.incentiviT3['fissa'] + min(max(0, 0.180 - pz), 0.040), parametri.incentiviT3['massimo']) * x