# -*- coding: utf-8 -*-

from datetime import datetime
dateformat = '%d.%m.%Y'             # T() zde dělá potíže ve strftime()
datetimeformat = '%d.%m.%Y %H:%M'

migrate = True
db = DAL('sqlite://poptavky.sqlite',pool_size=1,check_reserved=['all'], migrate=migrate)
#db = DAL('mysql://cz:gEyTXVLfTeNeIrtxgCCE@mysql.server/cz$default',pool_size=5,check_reserved=['all'], migrate=migrate)
#db = DAL('mysql://cz:gEyTXVLfTeNeIrtxgCCE@localhost/edgar',pool_size=5,check_reserved=['all'], migrate=migrate)
#db = DAL('postgres://cz:gEyTXVLfTeNeIrtxgCCE@localhost/edgar',pool_size=5,check_reserved=['all'], migrate=migrate)

from gluon.tools import Auth, Crud

crud = Crud(db)
crud.settings.update_deletable = False

auth = Auth(db)
auth.settings.create_user_groups = False
auth.settings.actions_disabled+=('register','request_reset_password')
#auth.settings.registration_requires_approval = True

db.define_table('postup',         # postupy = seznamy prací pro poptávky
        Field('nazev', label=T('Název'),
                comment=T("název postupu - výčtu prací"),
                requires=IS_NOT_EMPTY()),
        Field('maska_id', 'string', label=T('div-id'),
                comment=T("div-id této masky"),
                writable=False),
        Field('maska', 'text', label=T('Maska'),
                comment=T("HTML masky s procento_s"),
                writable=False),
        Field('maska_flds', 'string', label=T('Pole v masce'),
                comment=T("které údaje promítá maska (oddělit čárkami)"),
                writable=False),
        Field('hardcoded_as', 'string', length=1, label=T('Hardkód HTML'),
                comment=T("*|o|r|f pro hardkódované masky"),
                writable=False),
        format='%(nazev)s',
        )

db.define_table('firma',
        Field('postup_id', db.postup, label=T('Hlavní postup'),
                comment=T("pro firmu typický postup prací")),
        Field('jmeno', label=T('Jméno'), requires=IS_NOT_EMPTY()),
        Field('obprefix', length=3, label=T('Prefix číselné řady')),
        Field('obno', 'integer', default=0,
                label=T('Poslední použité číslo řady')),
        Field('obrok', 'integer', default=0, label=T('Rok číslování řady')),
        Field('funkce', label=T('Funkce'),
                comment=T("Pojmenování function pro kontrolér typypraci")),
        format='%(jmeno)s',
        )

## create all tables needed by auth if not custom tables
auth.settings.extra_fields['auth_user'] = [
    Field('firma_id', db.firma, label=T('Firma')),
    ]

auth.define_tables(username=True, signature=False)
db.auth_user.firma_id.requires=IS_EMPTY_OR(IS_IN_DB(db,db.firma.id,'%(jmeno)s'))

cm_comment = T("pro formulář zadání prací (položek poptávky)")
db.define_table('cinnost',        # číselník činností (prací pro poptávky)
        Field('firma_id', db.firma, label=T('Firma'),
         comment=T("Příslušnost k firmě pro zobrazení v číselníku typů prací")),
        Field('nazev', label=T('Název'),
                comment=T("název práce"), requires=IS_NOT_EMPTY()),
        Field('lbl', label=T('Label'), comment=cm_comment),
        Field('cmt', label=T('Comment'), comment=cm_comment),
        Field('strojovy', label=T('Řetězec pro pojmenování'),
                comment=T("název pro vyvoření id prvku"),
                requires=IS_NOT_EMPTY()),
        Field('mn_vyznam', default='', label=T('Význam množství'),
         comment=T("veličina[jednotka]; je-li prázdné, množství se nezadává")),
        format='%(nazev)s',
        )

db.define_table('krok',        # výčet činností v daném postupu
        Field('postup_id', db.postup, label=T('Postup'),
                comment=T("patří do postupu")),
        Field('cinnost_id', db.cinnost, label=T('Činnost'),
                comment=T("práce")),
        format='%(nazev)s',
        )

db.define_table('vlastnost',      # číselník možných údajů činností
        Field('nazev', label=T('Název'), comment=T("název údaje"),
                requires=IS_NOT_EMPTY()),
        Field('strojovy', label=T('Název pole'),
                comment=T("název pole v tabulce typprace"),
                requires=IS_NOT_EMPTY()),
        Field('typ', default='', length=1, label=T('Typ údaje'),
                comment=T("typ proměnné / vstupního prvku")),
        Field('jednotka', default='', length=10, label=T('Jednotka'),
                comment=T("jednotka údaje")),
        format='%(nazev)s',
        )

