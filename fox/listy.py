#!/usr/bin/env python
# -*- coding: utf8 -*-

u'''
import Lišty z FoxPro tabulky

http://www.connectionstrings.com/
natvrdo c:\ramovani\data - případně vyedituj
(zde nepoužito, ale:) chci-li na 64b. mašině vytvářet DSN, musím pustit Odbcad32.exe z %systemdrive%\Windows\SysWoW64, jinak nevidím 32b. ovladače
FoxPro ODBC driver: http://download.microsoft.com/download/vfoxodbcdriver/Install/6.1/W9XNT4/EN-US/VFPODBC.msi
'''

import pyodbc
from decimal import Decimal

def fox_table(folder, table): 
    cnxn = pyodbc.connect(r"Driver={{Microsoft Visual FoxPro Driver}};SourceType=DBF;SourceDB={0};Exclusive=No;Collate=Machine;NULL=NO;DELETED=NO;BACKGROUNDFETCH=NO;".format(folder), autocommit=True) 
        # r"Driver={{Microsoft...}};DefaultDir={0}".format(r'c:\ramovani\data') 
        # pyodbc.connect(r"Driver={Microsoft Paradox Driver (*.db )};DriverID=538;Fil=Paradox 5.X;DefaultDir=c:\ramovani\data;Dbq=c:\ramovani\data;CollatingSequence=ASCII;", autocommit=True)
    cursor = cnxn.cursor()
    cursor.execute("select * from %s" % table)
    rows=cursor.fetchall()
    for i, row in enumerate(rows):
        for j, fld in enumerate(row):
            if isinstance(fld, str):
                # fld = fld.strip() nelze! immutable - založí jiný objekt
                rows[i][j] = fld.strip()
    # cnxn.commit()
    cnxn.close()
    return rows

def import_listy_rp():
    listy_id = 5  # ==5: lišty [RP]
    fox_listy = fox_table(r"c:\ramovani\data\fox", "listy")
    db(db.typprace.cinnost_id==listy_id).delete()
    for fox_lista in fox_listy:
        # CISLO, TYP, FIRMA, TOVARNICIS, NAZEV, SIRKA, CENA, SKLADEM, CENANAKUP
        fx_vyrobce=(fox_lista[2] or '').decode('cp1250')
        fx_tovarni=(fox_lista[3] or '').decode('cp1250')
        fx_nazev=(fox_lista[4] or '').decode('cp1250') 
        fx_typ=(fox_lista[1] or '').decode('cp1250')
        db.typprace.insert(cinnost_id=listy_id,
              cislo=str(fox_lista[0]),
              vyrobce=fx_vyrobce,
              tovarni=fx_tovarni,
              skladem=fox_lista[7][0].upper()=='A',
              sirka=fox_lista[5], 
              cena=fox_lista[6], 
              nakupni=fox_lista[8],
              nazev=fx_nazev, 
              typ=fx_typ,
              zobrazit=u'%s %s %s %s %s (Kč %s)'%(fox_lista[0], fx_typ,
                              fx_nazev, fx_vyrobce, fx_tovarni, fox_lista[6]), 
              )    
    db.commit()
    
if __name__=='__main__':
    import_listy_rp()
