import pandas as pd
#pd.options.mode.chained_assignment = None
import numpy as np
import itertools
import functions
import parametri
import os
from pathlib import Path

input_directory = 'C:/Users/trevi/Dropbox/@Trevisan-Ghiani/WIP/Special Issue FES + EEEIC/Input Files/'
output_directory = 'C:/Users/trevi/Dropbox/@Trevisan-Ghiani/WIP/Special Issue FES + EEEIC/OutputSimulazioni/'
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
print(list_utenti)

# Li usa le API di PVGIS per il calcolo della produzione del PV
# Locallizzazione
Lat = 39.205
Lon = 9.130
# Perdite PV (%)
perdite = 16
# Potenza da installare presso l'AUC (kWp)
#potenza = 20
# Capacità BESS (kWh)
#c_bess = 5

df_annuali = pd.DataFrame()


# Struttura delle entrate
parametri.incentivi['RestituzioneComponentiTariffarie'] = 0.009  # (€/kWh) Alternativamente procedere al calcolo dettagliato come descritto sulle regole del GSE.
parametri.incentivi['IncentivoAUC'] = 0.100  # (€/kWh) E' l'parametri.incentivi['IncentivoAUC'] arera + mise dato agli AUC

# Coppie potenza pv-bess
PUN_list = [0.05, 0.100, 0.150]
listaPV = [5, 7.5, 10, 12.5, 15, 17.5, 20] #np.arange(1, 20, 1).tolist() 
listaBESS = [0, 5, 7.5, 10, 12.5, 15, 17.5, 20] #np.arange(0, 15, 1).tolist() 
list_dimensionamenti = list(itertools.product(listaPV, listaBESS))
print(f'Valuto {len(list_dimensionamenti)} combinazioni di dimensionamento.\nNumero di casi totali: {len(list_dimensionamenti)*len(PUN_list)}')

ElencoSimEconomiche = pd.DataFrame()
#Simulo tutti i dimensionamenti sepecificati con il PUN specificato nel file.
df_prezzi['PUN'] = df_prezzi['PUN'] / 1000
#for elements in list_dimensionamenti:
#    potenza = elements[0]
#    c_bess = elements[1]
#    print(f'Analizzo iterazione con PUN da file con potenza PV pari a {potenza}kWp e capacità bess pari a {c_bess}kWh')
#    membri['AUC'] = pd.DataFrame()
#    # Istanzio la colonna DataOra
#    membri['AUC']['DataOra'] = np.array(membri[list_utenti[0]]['DataOra'])
#    membri['AUC']['Month'] = membri['AUC']['DataOra'].dt.month
#    membri['AUC']['Day'] = membri['AUC']['DataOra'].dt.day
#    membri['AUC']['Hour'] = membri['AUC']['DataOra'].dt.hour
#    membri['AUC']['Consumption'] = 0
#    functions.SimulaAUC(potenza, c_bess, list_utenti, df_prezzi, membri, Lat, Lon, perdite, parametri.incentivi['IncentivoAUC'], parametri.incentivi['RestituzioneComponentiTariffarie'], PUN_value=-1)
#
#    # Creazione df mensili ed annuali
#    AUC_mensile = membri['AUC'].resample('M', on='DataOra').sum().drop(
#        columns=['Month', 'Day', 'Hour', 'PUN', 'SOC']).reset_index()
#    AUC_annuale = membri['AUC'].resample('Y', on='DataOra').sum().drop(
#        columns=['Month', 'Day', 'Hour', 'PUN', 'SOC']).reset_index()
#    SimEconomica = functions.SimEconomicaAUC(AUC_annuale, parametri.parametri_economici['PV'], parametri.parametri_economici['BESS'],
#                                          parametri.parametri_economici['Infrastruttura'], parametri.parametri_economici['Manodopera'],
#                                          parametri.parametri_economici['Gestione'], parametri.parametri_economici['Assicurazione'],
#                                          parametri.parametri_economici['TassoSconto'],
#                                          parametri.parametri_economici['CoeffRiduzionePrestazioni'], potenza, c_bess)
#    SimEconomica['RapportoCondivisaProduzione'] = AUC_annuale['Condivisa'][0] / AUC_annuale['P'][0]
#    SimEconomica['PUN'] = df_prezzi['PUN'].mean()
#    ElencoSimEconomiche = pd.concat([ElencoSimEconomiche, SimEconomica])
#
#    # Scrittura in output
#    try:
#        file = Path(
#            output_directory + 'output_PUN_File' + str(
#                potenza) + '_' + str(c_bess) + '.xlsx')
#        if file.exists():
#            print("Il file esiste già. Elimino quello vecchio.")
#            os.remove(file)
#        with pd.ExcelWriter(
#                output_directory + 'output_PUN_File' + str(
#                    potenza) + '_' + str(c_bess) + '.xlsx') as writer:
#            membri['AUC'].to_excel(writer, sheet_name='AUC', index=False)
#            AUC_mensile.to_excel(writer, sheet_name='AUC_mensile', index=False)
#            AUC_annuale.to_excel(writer, sheet_name='AUC_annuale', index=False)
#            SimEconomica.to_excel(writer, sheet_name='SimEconomica', index=False)
#            print('Scrittura del file output_PUN_File' + str(potenza) + '_' + str(
#                c_bess) + '.xlsx realizzata con successo')
#    except:
#        raise TypeError('Impossibile scrivere il file output_PUN_File' + str(potenza) + '_' + str(
#            c_bess) + '.xlsx verificare che non sia già aperto e riprovare.')
#
#    AUC_annuale['PV'] = potenza
#    AUC_annuale['BESS'] = c_bess
#    #AUC_annuale['PUN'] = PUN_value
#    df_annuali = pd.concat([df_annuali, AUC_annuale])
#
##Scrivo i df_annuali con tutti i risultati con PUN specificato in file.
#try:
#    file = Path(
#        output_directory + 'risultati_annuali_PUN_File.xlsx')
#    if file.exists():
#        print("Il file esiste già. Elimino quello vecchio.")
#        os.remove(file)
#    with pd.ExcelWriter(
#            output_directory + 'risultati_annuali_PUN_File.xlsx') as writer:
#        df_annuali.to_excel(writer, sheet_name='Annual Results', index=False)
#        print('Scrittura del file risultati_annuali.xlsx realizzata con successo')
#except:
#    raise TypeError('Impossibile scrivere il file risultati_annuali_PUN_File.xlsx, verificare che non sia già aperto e riprovare.')

