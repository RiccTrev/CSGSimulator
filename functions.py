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
        minutes=10)  # Tolgo 10 minuti perché pvgis mi torna i dati di produzione al tempo hh:10
    df['P'] = df['P'] / 1000  # Divido per 1k per avere il valore in kW e non in W
    df = df.drop(columns=['time', 'G(i)', 'H_sun', 'T2m', 'WS10m', 'Int'])  # Rimuovo colonne inutilizzate
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
    # Imposto df_PUN che mi serve per fare il merge e il calcolo spesa energia/vendita energia
    df_PUN = df_prezzi[['DataOra', 'PUN']].copy()  # Lavoro su copia dell'originale. Non modifica originale e sopprime errore SettingWithCopyWarning
    df_PUN['DataOra'] = pd.to_datetime(df_PUN['DataOra'], format='%d/%m/%Y %H:%M:%S')
    # df_PUN.loc[df_PUN.DataOra] = pd.to_datetime(df_PUN['DataOra'])

    if PUN_value != -1:
        print('Setting new PUN value')
        df_PUN['PUN'] = PUN_value
    #print(f'VALORE PUN: {df_PUN["PUN"].mean()}')
    for membro in list_utenti:  # Itero sui membri e aggiungo i consumi di ogni membro.
        if membro == 'Utenze Comuni':
            continue
        membri['AUC']['Consumption'] = membri['AUC']['Consumption'] + membri[membro]['Consumption']
    # Istanzio un produttore nella comunità

    #Mi serve una colonna PUN nel df membri['AUC'] per quando calcolo l'incentivo MASE
    membri['AUC']['PUN'] = df_PUN['PUN']
    #membri['AUC'] = membri['AUC'].merge(df_PUN, on='DataOra', how='left')

    produzione = CalcolaProduzionePV(Lat=Lat, Lon=Lon, Potenza=int(potenza), Perdite=perdite)
    # Rielaboro il df produzione per poi unirlo a quello AUC con il dato di produzione per la corretta ora
    produzione['Month'] = produzione['DataOra'].dt.month
    produzione['Day'] = produzione['DataOra'].dt.day
    produzione['Hour'] = produzione['DataOra'].dt.hour
    produzione = produzione.drop(columns='DataOra')
    membri['AUC'] = pd.merge(membri['AUC'], produzione, on=['Month', 'Day', 'Hour'], how="left")
    # Istanzio gli array necessari per i calcoli
    consumo_utenze_comuni = np.array(membri['Utenze Comuni']['Consumption'])  # consumo delle utenze comuni
    consumo_AUC = np.array(membri['AUC']['Consumption'])  # consumo aggregato dell'AUC
    produzione = np.array(membri['AUC']['P'])  # produzione del PV
    autoconsumo = np.zeros(len(produzione), dtype=float)  # autoconsumo istantaneo delle utenze comuni
    produzione_residua = 0  # produzione al netto dell'autoconsumo istantaneo delle utenze comuni
    consumo_residuo_utenze_comuni = 0  # consumo residuo delle utenze comuni dopo aver consumato tutta la produzione.
    SOC = np.zeros(len(produzione), dtype=float)  # state of charge del BESS
    condivisa = np.zeros(len(produzione), dtype=float)  # energia condivisa
    immissione = np.zeros(len(produzione), dtype=float)  # energia immessa in rete
    prelievo = np.zeros(len(produzione),
                        dtype=float)  # energia prelevata dalla rete dall'AUC (utenze comuni comprese)
    # Itero sulla lunghezza degli array
    for x in range(len(consumo_AUC)):
        if x == 0:
            initial_SOC = 0  # Si parte sempre a batteria scarica
        else:
            initial_SOC = SOC[
                x - 1]  # Stato di carica all'inizio dell'iterazione è uguale a quello finale dello stato precedente.
        if consumo_utenze_comuni[x] > produzione[
            x]:  # se il consumo delle utenze comuni è maggiore della produzione
            autoconsumo[x] = produzione[x]
            if initial_SOC > 0:  # verifico lo stato della batteria (se c'è carica)
                consumo_residuo_utenze_comuni = consumo_utenze_comuni[x] - produzione[
                    x]  # calcolo il consumo residuo delle utenze comuni
                scarica_SOC = min(initial_SOC,
                                  consumo_residuo_utenze_comuni)  # calcolo la scarica del bess per soddisfare il consumo residuo delle utenze comuni
                consumo_residuo_utenze_comuni = consumo_residuo_utenze_comuni - scarica_SOC  # ricalcolo eventuale consumo residuo a fronte della scarica del bess
                SOC[x] = initial_SOC - scarica_SOC  # calcolo la carica del bess.
                autoconsumo[x] = autoconsumo[x] + scarica_SOC  # Autoconsumo anche l'energia prelevata dal BESS.
                if consumo_residuo_utenze_comuni > 0:  # se c'è ancora consumo residuo delle utenze comuni => prelevano dalla rete
                    prelievo[x] = consumo_residuo_utenze_comuni
                if SOC[x] >= 0:  # se c'è ancora carica nel bess la uso per soddisfare il fabbisogno dell'AUC.
                    immissione[x] = min(SOC[x], consumo_AUC[x])
                    SOC[x] = SOC[x] - immissione[x]  # Aggiorno quindi la carica nel c_bess
                    prelievo[x] = prelievo[x] + consumo_AUC[
                        x]  # Per soddisfare il fabbisogno dell'AUC bisogna prelevare dalla rete.
                condivisa[x] = min(immissione[x], prelievo[x])
            else:  # se la carica è == 0
                consumo_residuo_utenze_comuni = consumo_utenze_comuni[x] - autoconsumo[x]
                prelievo[x] = consumo_residuo_utenze_comuni + consumo_AUC[x]
                immissione[x] = 0
                condivisa[x] = min(prelievo[x], immissione[x])
                SOC[x] = initial_SOC
        elif consumo_utenze_comuni[x] < produzione[
            x]:  # se invece il consumo delle utenze comuni è inferiore alla produzione
            autoconsumo[x] = min(produzione[x], consumo_utenze_comuni[x])
            produzione_residua = produzione[x] - autoconsumo[x]
            if consumo_AUC[x] <= produzione_residua:  # Se il consumo dell'auc è inferiore alla produzione residua
                if c_bess > 0:
                    immissione[x] = consumo_AUC[x]  # immetto quanto consumo
                    SOC[x] = min(initial_SOC + (produzione_residua - immissione[x]),
                                 c_bess)  # aumento la carica del bess con il surpluss di produzione, posso caricare fino al massimo della c_BESS
                    if initial_SOC + (produzione_residua - immissione[
                        x]) > c_bess:  # se l'initial SOC + (la produzione residua - l'immissione) è maggiore della capacità
                        immissione[x] = immissione[x] + ((produzione[x] - consumo_AUC[x] - autoconsumo[x]) - (
                                c_bess - initial_SOC))  # immetto anche la quantità che non posso immagazzinare nel bess: prima parentesi: energia in surpluss, seconda parentesi: capacità batteria disponibile.
                else:
                    immissione[x] = produzione_residua
                prelievo[x] = consumo_AUC[x]
                condivisa[x] = min(immissione[x], prelievo[x])
            elif consumo_AUC[x] > produzione_residua:  # se invece il consumo dell'auc è maggiore della produzione residua
                consumo_residuo_AUC = consumo_AUC[x] - produzione_residua  # calcolo il consumo residuo dell'AUC
                immissione[x] = produzione_residua
                if initial_SOC > 0:  # se c'è carica nel bess
                    scarica_SOC = min(initial_SOC,
                                      consumo_residuo_AUC)  # calcolo la scarica massima del bess per soddisfare il consumo residuo dei residenti
                    immissione[x] = immissione[
                                        x] + scarica_SOC  # L'immissione che avviene dal BESS viene immessa in rete
                    consumo_residuo_AUC = consumo_residuo_AUC - scarica_SOC  # ricalcolo eventuale consumo residuo a fronte della scarica del bess
                    SOC[x] = initial_SOC - scarica_SOC  # calcolo la carica del bess.
                prelievo[x] = consumo_AUC[x]
                condivisa[x] = min(prelievo[x], immissione[x])
    membri['AUC']['Prelievo'] = prelievo
    membri['AUC']['Immissione'] = immissione
    membri['AUC']['Condivisa'] = condivisa
    membri['AUC']['Autoconsumo'] = autoconsumo
    membri['AUC']['Utenze Comuni'] = consumo_utenze_comuni
    membri['AUC']['SOC'] = SOC

    # Struttura dei costi
    # Ripartizione costi bolletta: la bolletta viene ricostruita con un sistema di proporzioni a partire dal costo della materia energia calcolata come PUN * Energia Prelevata.
    trasporto_e_gestione = parametri.componenti_bolletta[
        'trasporto_e_gestione']  # (%) I costi di trasporto e gestione sono l'8% della bolletta totale
    imposte = parametri.componenti_bolletta['imposte']  # (%) Le imposte sono il 10% della bolletta
    materia_energia = parametri.componenti_bolletta[
        'materia_energia']  # (%) di incidenza della materia energia sulla bolletta
    ###########
    # NB Il calcolo viene fatto sulla somma dei prelievi delle utenze comuni + quelle delle utenze.
    ###########
    # Ricostruisco le componenti della bolletta a partire dalla spesa per la materia energia (semplici proporzioni, sorgente: https://www.arera.it/it/dati/ees5.htm)
    membri['AUC']['MateriaEnergia'] = membri['AUC']['PUN'] * membri['AUC']['Prelievo']
    membri['AUC']['TrasportoEGestione'] = membri['AUC']['MateriaEnergia'] * (
            trasporto_e_gestione / materia_energia)
    membri['AUC']['Imposte'] = membri['AUC']['MateriaEnergia'] * (imposte / materia_energia)
    membri['AUC']['CostoBolletta'] = membri['AUC']['MateriaEnergia'] + membri['AUC']['TrasportoEGestione'] + membri['AUC']['Imposte']
    #membri['AUC']['EntrateCondivisa'] = membri['AUC']['Condivisa'] * incentivo
    membri['AUC']['EntrateCondivisa'] = membri['AUC'].apply(lambda x: CalcolaIncentiviMASE(x['Condivisa'], x['PUN'], potenza), axis=1)
    membri['AUC']['RestituzioneComponentiTariffarie'] = membri['AUC'][
                                                            'Condivisa'] * restituzione_componenti_tariffarie
    membri['AUC']['RID'] = membri['AUC']['Immissione'] * membri['AUC']['PUN']
    membri['AUC']['RisparmioDaAutoconsumo'] = (membri['AUC']['Autoconsumo'] * membri['AUC']['PUN']) * (
            1 + (trasporto_e_gestione / materia_energia) + (imposte / materia_energia))
    membri['AUC']['EntrateTotali'] = membri['AUC']['EntrateCondivisa'] + membri['AUC'][
        'RestituzioneComponentiTariffarie'] + membri['AUC']['RID']


