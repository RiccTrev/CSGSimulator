#SET LOCATION
Lat = 39.205 #latitude
Lon = 9.130 #longitude

# SET LOSSES FOR THE PV (%)
perdite = 16

#SET DIMENSIONINGS TO BE EVALUATED
PUN_list = [0.05] #€/kWh
listaPV = [5, 7.5, 10] 
listaBESS = [0, 5] 

#Cost dictionary
parametri_economici = {
    'PV': 1100, # €/kWp
    'BESS': 1000, # €/kWh
    'Infrastruttura': 100, # €/kWx
    'Manodopera': 300, # €/kWp
    'Gestione': 10, # €/kWx
    'Assicurazione': 0.005, # As a percentage on CAPEX
    'TassoSconto': 0.06, # %
    'CoeffRiduzionePrestazioni': 0.01, # % annual revenue reduction attributable to reduction in PV benefits
    'TAEG': 0.06
}

#Incentive dictionary
incentivi = {
    'RestituzioneComponentiTariffarie': 0.009, # €/MWh
    'IncentivoAUC': 0.100, # €/MWh
    'IncentivoCER': 0.110 # €/MWh
}

#New incentive MASE:
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
    'trasporto_e_gestione': 0.08,  # (%) Transportation and management costs are 8% of the total bill
    'imposte': 0.1  # (%) Taxes are 10% of the bill
}
componenti_bolletta['materia_energia'] = 1 - componenti_bolletta['imposte'] - componenti_bolletta['trasporto_e_gestione']  # (%) Of incidence of energy matter on the bill

