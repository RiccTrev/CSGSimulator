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

# import astral
# from astral import LocationInfo
# from astral.sun import sun

########################################################################################################################
#                                       FUNZIONI USATE DA "Dimensionatore.py"                                          #
########################################################################################################################

# Converte numero a sigla mese e vice-versa
import parametri


def ConvertMonth(month):
    if isinstance(month, int):
        mesi = {
            1: 'gen',
            2: 'feb',
            3: 'mar',
            4: 'apr',
            5: 'mag',
            6: 'giu',
            7: 'lug',
            8: 'ago',
            9: 'set',
            10: 'ott',
            11: 'nov',
            12: 'dic'}
        return mesi[month]
    elif isinstance(month, str):
        mesi = {
            'gen': 1,
            'feb': 2,
            'mar': 3,
            'apr': 4,
            'mag': 5,
            'giu': 6,
            'lug': 7,
            'ago': 8,
            'set': 9,
            'ott': 10,
            'nov': 11,
            'dic': 12}
        return mesi[month]


def AssociaFasce(list, m):
    # Month serve per ripartire su F2 ed F3 i festivi
    F1 = []
    F2 = []
    F3 = []
    for i in range(len(list)):
        if (i >= 0) and (i < 7):
            F1.append(0)
            F2.append(0)
            F3.append(list[i])
        elif ((i >= 7) and (i < 8)) or ((i >= 19) and (i < 23)):
            F1.append(0)
            F2.append(list[i])
            F3.append(0)
        elif i == 23:
            F1.append(0)
            F2.append(0)
            F3.append(list[i])
        elif (i >= 8) and (i < 19):
            F1.append(list[i])
            F2.append(0)
            F3.append(0)
        else:
            raise TypeError('Attenzione, impossibile associare fascia, interrompo esecuzione')
    # Determino i giorni festivi e prefestivi nel mese per ripartire su F2 ed F3. I festivi sono tutti in F3, i prefestivi sono 2/3 in F2 ed 1/3 in F3
    y = datetime.datetime.now().year
    prefestivi = sum(1 for d in range(0, monthrange(y, m)[1]) if weekday(y, m, d + 1) == 5)
    festivi = sum(1 for d in range(0, monthrange(y, m)[1]) if weekday(y, m, d + 1) == 6)
    festivita = [datetime.date(y, 1, 1),  # primo dell'anno
                 datetime.date(y, 1, 6),  # epifania
                 easter(y),  # pasqua
                 easter(y) + timedelta(days=1),  # pasquetta
                 datetime.date(y, 4, 25),  # anniversario della liberazione
                 datetime.date(y, 5, 1),  # Festa del lavoro
                 datetime.date(y, 6, 2),  # Fondazione della Repubblica
                 datetime.date(y, 8, 15),  # Assunzione della beata vergine
                 datetime.date(y, 11, 1),  # Ognisanti
                 datetime.date(y, 12, 8),  # Immacolata concezione
                 datetime.date(y, 12, 25),  # Natale
                 datetime.date(y, 12, 26)]  # S. Stefano

    for i in range(0, len(festivita)):
        if festivita[i].month == m:
            if weekday(festivita[i].year, m, festivita[
                i].day) == 5:  # Se la festività è di sabato => tolgo un giorno ai sabati e lo metto in festivita
                prefestivi = prefestivi - 1
                festivi = festivi + 1
            elif weekday(festivita[i].year, m, festivita[i].day) == 6:  # se la festività è di domenica => non cambia
                prefestivi = prefestivi
                festivi = festivi
            else:  # Se non è ne sabato, ne domenica
                prefestivi = prefestivi
                festivi = festivi + 1

    # Percentuale di giorni in F2 ed in F3
    perc_F2 = 2 / 3 * (prefestivi / monthrange(y, m)[1])
    perc_F3 = 1 / 3 * (festivi / monthrange(y, m)[1])
    # Converto in np array per facilità di operazioni
    F1 = np.array(F1)
    F2 = np.array(F2)
    F3 = np.array(F3)
    # Ripartisco su numero totale giorni
    F1 = F1 * monthrange(y, m)[1]
    F2 = F2 + F1 * perc_F2
    F3 = F3 + F1 * perc_F3
    F1 = F1 - F2 - F3
    # Converto nuovamente a lista
    F1 = F1.tolist()
    F2 = F2.tolist()
    F3 = F3.tolist()

    return pd.DataFrame({'Produzione F1': F1, 'Produzione F2': F2, 'Produzione F3': F3})