db.define_table('popis',     # seznam vlastností relevantních pro činnost
        Field('cinnost_id', db.cinnost, label=T('Činnost'),
                comment=T("činnost")),
        Field('vlastnost_id', db.vlastnost, label=T('Vlastnost'),
                comment=T("vlastnost pro popis této činnosti")),
        Field('jednotka', length=10, label=T('Jednotka'),
                comment=T("doplňuje jednotku uvedenou u Vlastnosti")),
        format='%(nazev)s',
        )

db.define_table('zakaznik',
        Field('jmeno', label=T('Jméno'),
                comment=T("příjmení a jméno --nebo-- název firmy"),
                requires=IS_NOT_EMPTY()),
        Field('telefon', label=T('Telefon')),
        Field('email', label=T('E-mail')),
        Field('koeficient', 'double', default=1.0,
                label=T('Koeficient'), comment="1 nebo >1"),
        Field('staly', 'boolean', label=T('Stálý zákazník')),
        format='%(jmeno)s',
        )

zahajena = (('v',T('výroba')), ('k',T('kompletace')), ('e',T('vydáno')))
db.define_table('poptavka',
        Field('zakaznik_id', db.zakaznik, label=T("Zákazník")),
        Field('zadal_id', db.auth_user,
                label=T("Zadal"), comment=T("poptávku přijal"), writable=False),
        Field('vydal_id', db.auth_user,
                label=T("Vydal"), comment=T("zákazníkovi předal pracovník"),
                requires=IS_EMPTY_OR(IS_IN_DB(db, db.auth_user.id)),
                writable=False),
        Field('firma_id', db.firma,
                label=T("Firma"), comment=T("přijato firmou"), writable=False),
        Field('cislo', label=T('Číslo'),
                comment=T("firemní pořadové číslo poptávky"), writable=False),
        Field('popis', label=T('Popis'),
                comment=T("popis poptávky (zobrazuje se v seznamu poptávek)"),
                requires=IS_NOT_EMPTY()),
        Field('urgentni', 'boolean', label=T('Urgentní')),
        Field('zapsano_dne', 'datetime', default=datetime.now(),
                label=T("Zapsáno dne"), comment=T("kdy přijato"),
                requires=IS_DATETIME(format=datetimeformat),
                writable=False),
        Field('ma_byt_dne', 'date', label=T("Připravit dne"),
                comment=T("má být k vyzvednutí dne"),
                requires=IS_EMPTY_OR(IS_DATE(format=dateformat))),
        Field('cena', 'integer', default=0, label=T("Obvyklá cena"),
                comment=T("celková cena"), writable=False),
        Field('sleva', 'integer', default=0, label=T('Přirážka/Sleva'),
                comment=T("(+)přirážka (-)sleva přiznaná pro tuto poptávku")),
        Field('cena_zakaznik', 'integer', default=0, label=T('Výsledná cena'),
                comment=T("cena po poptávkové i zákaznické slevě"),
                compute=lambda r: r['cena']+r['sleva']),
        Field('stav', length=1, label=T("Stav poptávky"), default='p',
                widget=SQLFORM.widgets.options.widget,
                requires=(IS_IN_SET((('p',T('zatím nerealizovat')),)+zahajena),
                            IS_NOT_EMPTY())),
        Field('cast_ne', 'boolean', label=T('Část nerealizovat'),
             comment=T('zaškrtni, nemají-li se zatím vyrábět všechny položky'),
             readable=False, writable=False),
        Field('vyzvednuto', 'datetime', label=T("Vyzvednuto"),
                comment=T("bylo vyzvednuto dne"),
                requires=IS_EMPTY_OR(IS_DATETIME(format=datetimeformat))),
        Field('poznamka', 'text', label=T("Poznámka")),
        Field('zakaznik_', default='', readable=False, writable=False),
        Field('polozek_', 'integer', default=0, readable=False, writable=False),
        Field('obrok_', 'integer', default=0, readable=False, writable=False),
        Field('obno_', 'integer', default=0, readable=False, writable=False),
        Field('foto_', 'boolean', default=False),
        format=
        '%(cislo)s, %(popis)s, %(zakaznik_)s, %(zapsano_dne)s - %(ma_byt_dne)s',
        )

