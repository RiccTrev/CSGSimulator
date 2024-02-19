import pandas as pd
#pd.options.mode.chained_assignment = None
import numpy as np
import itertools
import functions
import parametri
import os
from pathlib import Path

#IMPOSTA LAT, LON e perdite
# Li usa le API di PVGIS per il calcolo della produzione del PV
# Locallizzazione
Lat = parametri.Lat
Lon = parametri.Lon
# Perdite PV (%)
perdite = parametri.perdite
# Potenza da installare presso l'AUC (kWp)
#potenza = 20
# Capacità BESS (kWh)
#c_bess = 5


cwd = os.getcwd()
input_directory = cwd + "/Input/"
output_directory = cwd + "/Output/"
if not os.path.exists(output_directory):
    os.mkdir(output_directory)

# Importo PUN in un Dataframe
try:
    fn = input_directory + 'PUN_2021_Aggiustato.xlsx'
    xl = pd.ExcelFile(fn)
    # xl.sheet_names
    # Creo un dizionario di DataFrame.
    dfs = {sh: xl.parse(sh, header=0) for sh in xl.sheet_names}
    # Stampo le chiavi del dizionario (nomi dei workspace di excel)
    dfs.keys()
    df_prezzi = dfs['Prezzi-Prices']
except:
    raise TypeError('Non sono riuscito ad aprire il file.')

# Importo i profili di carico delle Utenze
try:
    fn = input_directory + 'Carichi_utenze_AUC.xlsx'
    xl = pd.ExcelFile(fn)
    # xl.sheet_names
    # Creo un dizionario di DataFrame.
    membri = {sh: xl.parse(sh, header=0) for sh in xl.sheet_names}
    # Stampo le chiavi del dizionario (nomi dei workspace di excel)
    membri.keys()
except:
    raise TypeError('Non sono riuscito ad aprire il file.')

# Creo le colonne month, day, hour per ogni dataframe. Mi serve per fare il merge con i dati di produzione.
for membro in membri.keys():
    membri[membro]['Month'] = membri[membro]['DataOra'].dt.month
    membri[membro]['Day'] = membri[membro]['DataOra'].dt.day
    membri[membro]['Hour'] = membri[membro]['DataOra'].dt.hour
    membri[membro]['DayOfWeek'] = membri[membro]['DataOra'].dt.dayofweek

# Lista degli utenti della configurazione
list_utenti = list(membri.keys())
print(f'Evaluating users: {list_utenti}')

df_annuali = pd.DataFrame()
# Coppie potenza pv-bess
PUN_list = parametri.PUN_list
listaPV = parametri.listaPV
listaBESS = parametri.listaBESS 
list_dimensionamenti = list(itertools.product(listaPV, listaBESS))
print(f'Evaluating {len(list_dimensionamenti)} combinations.\nTotal number of scenarios: {len(list_dimensionamenti)*len(PUN_list)}')

ElencoSimEconomiche = pd.DataFrame()
#Simulo tutti i dimensionamenti sepecificati con il PUN specificato nel file.
df_prezzi['PUN'] = df_prezzi['PUN'] / 1000