def CalcolaAutoconsumoEdImmissione(df):
    df['Autoconsumo'] = np.minimum(df['P'], df['Consumption'])
    df['Immissione'] = np.array(df['P']) - np.array(df['Autoconsumo'])
    return df


def CalcolaAutoconsumoFasce(df):
    if df['Potenza Da Installare'] == 0:  # Se non c'è nuova capacità installata => Autoconsumo = 0.
        df['Autoconsumo F1'] = 0
        df['Autoconsumo F2'] = 0
        df['Autoconsumo F3'] = 0
        return df
    elif (df['Immissione F1'] > 0 or df['Immissione F2'] > 0 or df['Immissione F3'] > 0) and df[
        'Potenza Da Installare'] != 0:  # Se immette ed installa anche nuova capacità non possiamo stimare l'autoconsumo.
        df[
            'Autoconsumo F1'] = 0  # min(df['Fascia 1'], df['Produzione F1']) #df[['Fascia 1','Produzione F1']].min(axis=1)
        df[
            'Autoconsumo F2'] = 0  # min(df['Fascia 2'], df['Produzione F2']) #df[['Fascia 2','Produzione F2']].min(axis=1)
        df[
            'Autoconsumo F3'] = 0  # min(df['Fascia 3'], df['Produzione F3']) #df[['Fascia 3','Produzione F3']].min(axis=1)
        return df
    else:  # Se installa nuova capacità
        df['Autoconsumo F1'] = min(df['Fascia 1'], df['Produzione F1'])  # df[['Fascia 1','Produzione F1']].min(axis=1)
        df['Autoconsumo F2'] = min(df['Fascia 2'], df['Produzione F2'])  # df[['Fascia 2','Produzione F2']].min(axis=1)
        df['Autoconsumo F3'] = min(df['Fascia 3'], df['Produzione F3'])  # df[['Fascia 3','Produzione F3']].min(axis=1)


def CalcolaImmissioneFasce(df):
    # Aggiorno l'immissione tenendo conto della nuova capacità installata
    df['Immissione F1'] = df['Immissione F1'] + df['Produzione F1'] - df['Autoconsumo F1']
    df['Immissione F2'] = df['Immissione F2'] + df['Produzione F2'] - df['Autoconsumo F2']
    df['Immissione F3'] = df['Immissione F3'] + df['Produzione F3'] - df['Autoconsumo F3']
    return df


def OttieniProduzioneOraria(Lat, Lon, Month, Slope=35, Azimut=0):
    response = requests.get("https://re.jrc.ec.europa.eu/api/v5_2/DRcalc?"
                            "lat=" + str(Lat) +
                            "&lon=" + str(Lon) +
                            "&raddatabase=PVGIS-SARAH2"
                            "&usehorizon=1"
                            "&angle=" + str(Slope) +
                            "&azimut=" + str(Azimut) +
                            "&month=" + str(Month) +
                            "&global=1"
                            "&localtime=1"
                            "&outputformat=json")
    todos = json.loads(response.text)
    length = len(todos['outputs']['daily_profile'])
    my_list = []
    for i in range(length):
        my_list.append(todos['outputs']['daily_profile'][i]['G(i)'])
    return my_list