# SimEconomica: ritorna RicaviESCOAnno1, RicaviAUCAnno1, VariazioneCostiAUCAnno1, NPV, TIR, PI, PBT per le varie percentuali di redistribuzione dell'incentivo per l'energia condivisa.
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
    # df: df con le statistiche annuali
    # CostoPV: costo unitario del fotovoltaico (€/kWp)
    # CostoBESS: costo unitario dell'accumulo (€/kWh)
    # CostoInfrastruttura: costo unitario dell'infrastruttura (€/kWx)
    # CostoManodopera: costo unitario della manodopera (€/kWh)
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

    # Per ogni percentuale simulo con metodologia Discounted Cashflow
    percentuali = np.arange(0, 1.05, 0.5)
    orizzonte_temporale = 20  # Anni
    # Array che contengono i risultati
    RicaviESCO = np.zeros(len(percentuali))
    RicaviAUC = np.zeros(len(percentuali))
    VariazioneCostiAUC = np.zeros(len(percentuali))
    NPV = np.zeros(len(percentuali))
    TIR = np.zeros(len(percentuali))
    PI = np.zeros(len(percentuali))
    PBT = np.zeros(len(percentuali))
    results = pd.DataFrame(
        columns=['RicaviEscoAnno1', 'RicaviAUCAnno1', 'VariazioneCostiAUC', 'RataMutuoImpianti', 'NPV', 'TIR', 'PI', 'PBT'])
    #Calcolo rata mutuo per impianti (usata solo caso p = 0, investimento diretto utenti)
    temp = (1+(TAEG/12))**(12*orizzonte_temporale)
    rata = (CAPEX*(temp)*(TAEG/12)/(temp-1))
    #Alla esco arriva tutto il RID + percentuale energia condivisa.
    for p in range(len(percentuali)):
        FlussiScontati = np.zeros(orizzonte_temporale)
        FlussiNonScontati = np.zeros(orizzonte_temporale)
        FlussiCumulati = np.zeros(orizzonte_temporale)
        if percentuali[p] == 0: #AUC investe da solo 
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
                    # Calcolo PBT
                    if FlussiCumulati[a - 1] < 0 and FlussiCumulati[a] > 0:
                        PBT[p] = (a - 1) + (-FlussiCumulati[a - 1] / FlussiScontati[a])
                else:
                    FlussiNonScontati[a] = FlussiNonScontati[a - 1] * (1 - CoefficienteRiduzione)
                    FlussiScontati[a] = FlussiNonScontati[a] / pow((1 + TassoSconto), a)
                    FlussiCumulati[a] = FlussiCumulati[a - 1] + FlussiScontati[a]
                    # Calcolo PBT
                    if FlussiCumulati[a - 1] < 0 and FlussiCumulati[a] > 0:
                        PBT[p] = (a - 1) + (-FlussiCumulati[a - 1] / FlussiScontati[a])
            if PBT[p] == 0:
                PBT[p] == 20
            EsborsoNettoAUC = rata + OPEX + CostiEnergia - RicaviAUC_Anno1
            RicaviESCO[p] = 0
            RicaviAUC[p] = float(RicaviAUC_Anno1.iloc[0])
            CostiPrima = CostiEnergia + RisparmioDaAutoconsumo
            VariazioneCostiAUC[p] = ((EsborsoNettoAUC.iloc[0] - CostiPrima.iloc[0]) / CostiPrima.iloc[0])
            # print(f'Flussi scontati per p = {percentuali[p]}: {FlussiScontati}')
            NPV[p] = np.sum(FlussiScontati)
            TIR[p] = npf.irr(FlussiNonScontati)
            PI[p] = 1 + (NPV[p] / CAPEX)

        else: #Esco investe e da parte dei ricavi ad AUC
            RicaviESCO_Anno1 = RicaviRID + percentuali[p] * RicaviEnergiaCondivisa 
            RicaviAUC_Anno1 = (1 - percentuali[p]) * RicaviEnergiaCondivisa + RisparmioDaAutoconsumo #Aggiunto Risparmio da autoconsumo: il problema è che il PBT viene calcolato su ricavi ESCo 
            for a in range(orizzonte_temporale):
                if a == 0:
                    FlussiScontati[a] = -CAPEX
                    FlussiNonScontati[a] = -CAPEX
                    FlussiCumulati[a] = -CAPEX
                elif a == 1:
                    FlussiScontati[a] = float(RicaviESCO_Anno1.iloc[0]) / pow((1 + TassoSconto), a)
                    FlussiNonScontati[a] = float(RicaviESCO_Anno1.iloc[0])
                    FlussiCumulati[a] = FlussiCumulati[a - 1] + FlussiScontati[a]
                    # Calcolo PBT
                    if FlussiCumulati[a - 1] < 0 and FlussiCumulati[a] > 0:
                        PBT[p] = (a - 1) + (-FlussiCumulati[a - 1] / FlussiScontati[a])
                else:
                    FlussiNonScontati[a] = FlussiNonScontati[a - 1] * (1 - CoefficienteRiduzione)
                    FlussiScontati[a] = FlussiNonScontati[a] / pow((1 + TassoSconto), a)
                    FlussiCumulati[a] = FlussiCumulati[a - 1] + FlussiScontati[a]
                    # Calcolo PBT
                    if FlussiCumulati[a - 1] < 0 and FlussiCumulati[a] > 0:
                        PBT[p] = (a - 1) + (-FlussiCumulati[a - 1] / FlussiScontati[a])
            if PBT[p] == 0:
                PBT[p] == 20
            EsborsoNettoAUC = OPEX + CostiEnergia - RicaviAUC_Anno1
            RicaviESCO[p] = float(RicaviESCO_Anno1.iloc[0])
            RicaviAUC[p] = float(RicaviAUC_Anno1.iloc[0])
            CostiPrima = CostiEnergia + RisparmioDaAutoconsumo
            VariazioneCostiAUC[p] = float((EsborsoNettoAUC.iloc[0] - CostiPrima.iloc[0]) / CostiPrima.iloc[0])
            # print(f'Flussi scontati per p = {percentuali[p]}: {FlussiScontati}')
            NPV[p] = np.sum(FlussiScontati)
            TIR[p] = npf.irr(FlussiNonScontati)
            PI[p] = 1 + (NPV[p] / CAPEX)
    # Metto gli array in un df che ritorno
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