###############################################
###############################################
df_annuali = pd.DataFrame() # Empty df_annuali
for PUN_value in PUN_list:
    for elements in list_dimensionamenti:
        potenza = elements[0]
        c_bess = elements[1]
        print(f'Analizzo iterazione con PUN medio {PUN_value}€/kWh, potenza PV pari a {potenza}kWp e capacità bess pari a {c_bess}kWh')
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
        AUC_mensile = membri['AUC'].resample('M', on='DataOra').sum().drop(
            columns=['Month', 'Day', 'Hour', 'PUN', 'SOC']).reset_index()
        AUC_annuale = membri['AUC'].resample('Y', on='DataOra').sum().drop(
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
                print("Il file esiste già. Elimino quello vecchio.")
                os.remove(file)
            with pd.ExcelWriter(
                    output_directory + 'output_' + str(
                        PUN_value * 1000) + '_' + str(
                        potenza) + '_' + str(c_bess) + '.xlsx') as writer:
                membri['AUC'].to_excel(writer, sheet_name='AUC', index=False)
                AUC_mensile.to_excel(writer, sheet_name='AUC_mensile', index=False)
                AUC_annuale.to_excel(writer, sheet_name='AUC_annuale', index=False)
                SimEconomica.to_excel(writer, sheet_name='SimEconomica', index=False)
                print('Scrittura del file output_' + str(PUN_value * 1000) + '_' + str(potenza) + '_' + str(
                    c_bess) + '.xlsx realizzata con successo')
        except:
            raise TypeError(
                'Impossibile scrivere il file output_' + str(PUN_value * 1000) + '_' + str(potenza) + '_' + str(
                    c_bess) + '.xlsx verificare che non sia già aperto e riprovare.')

        print(f'Analizzo iterazione con potenza PV pari a {potenza}kWp e capacità bess pari a {c_bess}kWh')

        AUC_annuale['PV'] = potenza
        AUC_annuale['BESS'] = c_bess
        AUC_annuale['PUN'] = PUN_value
        df_annuali = pd.concat([df_annuali, AUC_annuale])

try:
    file = Path(
        output_directory + 'risultati_annuali.xlsx')
    if file.exists():
        print("Il file esiste già. Elimino quello vecchio.")
        os.remove(file)
    with pd.ExcelWriter(
            output_directory + 'risultati_annuali.xlsx') as writer:
        df_annuali.to_excel(writer, sheet_name='Annual Results', index=False)
        print('Scrittura del file risultati_annuali.xlsx realizzata con successo')
    with pd.ExcelWriter(
            output_directory + 'ElencoSimSensitivita.xlsx') as writer:
        ElencoSimEconomiche.to_excel(writer, sheet_name='ElencoSimulazioni', index=False)
        print('Scrittura del file ElencoSimSensitivita.xlsx realizzata con successo')
except:
    raise TypeError('Impossibile scrivere il file risultati_annuali.xlsx, verificare che non sia già aperto e riprovare.')