###############################################
###############################################
df_annuali = pd.DataFrame() # Empty df_annuali
for PUN_value in PUN_list:
    for elements in list_dimensionamenti:
        potenza = elements[0]
        c_bess = elements[1]
        print(f'Evaluating iteration with PUN: {PUN_value}€/kWh, PV: {potenza}kWp, BESS: {c_bess}kWh')
        membri['AUC'] = pd.DataFrame()
        # Istanzio la colonna DataOra
        membri['AUC']['DataOra'] = np.array(membri[list_utenti[0]]['DataOra'])
        membri['AUC']['Month'] = membri['AUC']['DataOra'].dt.month
        membri['AUC']['Day'] = membri['AUC']['DataOra'].dt.day
        membri['AUC']['Hour'] = membri['AUC']['DataOra'].dt.hour
        membri['AUC']['Consumption'] = 0
        functions.SimulaAUC(potenza, c_bess, list_utenti, df_prezzi, membri, Lat, Lon, perdite, parametri.incentivi['IncentivoAUC'],
                            parametri.incentivi['RestituzioneComponentiTariffarie'], PUN_value)

        # Creazione df mensili ed annuali
        AUC_mensile = membri['AUC'].resample('ME', on='DataOra').sum().drop(
            columns=['Month', 'Day', 'Hour', 'PUN', 'SOC']).reset_index()
        AUC_annuale = membri['AUC'].resample('YE', on='DataOra').sum().drop(
            columns=['Month', 'Day', 'Hour', 'PUN', 'SOC']).reset_index()
        SimEconomica = functions.SimEconomicaAUC(AUC_annuale, parametri.parametri_economici['PV'], parametri.parametri_economici['BESS'],
                                              parametri.parametri_economici['Infrastruttura'],
                                              parametri.parametri_economici['Manodopera'],
                                              parametri.parametri_economici['Gestione'],
                                              parametri.parametri_economici['Assicurazione'],
                                              parametri.parametri_economici['TassoSconto'],
                                              parametri.parametri_economici['CoeffRiduzionePrestazioni'], potenza, c_bess)
        SimEconomica['RapportoCondivisaProduzione'] = AUC_annuale['Condivisa'][0] / AUC_annuale['P'][0]
        SimEconomica['PUN'] = PUN_value
        ElencoSimEconomiche = pd.concat([ElencoSimEconomiche, SimEconomica])

        # Scrittura in output
        try:
            file = Path(
                output_directory + 'output_' + str(
                    PUN_value * 1000) + '_' + str(
                    potenza) + '_' + str(c_bess) + '.xlsx')
            if file.exists():
                print("File already exist. Deleting the old one...")
                os.remove(file)
            with pd.ExcelWriter(
                    output_directory + 'output_' + str(
                        PUN_value * 1000) + '_' + str(
                        potenza) + '_' + str(c_bess) + '.xlsx') as writer:
                membri['AUC'].to_excel(writer, sheet_name='AUC', index=False)
                AUC_mensile.to_excel(writer, sheet_name='AUC_mensile', index=False)
                AUC_annuale.to_excel(writer, sheet_name='AUC_annuale', index=False)
                SimEconomica.to_excel(writer, sheet_name='SimEconomica', index=False)
                print('Writing file output_' + str(PUN_value * 1000) + '_' + str(potenza) + '_' + str(
                    c_bess) + '.xlsx successfully written')
        except:
            raise TypeError(
                'Can not write output_' + str(PUN_value * 1000) + '_' + str(potenza) + '_' + str(
                    c_bess) + '.xlsx close the file and retry.')

        print(f'Analyzing PV: {potenza}kWp, BESS: {c_bess}kWh')

        AUC_annuale['PV'] = potenza
        AUC_annuale['BESS'] = c_bess
        AUC_annuale['PUN'] = PUN_value
        df_annuali = pd.concat([df_annuali, AUC_annuale])

try:
    file = Path(
        output_directory + 'risultati_annuali.xlsx')
    if file.exists():
        print("The file already exist. Deleting the old one...")
        os.remove(file)
    with pd.ExcelWriter(
            output_directory + 'risultati_annuali.xlsx') as writer:
        df_annuali.to_excel(writer, sheet_name='Annual Results', index=False)
        print('File risultati_annuali.xlsx successfully writen')
    with pd.ExcelWriter(
            output_directory + 'ElencoSimSensitivita.xlsx') as writer:
        ElencoSimEconomiche.to_excel(writer, sheet_name='ElencoSimulazioni', index=False)
        print('File ElencoSimSensitivita.xlsx successfully written')
except:
    raise TypeError('Can not write file risultati_annuali.xlsx, close it and retry')