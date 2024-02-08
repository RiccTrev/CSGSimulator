#Dizionario contenente i costi che vengono usati per la simulazione economica
parametri_economici = {
    'PV': 1100, # €/kWp
    'BESS': 1000, # €/kWh
    'Infrastruttura': 100, # €/kWx
    'Manodopera': 300, # €/kWp
    'Gestione': 10, # €/kWx
    'Assicurazione': 0.005, # Come percentuale sul CAPEX
    'TassoSconto': 0.06, # %
    'CoeffRiduzionePrestazioni': 0.01, #% riduzione annua entrate attribuibile a riduzione prestazioni PV
    'TAEG': 0.06
}

incentivi = {
    'RestituzioneComponentiTariffarie': 0.009, # €/MWh
    'IncentivoAUC': 0.100, # €/MWh
    'IncentivoCER': 0.110 # €/MWh
}



#Struttura dei nuovi incentivi MASE:
#incentiviT1 per impianti di potenza inferiore a 200kWp
#incentiviT2 per impianti di potenza compresa fra 200 e 600 kWp
#incentiviT3 per impianti di potenza superiore a 600kWp
incentiviT1 = {
    'fissa': 0.080,
    'massimo': 0.120
}
incentiviT2 = {
    'fissa': 0.070,
    'massimo': 0.110
}
incentiviT3 = {
    'fissa': 0.060,
    'massimo': 0.100
}

componenti_bolletta = {
    'trasporto_e_gestione': 0.08,  # (%) I costi di trasporto e gestione sono l'8% della bolletta totale
    'imposte': 0.1  # (%) Le imposte sono il 10% della bolletta
}
componenti_bolletta['materia_energia'] = 1 - componenti_bolletta['imposte'] - componenti_bolletta['trasporto_e_gestione']  # (%) di incidenza della materia energia sulla bolletta