db.define_table('polozka',
        Field('poptavka_id', db.poptavka, label=T('Poptávka'),
                comment=T("patří k poptávce"), writable=False),
        Field('postup_id', db.postup, label=T('Postup'),
                comment=T("postup řídí seznam prací/materiálu"),
                readable=False, writable=False),
        Field('ks', 'integer', default=1, label=T('Ks'),
                comment=T("shodných kusů")),
        Field('popis', label=T('Popis'),
                comment=T("vhodná identifikace položky poptávky"),
                requires=IS_NOT_EMPTY()),
        Field('sirka', 'integer', label=T('Šířka [mm]')),
        Field('vyska', 'integer', label=T('Výška [mm]')),
        Field('horni', 'integer', label=T('Horní okraj [mm]')),
        Field('pravy', 'integer', label=T('Pravý okraj [mm]')),
        Field('dolni', 'integer', label=T('Dolní okraj [mm]')),
        Field('levy', 'integer', label=T('Levý okraj [mm]')),
        Field('cena_1ks', 'double', default=0, label=T('Cena/ks'),
                comment=T("ceníková cena za 1 ks"), writable=False),
        Field('cena', 'double', default=0, label=T('Cena'),
                comment=T("cena za všechny ks"), writable=False),
        Field('zatim_ne', 'boolean', default=False,
            label=T('Zatím odložit realizaci'),
            comment=T('zaškrtni, jestliže se zatím nemá tato položka vyrábět'),
            readable=False, writable=False), # dočasně? deaktivováno
        Field('vyzvednuto', 'datetime', label=T("Vyzvednuto"),
                comment=T("bylo vyzvednuto dne"),
                requires=IS_EMPTY_OR(IS_DATETIME(format=datetimeformat))),
        Field('foto', 'upload', uploadseparate=True, autodelete=True),
        Field('poznamka', 'text', label=T("Poznámka")),
        format='%(popis)s',
        )

db.define_table('typprace',
        Field('cinnost_id', db.cinnost, label=T('Činnost'),
                readable=False, writable=False),
        Field('vyrobce', default='', label=T('Výrobce')),
        Field('typ', default='', label=T('Typ')),
        Field('nazev', default='', label=T('Název')),
        Field('cislo', default='', label=T('Číslo')),
        Field('cena', 'double', default=0, label=T('Cena')),
        Field('tovarni', default='', label=T('Tovární číslo')),
        Field('skladem', 'boolean', default=True, label=T('Skladem')),
        Field('maxsirka', 'integer', default=0, label=T('Max. šířka [mm]')),
        Field('maxdelka', 'integer', default=0, label=T('Max. délka [mm]')),
        Field('maxvyska', 'integer', default=0, label=T('Max. výška [mm]')),
        Field('nakupni', 'double', default=0, label=T('Nákupní cena')),
        Field('cena2', 'double', default=0, label=T('Cena 2 (okraje)')),
        Field('prorez', default='', label=T('Prořez')),
        Field('sirka', 'integer', default=0, label=T('Šířka (tloušťka) [mm]')),
        Field('sirkaprofilu', 'integer', default=0,
                label=T('Šířka profilu [mm]')),
        Field('vyskaprouzku', 'integer', default=0,
                label=T('Výška proužku [mm]')),
        Field('samolepka', 'boolean', default=False, label=T('Samolepka')),
        Field('bezpecnasirka', 'integer', default=0,
                label=T('Bezpečná šířka [mm]')),
        Field('bezpecnadelka', 'integer', default=0,
                label=T('Bezpečná délka [mm]')),
        Field('bezpecnavyska', 'integer', default=0,
                label=T('Bezpečná výška [mm]')),
        Field('kazeta', default='', label=T('Kazeta (vitrína)')),
        Field('gramaz', 'double', default=0, label=T('Gramáž (gsm) [g/m2]')),
        format='%(cinnost_id)s: %(nazev)s',
        )

db.define_table('prace',
        Field('poptavka_id', db.poptavka, label=T('Poptávka'),
                comment=T("patří k poptávce"),
                readable=False, writable=False),
        Field('polozka_id', db.polozka, label=T('Položka poptávky'),
                comment=T("patří k položce poptávky"),
                readable=False, writable=False),
        Field('typprace_id', db.typprace, label=T('Typ práce'),
                comment=T("typ práce podle číselníku prací/materiálu"),
                readable=False, writable=False),
        Field('cinnost_id', db.cinnost, label=T('Činnost'),
                comment=T("pro kterou činnost je zvolen typ práce"),
                readable=False, writable=False),
        Field('mnozstvi', 'double', default=1, label=T('Množství'),
                comment=T("množství této práce nebo materiálu")),
        Field('cena_1j', label=T('Cena/jednotku'),
                comment=T("ceníková cena za jednotku"), writable=False),
        Field('cena', label=T('Cena celkem'),
                comment=T("cena za tuto práci celkem"), writable=False),
        Field('cena2_1j', label=T('Cena (okraje)/jednotku'),
                comment=T("ceníková cena za jednotku (okraje)"),
                writable=False),
        Field('cena2', label=T('Cena okraje'),
                comment=T("cena za tuto práci (za okraje)"), writable=False),
        Field('dokonceno', 'datetime',
                label=T("Dokončeno"), comment=T("kdy byla práce dokončena"),
                requires=IS_EMPTY_OR(IS_DATETIME(format=datetimeformat)),
                writable=False),
        )