def StimaProduzioneOrariaPerFasce(Lat, Lon, Month, PotenzaImpianto=0, SuperficieDisponibile=0, PotenzaModulo=250,
                                  AreaModulo=1.65, Perdite=0.16, Slope=35, Azimut=0):
    # I valori impostati di default sono in condizioni standard.
    # Per ogni fascia oraria calcolo l'energia prodotta dall'impianto E = AreaImpianto * rendimento * Irraggiamento nell'ora * Perdite
    # Il rendimento è calcolato a condizioni standard (1000W/m2, temperatura cella: 25 gradi, vento 1 m/s) come: (PotenzaModulo/AreaModulo/1000)*100
    Rendimento = (PotenzaModulo / AreaModulo / 1000)
    if PotenzaImpianto == 0 and SuperficieDisponibile == 0:
        Produzione = [0] * 24
        PotenzaInstallabile = [0] * 24
        SuperficieImpianto = [0] * 24
        # print('Non viene installato alcun impianto')
        df_produzione_oraria = pd.DataFrame()
        df_produzione_oraria['Produzione F1'] = [0] * 24
        df_produzione_oraria['Produzione F2'] = [0] * 24
        df_produzione_oraria['Produzione F3'] = [0] * 24
        df_produzione_oraria['Potenza Installabile'] = [0] * 24
        df_produzione_oraria['Superficie Necessaria'] = [0] * 24
        df_produzione_oraria['Periodo'] = [ConvertMonth(Month)] * 24
        return df_produzione_oraria
    else:
        # Ottengo i dati d'irraggiamento da PV GIS per la lat e la lon per la giornata tipo del mese
        # Due modalità di calcolo della produzione:
        # 1) Se viene fornita la potenza da installare
        # 2) Se viene fornita la potenza dell'impianto => Devo calcolare la potenza installabile
        # print(f'Dettagli tecnici impianto:\nPotenza Singolo Modulo: {PotenzaModulo}W\n'
        #      f'Potenza Specificata: {PotenzaImpianto}W\n'
        #      f'Superficie Specificata: {SuperficieDisponibile}m2\n'
        #      f'Area Unitaria Modulo: {AreaModulo}m2\n'
        #      f'Rendimento: {Rendimento*100:.2f}%\n'
        #      f'Perdite: {Perdite*100:.2f}%\n'
        #      f'Slope: {Slope} gradi\n'
        #      f'Azimut: {Azimut} gradi')
        if PotenzaImpianto != 0:
            PotenzaInstallabile = 0
            # Determino il numero di moduli necessario per calcolare la superficie necessaria
            NumeroModuli = PotenzaImpianto / PotenzaModulo
            SuperficieImpianto = AreaModulo * NumeroModuli
            Produzione = OttieniProduzioneOraria(Lat, Lon,
                                                 Month)  # Altri parametri che possono essere passati: Slope (default 35), Azimut (default 0)
            # Per ogni valore orario calcolo l'energia prodotta
            for i in range(len(Produzione)):
                Produzione[i] = (Produzione[i] * SuperficieImpianto * Rendimento * (
                        1 - Perdite)) / 1000  # L'ultimo termine è il numero di giorni nel mese dell'anno corrente * monthrange(datetime.datetime.now().year, Month)[1]
            # print(f'Superficie necessaria per la potenza specificata: {SuperficieImpianto:.2f}m2')
            # print(f'Numero di moduli necessari: {NumeroModuli}')
        elif SuperficieDisponibile != 0:  # Se viene specificata una superficie disponibile
            SuperficieImpianto = 0
            # Determino la potenza installabile, non mi serve per calcolare la produzione, ma la calcolo lo stesso!
            NumeroModuli = math.floor(SuperficieDisponibile / AreaModulo)
            PotenzaInstallabile = NumeroModuli * PotenzaModulo
            Produzione = OttieniProduzioneOraria(Lat, Lon, Month)
            for i in range(len(Produzione)):
                Produzione[i] = (Produzione[i] * SuperficieDisponibile * Rendimento * (
                        1 - Perdite)) / 1000  # L'ultimo termine è il numero di giorni nel mese dell'anno corrente * monthrange(datetime.datetime.now().year, Month)[1]
            # print(f'Potenza massima installabile per la superficie specificata: {PotenzaInstallabile:.2f}W')
            # print(f'Numero di moduli necessari: {NumeroModuli}')
        df_produzione_oraria = AssociaFasce(Produzione,
                                            Month)  # Gli passo anche month perché ripartisco su F2 ed F3 in base ai giorni festivi nel mese
        # Creo colonne potenza Installabile e superficie necessaria
        df_produzione_oraria['Potenza Installabile'] = [PotenzaInstallabile] * len(df_produzione_oraria.index)
        df_produzione_oraria['Superficie Necessaria'] = [SuperficieImpianto] * len(df_produzione_oraria.index)
        df_produzione_oraria['Periodo'] = [ConvertMonth(Month)] * len(df_produzione_oraria.index)
        # display(df_produzione_oraria)
        return df_produzione_oraria


