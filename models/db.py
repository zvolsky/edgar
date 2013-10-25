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
        Field('hlavni', 'boolean', label=T('Předvolený postup'),
                comment=T("postup se předvolí pro nové poptávky, není-li žádný nastaven pro uživatele")),
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
                comment=T("pro firmu typický výrobní postup")),
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
    Field('postup_id', db.postup, label=T('Obvyklý postup'),
            comment=T("pro něj předvolený výrobní postup (jinak se vezme od firmy)"),
            requires=IS_EMPTY_OR(IS_IN_DB(db, db.postup.id, '%(nazev)s'))),
    ]

auth.define_tables(username=True, signature=False)
db.auth_user.firma_id.requires=IS_EMPTY_OR(IS_IN_DB(db,db.firma.id,'%(jmeno)s'))

cm_comment = T("pro formulář zadání prací (položek poptávky)")
db.define_table('cinnost',        # číselník činností (prací pro poptávky)
        Field('firma_id', db.firma, label=T('Firma'),
         comment=T("příslušnost k firmě pro zobrazení v číselníku typů prací (nebo prázdné: nedefinuje žádný číselník)"),
         requires=IS_EMPTY_OR(IS_IN_DB(db, db.firma.id, '%(jmeno)s'))),
        Field('nazev', label=T('Název'),
                comment=T("název práce"), requires=IS_NOT_EMPTY()),
        Field('func_todo', label=T('Volat funkci'),
                comment=T("funkce pro stanovení 'mnozstvi' a 'info'")),
        Field('lbl', label=T('Label'), comment=cm_comment),
        Field('cmt', label=T('Comment'), comment=cm_comment),
        Field('strojovy', label=T('Řetězec pro pojmenování'),
                comment=T("název pro vyvoření id prvku (nezadání není kontrolováno, ale způsobí chybu v číselníku typů prací)")),
        Field('mn_vyznam', default='', label=T('Význam množství'),
         comment=T("veličina[jednotka]; je-li prázdné, množství se nezadává")),
        format='%(nazev)s',
        )

