__author__ = "Riccardo Trevisan - University of Cagliari"
__version__ = "1.0.0"
__description__ = "This is a tool for the techno-economic simulation of CSGs (collective self consumtpion groups) according to the italian legislation."
__status__ = "validated"
__date__ = "5/01/2024"
__credits__ = "Riccardo Trevisan, University of Cagliari"
__license__ = "CC BY-NC-SA 4.0"
__python_version__ = "3.12.1"


def main(args):
    # Load parameters from file
    Lat = parametri.Lat
    Lon = parametri.Lon
    perdite = parametri.perdite
    # Open files
    cwd = os.getcwd()
    input_directory = cwd + "/Input/"
    output_directory = cwd + "/Output/"
    if not os.path.exists(output_directory):
        os.mkdir(output_directory)

    # Import PUN in Dataframe
    try:
        fn = input_directory + 'PUN.xlsx'
        xl = pd.ExcelFile(fn)
        # Create a dictionary of dfs
        dfs = {sh: xl.parse(sh, header=0) for sh in xl.sheet_names}
        df_prezzi = dfs['Prezzi-Prices']
    except:
        raise TypeError('Could not open file PUN.')

    # Import the load profiles of the Utilities.
    try:
        fn = input_directory + 'Carichi_utenze_AUC.xlsx'
        xl = pd.ExcelFile(fn)
        membri = {sh: xl.parse(sh, header=0) for sh in xl.sheet_names}
    except:
        raise TypeError('Could not open "Carich_utenze_AUC"')

    # I create month, day, hour columns for each dataframe. I need it to merge with the production data.
    for membro in membri.keys():
        membri[membro]['Month'] = membri[membro]['DataOra'].dt.month
        membri[membro]['Day'] = membri[membro]['DataOra'].dt.day
        membri[membro]['Hour'] = membri[membro]['DataOra'].dt.hour
        membri[membro]['DayOfWeek'] = membri[membro]['DataOra'].dt.dayofweek

    # Configuration user list
    list_utenti = list(membri.keys())
    print(f'Evaluating users: {list_utenti}')

    df_annuali = pd.DataFrame()
    # Power pairs pv-bess
    PUN_list = parametri.PUN_list
    listaPV = parametri.listaPV
    listaBESS = parametri.listaBESS 
    list_dimensionamenti = list(itertools.product(listaPV, listaBESS))
    print(f'Evaluating {len(list_dimensionamenti)} combinations.\nTotal number of scenarios: {len(list_dimensionamenti)*len(PUN_list)}')

    ElencoSimEconomiche = pd.DataFrame()
    # Simulate all the sizing sepecified with the PUN specified in the file.
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
            # Instantiate the DateTime column
            membri['AUC']['DataOra'] = np.array(membri[list_utenti[0]]['DataOra'])
            membri['AUC']['Month'] = membri['AUC']['DataOra'].dt.month
            membri['AUC']['Day'] = membri['AUC']['DataOra'].dt.day
            membri['AUC']['Hour'] = membri['AUC']['DataOra'].dt.hour
            membri['AUC']['Consumption'] = 0
            functions.SimulaAUC(potenza, c_bess, list_utenti, df_prezzi, membri, Lat, Lon, perdite, parametri.incentivi['IncentivoAUC'],
                                parametri.incentivi['RestituzioneComponentiTariffarie'], PUN_value)

            # Monthly and annual df creation.
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

            # Writing to output
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

def parse_args(args):
    """
    Args:
      args ([str]): Lista di stringhe che rappresentano i parametri della riga di comando. Questi possono includere:
        --version: Mostra la versione corrente del programma e termina.
        --author: Stampa il nome dell'autore del programma e termina.
        --status: Mostra lo status corrente del programma e termina.
        --last_release: Visualizza la data dell'ultima release del programma e termina.
        --description: Fornisce una descrizione del programma e termina.
        --credits: Mostra i crediti del programma e termina.
        -f, --file: Percorso obbligatorio del file JSON da analizzare per l'esecuzione del simulatore.

    Returns:
      :obj:`argparse.Namespace`: Namespace contenente i risultati dell'analisi. Il programma elabora questi dati e restituisce un risultato sotto forma di JSON.
    """
    parser = argparse.ArgumentParser(description="Collective self consumption groups simulator")
    parser.add_argument(
      "--version",
      action="version",
      version="V{ver}".format(ver=__version__),
      help = "Show version")
    parser.add_argument(
      "--license",
      action="store_true",
      help="Show license")
    parser.add_argument(
      "--python_version",
      action="store_true",
      help="Show python version")
    parser.add_argument(
      "--author",
      action="store_true",
      help="Show author")
    parser.add_argument(
      "--status",
      action="store_true",
      help="Show status")
    parser.add_argument(
      "--last_release",
      action="store_true",
      help="Show date of last release")
    parser.add_argument(
      "--description",
      action="store_true",
      help="Show description of program")
    parser.add_argument(
      "--credits",
      action="store_true",
      help="Show credits")
    parser.add_argument(
        "-f", "--file",
        type=str,
        required=False,
        help="Files must be placed inside Input folder. See README.md for more information.")


    return parser.parse_args(args)


if __name__ == "__main__":
    import argparse
    import logging
    import sys
    import json
    from datetime import datetime
    import pandas as pd
    import numpy as np
    import itertools
    import functions
    import parametri
    import os
    from pathlib import Path


    logging.basicConfig(level=logging.INFO)
    args = parse_args(sys.argv[1:])
    if args.author:
      print("Author: {autore}".format(autore=__author__))
      sys.exit()
    if args.status:
      print("Status: {status}".format(status=__status__))
      sys.exit()
    if args.last_release:
      print("Last release: {rilascio}".format(rilascio=__date__))
      sys.exit()
    if args.description:
      print("{description}".format(description=__description__))
      sys.exit()
    if args.credits:
      print("{credits}".format(credits=__credits__))
      sys.exit()
    if args.license:
      print("{license}".format(credits=__credits__))
      sys.exit()
    if args.license:
      print("{python_version}".format(credits=__credits__))
      sys.exit()

    # Chiamata a main con i dati JSON
    main(args)