def CalcolaProducibilita(Lat, Lon, Perdite=0.16):
    # Ritorna kWh/kWp per lat, lon e perdite specificate.
    Power = 1  # Potenza installata così mi torna il valore di kWh prodotti da 1 kWp installato
    response = requests.get("https://re.jrc.ec.europa.eu/api/v5_2/PVcalc?"
                            "lat=" + str(Lat) +
                            "&lon=" + str(Lon) +
                            "&peakpower=" + str(Power) +
                            "&loss=" + str(Perdite * 100) +
                            "&optimalinclination=1" +
                            "&optimalangles=1" +
                            "&inclined_optimum=1" +
                            "&vertical_optimum=1" +
                            "&vertical_optimum=1" +
                            "&outputformat=json")
    todos = json.loads(response.text)
    json_formatted_str = json.dumps(todos, indent=2)
    print(f"Producibilità: {todos['outputs']['totals']['fixed']['E_y']} kWh/kWp")
    return todos['outputs']['totals']['fixed']['E_y']


def StimaProduzioneMensile(df, Perdite=0.16):
    mesi = {
        0: 'gen',
        1: 'feb',
        2: 'mar',
        3: 'apr',
        4: 'mag',
        5: 'giu',
        6: 'lug',
        7: 'ago',
        8: 'set',
        9: 'ott',
        10: 'nov',
        11: 'dic'}
    # output = pd.DataFrame(columns = ['Identificativo', 'Lat', 'Lon', 'Periodo', 'Produzione'])
    my_list = []
    old_id = str(0)
    for index, row in df.iterrows():
        if row['Potenza Da Installare'] == 0:
            continue
        if old_id == row['Identificativo']:
            continue
        else:
            old_id = row['Identificativo']
        response = requests.get("https://re.jrc.ec.europa.eu/api/v5_1/PVcalc?lat=" + str(row['Lat']) + "&lon=" + str(
            row['Lon']) + "&raddatabase=PVGIS-SARAH&peakpower=" + str(
            row['Potenza Da Installare']) + "&pvtechchoice=crystSi&loss=" + str(
            Perdite * 100) + "&optimalinclination=1&vertical_optimum=1&outputformat=json")
        todos = json.loads(response.text)
        for i in range(0, 12):
            new_row = []
            new_row = [row['Identificativo'], row['Lat'], row['Lon'], mesi[i],
                       todos['outputs']['monthly']['fixed'][i]['E_m']]
            my_list.append(new_row)
    output = pd.DataFrame(my_list, columns=['Identificativo', 'Lat', 'Lon', 'Periodo', 'Produzione'])
    return output


def ModificaTimezone(date, FromZone, ToZone):
    from_zone = tz.gettz(FromZone)  # UTC
    to_zone = tz.gettz(ToZone)  # Europe/Rome
    # utc = datetime.utcnow()
    # Forza un stringa di date = datetime.strptime(date, '%I:%M:%S %p')
    # Tell the datetime object that it's in UTC time zone since
    # datetime objects are 'naive' by default
    date = date.replace(tzinfo=from_zone)
    # Convert time zone
    to_date = date.astimezone(to_zone)
    return to_date


# Ottengo le ore di sole per il 15 di ogni mese. N.B. Ritorna dati in UTC TIME, sono da portare avanti di un'ora!!!
def SunsetSunrise(lat, lon, month):
    city = LocationInfo("Roma", "Italy", "Europe/London", lat, lon)
    # print((
    # f"Information for {city.name}/{city.region}\n"
    # f"Timezone: {city.timezone}\n"
    # f"Latitude: {city.latitude:.02f}; Longitude: {city.longitude:.02f}\n"))
    s = sun(city.observer, date=datetime.date(datetime.datetime.now().year, month, 12))
    Alba = ModificaTimezone(s["sunrise"], "UTC", "Europe/Rome")
    Tramonto = ModificaTimezone(s["sunset"], "UTC", "Europe/Rome")  # .strftime("%H:%M")
    # print((
    #    #f'Tutto: {s}\n'
    #    f'Prime luci dell\'Alba: {ModificaTimezone(s["dawn"], "UTC", "Europe/Rome").strftime("%H:%M")}\n'
    #    f'Alba: {ModificaTimezone(s["sunrise"], "UTC", "Europe/Rome").strftime("%H:%M")}\n'
    #    f'Mezzogiorno: {ModificaTimezone(s["noon"], "UTC", "Europe/Rome").strftime("%H:%M")}\n'
    #    f'Tramonto: {ModificaTimezone(s["sunset"], "UTC", "Europe/Rome").strftime("%H:%M")}\n'
    #    f'Crepuscolo: {ModificaTimezone(s["dusk"], "UTC", "Europe/Rome").strftime("%H:%M")}\n'
    #    f'Ore di luce utili: {round((s["sunset"] - s["sunrise"]).days * 24 + (s["sunset"] - s["sunrise"]).seconds // 3600)}' #:{((s["sunset"] - s["sunrise"]).seconds % 3600) // 60}\n'
    # ))
    return Alba, Tramonto