db.define_table('krok',        # výčet činností v daném postupu
        Field('postup_id', db.postup, label=T('Postup'),
                comment=T("patří do postupu")),
        Field('cinnost_id', db.cinnost, label=T('Činnost'),
                comment=T("práce")),
        Field('poradi', 'integer', default=999999, label=T('Pořadí v postupu'),
                comment=T("číslovat např. po 100 pro pozdější možné vložení")),
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
        Field('koeficient', 'decimal(4,2)', default=1.0,
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
        Field('vyzvednuto', 'datetime', label=T("Vše vyzvednuto"),
                comment=T("bylo vyzvednuto dne"),
                requires=IS_EMPTY_OR(IS_DATETIME(format=datetimeformat))),
        Field('zaplaceno', 'datetime', label=T("Zcela zaplaceno"),
                comment=T("bylo celé zaplaceno dne"),
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
        Field('vydal_id', db.auth_user,
                label=T("Vydal"), comment=T("zákazníkovi předal pracovník"),
                requires=IS_EMPTY_OR(IS_IN_DB(db, db.auth_user.id)),
                writable=False),
        Field('ks', 'integer', default=1, label=T('Ks'),
                comment=T("shodných kusů")),
        Field('popis', label=T('Popis'),
                comment=T("vhodná identifikace položky poptávky"),
                requires=IS_NOT_EMPTY()),
        Field('sirka', 'decimal(6,1)', label=T('Šířka [cm]')),
        Field('vyska', 'decimal(6,1)', label=T('Výška [cm]')),
        Field('horni', 'decimal(6,1)', label=T('Horní okraj [cm]')),
        Field('pravy', 'decimal(6,1)', label=T('Pravý okraj [cm]')),
        Field('dolni', 'decimal(6,1)', label=T('Dolní okraj [cm]')),
        Field('levy', 'decimal(6,1)', label=T('Levý okraj [cm]')),
        Field('cena_1ks', 'decimal(8,2)', default=0.0, label=T('Cena/ks'),
                comment=T("ceníková cena za 1 ks"), writable=False),
        Field('cena', 'decimal(8,2)', default=0.0, label=T('Cena'),
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
        Field('cena', 'decimal(8,2)', default=0.0, label=T('Cena')),
        Field('tovarni', default='', label=T('Tovární číslo')),
        Field('skladem', 'boolean', default=True, label=T('Skladem')),
        Field('maxsirka', 'decimal(6,1)', default=0.0, label=T('Max. šířka [cm]')),
        Field('maxdelka', 'decimal(6,1)', default=0.0, label=T('Max. délka [cm]')),
        Field('maxvyska', 'decimal(6,1)', default=0.0, label=T('Max. výška [cm]')),
        Field('nakupni', 'decimal(8,2)', default=0.0, label=T('Nákupní cena')),
        Field('cena2', 'decimal(8,2)', default=0.0, label=T('Cena 2 (okraje)')),
        Field('prorez', default='', label=T('Prořez')),
        Field('sirka', 'decimal(6,1)', default=0.0, label=T('Šířka (tloušťka) [cm]')),
        Field('sirkaprofilu', 'decimal(6,1)', default=0.0,
                label=T('Šířka profilu [cm]')),
        Field('vyskaprouzku', 'decimal(6,1)', default=0.0,
                label=T('Výška proužku [cm]')),
        Field('samolepka', 'boolean', default=False, label=T('Samolepka')),
        Field('bezpecnasirka', 'decimal(6,1)', default=0.0,
                label=T('Bezpečná šířka [cm]')),
        Field('bezpecnadelka', 'decimal(6,1)', default=0.0,
                label=T('Bezpečná délka [mm]')),
        Field('bezpecnavyska', 'decimal(6,1)', default=0.0,
                label=T('Bezpečná výška [cm]')),
        Field('kazeta', default='', label=T('Kazeta (vitrína)')),
        Field('gramaz', 'decimal(8,2)', default=0.0, label=T('Gramáž (gsm) [g/m2]')),
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
        Field('info', default='', readable=False, writable=False),
        Field('mnozstvi', 'decimal(6,1)', default=1.0, label=T('Množství'),
                comment=T("množství této práce nebo materiálu"),
                writable=False),
        Field('cena_1j', 'decimal(8,2)', default=0.0, label=T('Cena/jednotku'),
                comment=T("ceníková cena za jednotku"), writable=False),
        Field('cena', 'decimal(8,2)', default=0.0, label=T('Cena celkem'),
                comment=T("cena za tuto práci celkem"), writable=False),
        Field('cena2_1j', 'decimal(8,2)', default=0.0,
                label=T('Cena (okraje)/jednotku'),
                comment=T("ceníková cena za jednotku (okraje)"),
                writable=False),
        Field('cena2', 'decimal(8,2)', default=0.0, label=T('Cena okraje'),
                comment=T("cena za tuto práci (za okraje)"), writable=False),
        Field('dokonceno', 'datetime',
                label=T("Dokončeno"), comment=T("kdy byla práce dokončena"),
                requires=IS_EMPTY_OR(IS_DATETIME(format=datetimeformat)),
                writable=False),
        )

db.define_table('platba',
        Field('zakaznik_id', db.zakaznik, label=T("Zákazník")),
        Field('poptavka_id', db.poptavka, label=T('Poptávka'),
                comment=T("patří k poptávce"),
                readable=False, writable=False),
        Field('prevzal_id', db.auth_user,
                label=T("Převzal"),
                comment=T("platbu přijal (nebo vydal v případě záporné částky)"),
                writable=False),
        Field('castka', 'decimal(8,2)', default=0.0, label=T('Zaplacená částka'),
                comment=T("zaplacená částka (záporné pro vrácený přeplatek)"),
                writable=False),
        Field('zaplaceno', 'datetime', label=T("Kdy placeno"),
                comment=T("bylo placeno dne"),
                requires=IS_EMPTY_OR(IS_DATETIME(format=datetimeformat))),
        )