def OreLuceInFasce(Alba, Tramonto):
    OreLuce = [Tramonto - Alba for Tramonto, Alba in zip(Tramonto, Alba)]
    OreLuce2 = [element.seconds // 3600 for element in OreLuce]
    # print(OreLuce2)
    F1 = []
    F2 = []
    F3 = []
    for i in range(len(Alba)):
        if Alba[i].hour <= 7:
            F3_i = 7 - Alba[i].hour
            F2_i = 1
            if Tramonto[i].hour <= 19:
                F1_i = Tramonto[i].hour - 8
            else:
                F1_i = 11
                F2_i = F2_i + (Tramonto[i].hour - 19)
        F1.append(F1_i)
        F2.append(F2_i)
        F3.append(F3_i)
    mesi = ['gen', 'feb', 'mar', 'apr', 'mag', 'giu', 'lug', 'ago', 'set', 'ott', 'nov', 'dic']
    df_OreLuce = pd.DataFrame({'Periodo': mesi, 'Ore Luce F1': F1, 'Ore Luce F2': F2, 'Ore Luce F3': F3},
                              columns=['Periodo', 'Ore Luce F1', 'Ore Luce F2', 'Ore Luce F3'])
    return df_OreLuce


########################################################################################################################
#                                       FUNZIONI USATE DA "Script_AUC_V2.py"                                           #
########################################################################################################################
def CalcolaProduzionePV(Lat, Lon, Potenza, Perdite):
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
    # json_formatted_str = json.dumps(todos['outputs']['hourly'], indent=2)
    # print(json_formatted_str)
    my_list = []
    # length = len(todos['outputs']['daily_profile'])
    # my_list = []
    # for i in range(length):
    #    my_list.append(todos['outputs']['daily_profile'][i]['G(i)'])
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
    # kwargs mi serve per passare PUN_value quando faccio la simulazione con PUN medio
    # Imposto df_PUN che mi serve per fare il merge e il calcolo spesa energia/vendita energia
    df_PUN = df_prezzi[['DataOra', 'PUN']].copy()  # Lavoro su copia dell'originale. Non modifica originale e sopprime errore SettingWithCopyWarning
    df_PUN['DataOra'] = pd.to_datetime(df_PUN['DataOra'])
    # df_PUN.loc[df_PUN.DataOra] = pd.to_datetime(df_PUN['DataOra'])

    if PUN_value != -1:
        print('Imposto nuovo valore PUN')
        df_PUN['PUN'] = PUN_value
    print(f'VALORE PUN: {df_PUN["PUN"].mean()}')
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
                    FlussiScontati[a] = RicaviAUC_Anno1 / pow((1 + TassoSconto), a)
                    FlussiNonScontati[a] = RicaviAUC_Anno1
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
            RicaviAUC[p] = RicaviAUC_Anno1
            CostiPrima = CostiEnergia + RisparmioDaAutoconsumo
            VariazioneCostiAUC[p] = ((EsborsoNettoAUC - CostiPrima) / CostiPrima)
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
                    FlussiScontati[a] = RicaviESCO_Anno1 / pow((1 + TassoSconto), a)
                    FlussiNonScontati[a] = RicaviESCO_Anno1
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
            RicaviESCO[p] = RicaviESCO_Anno1
            RicaviAUC[p] = RicaviAUC_Anno1
            CostiPrima = CostiEnergia + RisparmioDaAutoconsumo
            VariazioneCostiAUC[p] = ((EsborsoNettoAUC - CostiPrima) / CostiPrima)
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


########################################################################################################################
#                                       FUNZIONI USATE DA "Script_istanzia_CER.py"                                     #
########################################################################################################################

def SimulaUtenteCER(Consumption, Production, BESS_capacity, Initial_SOC, PUN):
    battery_energy = np.zeros_like(Consumption, dtype=float)
    battery_energy[0] = Initial_SOC
    grid_energy = np.zeros_like(Consumption, dtype=float)
    self_consumption = np.zeros_like(Consumption, dtype=float)
    # Calculate energy usage and storage for each time period
    for t in range(len(Consumption)):
        # Calculate energy available from PV production and battery storage
        if t == 0:
            energy_available = Production[t] + Initial_SOC
        else:
            energy_available = Production[t] + battery_energy[t - 1]
        # Calculate energy used to satisfy demand
        if energy_available >= Consumption[t]:
            # PV and/or battery energy can satisfy demand
            self_consumption[t] += Consumption[t]  # demand_satisfied[t] - grid_energy[t]
            if Consumption[t] > Production[t]:
                # need to take energy from battery
                if t == 0:
                    battery_energy[t] = battery_energy[t] - (Consumption[t] - Production[t])
                else:
                    battery_energy[t] = battery_energy[t - 1] - (Consumption[t] - Production[t])
            # Consumption is less than the PV production
            elif Consumption[t] <= Production[t]:
                # Store surplus PV energy in the battery
                if t == 0:
                    battery_energy[t] = min(battery_energy[0] + (Production[t] - Consumption[t]),
                                            BESS_capacity)
                else:
                    battery_energy[t] = min(battery_energy[t - 1] + (Production[t] - Consumption[t]),
                                            BESS_capacity)
                grid_energy[t] = Production[t] - Consumption[t] - (
                        battery_energy[t] - battery_energy[t - 1])  # injection in grid is positive
            elif Consumption[t] == Production[t]:
                if t == 0:
                    battery_energy[t] = BESS_capacity
                else:
                    battery_energy[t] = battery_energy[t - 1]
                grid_energy[t] = 0
        elif energy_available < Consumption[t]:  # if PV and/or battery energy cant satisfy demand
            # Not enough PV or battery energy to satisfy demand, use grid energy
            self_consumption[t] += energy_available
            battery_energy[t] = 0
            grid_energy[t] = -(Consumption[t] - energy_available)  # witdhrawals from grid are negative
    tot_sc = np.sum(self_consumption)
    consumption = tot_sc + (- np.sum(grid_energy[
                                         grid_energy <= 0]))  # Consumption is only when i withdraw from network. Terms are negative and need to be summed.

    user_parameters = {}
    calculate_withdrawal = np.vectorize(
        lambda x: -x if x < 0 else 0)  # the negative terms in grid energy are withdrawals from grid
    calculate_injection = np.vectorize(
        lambda x: x if x > 0 else 0)  # the positive terms in grid energy are injection in grid
    withdrawal = -np.minimum(grid_energy, 0)
    injection = np.maximum(grid_energy, 0)

    # print(f'GridEnergy: {grid_energy[:24]}')
    # print(f'Immissione: {injection[:24]}')
    # print(f'Prelievo: {withdrawal[:24]}')
    # print(f'Autoconsumo {self_consumption[:24]}')

    user_parameters["GridEnergy"] = grid_energy
    user_parameters["Autoconsumo"] = self_consumption
    user_parameters["Immissione"] = injection
    user_parameters["Prelievo"] = withdrawal
    user_parameters["SOC"] = battery_energy

    # Per l'utente voglio calcolare anche i seguenti: MateriaEnergia
    CalcolaCostiERisparmiUtente(user_parameters, PUN)
    return pd.DataFrame(user_parameters)

#Calcola i costi sostenuti dall'utente (componenti della bolletta) ed i risparmi per l'utente da autoconsumo e vendita dell'energia in rete
def CalcolaCostiERisparmiUtente(user_parameters, PUN):
    trasporto_e_gestione = parametri.componenti_bolletta[
        'trasporto_e_gestione']  # (%) I costi di trasporto e gestione sono l'8% della bolletta totale
    imposte = parametri.componenti_bolletta['imposte']  # (%) Le imposte sono il 10% della bolletta
    materia_energia = parametri.componenti_bolletta['materia_energia']

    user_parameters['MateriaEnergia'] = user_parameters['Prelievo'] * PUN
    user_parameters['TrasportoEGestione'] = user_parameters['MateriaEnergia'] * (trasporto_e_gestione / materia_energia)
    user_parameters['Imposte'] = user_parameters['MateriaEnergia'] * (imposte / materia_energia)
    user_parameters['CostoBolletta'] = user_parameters['MateriaEnergia'] + user_parameters['TrasportoEGestione'] + \
                                       user_parameters['Imposte']

    user_parameters['RID'] = user_parameters['Immissione'] * PUN
    user_parameters['RisparmioDaAutoconsumo'] = (user_parameters['Autoconsumo'] * PUN) * (
            1 + (trasporto_e_gestione / materia_energia) + (imposte / materia_energia))
    return

def SimEconomicaCER(df, CostoPV, CostoBESS, CostoInfrastruttura, CostoManodopera, CostoUnitarioGestione,
                 PercentualeAssicurazione, TassoSconto, CoefficienteRiduzione, PotenzaPV, CapacitaBESS):
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
    percentuali = np.arange(0, 1.05, 0.05)
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

    for p in range(len(percentuali)):
        FlussiScontati = np.zeros(orizzonte_temporale)
        FlussiNonScontati = np.zeros(orizzonte_temporale)
        FlussiCumulati = np.zeros(orizzonte_temporale)
        if percentuali[p] == 0: #Se la CER investe (solo caso p = 0)
            for a in range(orizzonte_temporale):
                RicaviESCO_Anno1 = 0
                RicaviAUC_Anno1 = RicaviRID + RicaviEnergiaCondivisa + RisparmioDaAutoconsumo
                if a == 0:
                    FlussiScontati[a] = -CAPEX
                    FlussiNonScontati[a] = -CAPEX
                    FlussiCumulati[a] = -CAPEX
                elif a == 1:
                    FlussiScontati[a] = RicaviAUC_Anno1 / pow((1 + TassoSconto), a)
                    FlussiNonScontati[a] = RicaviAUC_Anno1
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
            RicaviESCO[p] = RicaviESCO_Anno1
            RicaviAUC[p] = RicaviAUC_Anno1
            VariazioneCostiAUC[p] = ((EsborsoNettoAUC - CostiEnergia) / CostiEnergia)
            # print(f'Flussi scontati per p = {percentuali[p]}: {FlussiScontati}')
            NPV[p] = np.sum(FlussiScontati)
            TIR[p] = npf.irr(FlussiNonScontati)
            PI[p] = 1 + (NPV[p] / CAPEX)
        else: #Se c'è una esco che investe
            for a in range(orizzonte_temporale):
                RicaviESCO_Anno1 = RicaviRID + percentuali[p] * RicaviEnergiaCondivisa
                RicaviAUC_Anno1 = (1 - percentuali[p]) * RicaviEnergiaCondivisa + RisparmioDaAutoconsumo
                if a == 0:
                    FlussiScontati[a] = -CAPEX
                    FlussiNonScontati[a] = -CAPEX
                    FlussiCumulati[a] = -CAPEX
                elif a == 1:
                    FlussiScontati[a] = RicaviESCO_Anno1 / pow((1 + TassoSconto), a)
                    FlussiNonScontati[a] = RicaviESCO_Anno1
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
            RicaviESCO[p] = RicaviESCO_Anno1
            RicaviAUC[p] = RicaviAUC_Anno1
            VariazioneCostiAUC[p] = ((EsborsoNettoAUC - CostiEnergia) / CostiEnergia)
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
#Calcola per la CER l'incentivo totale all'energia condivisa e


def CalcolaIncentiviMASE(x, pz, potenza_totale):
    if potenza_totale < 200: # potenza < 200
        return min(parametri.incentiviT1['fissa'] + min(max(0, 0.180-pz), 0.040), parametri.incentiviT1['massimo']) * x
    elif 200 <= potenza_totale < 600: # potenza >=200 & <600
        return min(parametri.incentiviT2['fissa'] + min(max(0, 0.180 - pz), 0.040), parametri.incentiviT2['massimo']) * x
    elif potenza_totale > 600:  # potenza >600
        return min(parametri.incentiviT3['fissa'] + min(max(0, 0.180 - pz), 0.040), parametri.incentiviT3['massimo']) * x