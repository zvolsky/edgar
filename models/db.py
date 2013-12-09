# -*- coding: utf-8 -*-

from datetime import datetime
dateformat = '%d.%m.%Y'             # T() zde dělá potíže ve strftime()
datetimeformat = '%d.%m.%Y %H:%M'

def TFu(txt):
    '''temporary instead of T(), to speed up and have translation table clear'''
    return txt


if request.is_local:
    from gluon.custom_import import track_changes
    track_changes(True)    # auto-reload modules

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
        Field('nazev', label=TFu('Název'),
                comment=TFu("název postupu - výčtu prací"),
                requires=IS_NOT_EMPTY()),
        Field('hlavni', 'boolean', label=TFu('Předvolený postup'),
                comment=TFu("postup se předvolí pro nové poptávky, není-li žádný nastaven pro uživatele")),
        Field('maska_id', 'string', label=TFu('div-id'),
                comment=TFu("div-id této masky"),
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
        Field('postup_id', db.postup, label=TFu('Hlavní postup'),
                comment=TFu("pro firmu typický výrobní postup")),
        Field('jmeno', label=TFu('Jméno'), requires=IS_NOT_EMPTY()),
        Field('obprefix', length=3, label=TFu('Prefix číselné řady')),
        Field('obno', 'integer', default=0,
                label=TFu('Poslední použité číslo řady')),
        Field('obrok', 'integer', default=0, label=TFu('Rok číslování řady')),
        Field('funkce', label=TFu('Funkce'),
                comment=TFu("Pojmenování function pro kontrolér typypraci")),
        format='%(jmeno)s',
        )

## create all tables needed by auth if not custom tables
auth.settings.extra_fields['auth_user'] = [
    Field('firma_id', db.firma, label=TFu('Firma')),
    Field('postup_id', db.postup, label=TFu('Obvyklý postup'),
            comment=TFu("pro něj předvolený výrobní postup (jinak se vezme od firmy)"),
            requires=IS_EMPTY_OR(IS_IN_DB(db, db.postup.id, '%(nazev)s'))),
    ]

auth.define_tables(username=True, signature=False)
db.auth_user.firma_id.requires=IS_EMPTY_OR(IS_IN_DB(db,db.firma.id,'%(jmeno)s'))

cm_comment = TFu("pro formulář zadání prací (položek poptávky)")
db.define_table('cinnost',        # číselník činností (prací pro poptávky)
        Field('firma_id', db.firma, label=TFu('Firma'),
         comment=TFu("příslušnost k firmě pro zobrazení v číselníku typů prací (nebo prázdné: nedefinuje žádný číselník)"),
         requires=IS_EMPTY_OR(IS_IN_DB(db, db.firma.id, '%(jmeno)s'))),
        Field('nazev', label=TFu('Název'),
                comment=TFu("název práce"), requires=IS_NOT_EMPTY()),
        Field('chybi', default='bez ...', label=TFu('Text pro nepoužití'),
                comment=TFu("zobrazovaný text, jestliže se nepoužije"),
                requires=IS_NOT_EMPTY()),
        Field('func_todo', label=TFu('Volat funkci'),
                comment=TFu("funkce pro stanovení 'mnozstvi' a 'info'")),
        Field('lbl', label=TFu('Label'), comment=cm_comment),
        Field('cmt', label=TFu('Comment'), comment=cm_comment),
        Field('strojovy', label=TFu('Řetězec pro pojmenování'),
                comment=TFu("název pro vyvoření id prvku (nezadání není kontrolováno, ale způsobí chybu v číselníku typů prací)")),
        Field('mn_vyznam', default='', label=TFu('Význam množství'),
         comment=TFu("veličina[jednotka]; je-li prázdné, množství se nezadává")),
        format='%(nazev)s',
        )

db.define_table('krok',        # výčet činností v daném postupu
        Field('postup_id', db.postup, label=TFu('Postup'),
                comment=TFu("patří do postupu")),
        Field('cinnost_id', db.cinnost, label=TFu('Činnost'),
                comment=TFu("práce")),
        Field('poradi', 'integer', default=999999, label=TFu('Pořadí v postupu'),
                comment=TFu("číslovat např. po 100 pro pozdější možné vložení")),
        format='%(nazev)s',
        )

db.define_table('vlastnost',      # číselník možných údajů činností
        Field('nazev', label=TFu('Název'), comment=TFu("název údaje"),
                requires=IS_NOT_EMPTY()),
        Field('strojovy', label=TFu('Název pole'),
                comment=TFu("název pole v tabulce typprace"),
                requires=IS_NOT_EMPTY()),
        Field('typ', default='', length=1, label=TFu('Typ údaje'),
                comment=TFu("typ proměnné / vstupního prvku")),
        Field('jednotka', default='', length=10, label=TFu('Jednotka'),
                comment=TFu("jednotka údaje")),
        format='%(nazev)s',
        )

db.define_table('popis',     # seznam vlastností relevantních pro činnost
        Field('cinnost_id', db.cinnost, label=TFu('Činnost'),
                comment=TFu("činnost")),
        Field('vlastnost_id', db.vlastnost, label=TFu('Vlastnost'),
                comment=TFu("vlastnost pro popis této činnosti")),
        Field('jednotka', length=10, label=TFu('Jednotka'),
                comment=TFu("doplňuje jednotku uvedenou u Vlastnosti")),
        format='%(nazev)s',
        )

db.define_table('zakaznik',
        Field('jmeno', label=TFu('Jméno'),
                comment=TFu("příjmení a jméno --nebo-- název firmy"),
                requires=IS_NOT_EMPTY()),
        Field('telefon', label=TFu('Telefon')),
        Field('email', label=TFu('E-mail')),
        Field('koeficient', 'decimal(4,2)', default=1.0,
                label=TFu('Koeficient'), comment="1 nebo >1"),
        Field('staly', 'boolean', label=TFu('Stálý zákazník')),
        format='%(jmeno)s',
        )

zahajena = (('v',TFu('výroba')), ('k',TFu('kompletace')), ('e',TFu('vydáno')))
db.define_table('poptavka',
        Field('zakaznik_id', db.zakaznik, label=TFu("Zákazník")),
        Field('zadal_id', db.auth_user,
                label=TFu("Zadal"), comment=TFu("poptávku přijal"), writable=False),
        Field('vydal_id', db.auth_user,
                label=TFu("Vydal"), comment=TFu("zákazníkovi předal pracovník"),
                requires=IS_EMPTY_OR(IS_IN_DB(db, db.auth_user.id)),
                writable=False),
        Field('firma_id', db.firma,
                label=TFu("Firma"), comment=TFu("přijato firmou"), writable=False),
        Field('cislo', label=TFu('Číslo'),
                comment=TFu("firemní pořadové číslo poptávky"), writable=False),
        Field('popis', label=TFu('Popis'),
                comment=TFu("popis poptávky (zobrazuje se v seznamu poptávek)"),
                requires=IS_NOT_EMPTY()),
        Field('urgentni', 'boolean', label=TFu('Urgentní')),
        Field('zapsano_dne', 'datetime', default=datetime.now(),
                label=TFu("Zapsáno dne"), comment=TFu("kdy přijato"),
                requires=IS_DATETIME(format=datetimeformat),
                writable=False),
        Field('ma_byt_dne', 'date', label=TFu("Připravit dne"),
                comment=TFu("má být k vyzvednutí dne"),
                requires=IS_EMPTY_OR(IS_DATE(format=dateformat))),
        Field('cena', 'integer', default=0, label=TFu("Obvyklá cena"),
                comment=TFu("celková cena"), writable=False),
        Field('sleva', 'integer', default=0, label=TFu('Přirážka/Sleva'),
                comment=TFu("(+)přirážka (-)sleva přiznaná pro tuto poptávku")),
        Field('cena_zakaznik', 'integer', default=0, label=TFu('Výsledná cena'),
                comment=TFu("cena po poptávkové i zákaznické slevě"),
                compute=lambda r: r['cena']+r['sleva']),
        Field('stav', length=1, label=TFu("Stav poptávky"), default='p',
                widget=SQLFORM.widgets.options.widget,
                requires=(IS_IN_SET((('p',TFu('zatím nerealizovat')),)+zahajena),
                            IS_NOT_EMPTY())),
        Field('cast_ne', 'boolean', label=TFu('Část nerealizovat'),
             comment=TFu('zaškrtni, nemají-li se zatím vyrábět všechny položky'),
             readable=False, writable=False),
        Field('vyzvednuto', 'datetime', label=TFu("Vše vyzvednuto"),
                comment=TFu("bylo vyzvednuto dne"),
                requires=IS_EMPTY_OR(IS_DATETIME(format=datetimeformat))),
        Field('zaplaceno', 'datetime', label=TFu("Zcela zaplaceno"),
                comment=TFu("bylo celé zaplaceno dne"),
                requires=IS_EMPTY_OR(IS_DATETIME(format=datetimeformat))),
        Field('poznamka', 'text', label=TFu("Poznámka")),
        Field('zakaznik_', default='', readable=False, writable=False),
        Field('polozek_', 'integer', default=0, readable=False, writable=False),
        Field('obrok_', 'integer', default=0, readable=False, writable=False),
        Field('obno_', 'integer', default=0, readable=False, writable=False),
        Field('foto_', 'boolean', default=False),
        format=
        '%(cislo)s, %(popis)s, %(zakaznik_)s, %(zapsano_dne)s - %(ma_byt_dne)s',
        )

'''
db.define_table('polozka',
        Field('poptavka_id', db.poptavka),
        Field('postup_id', db.postup),
        Field('vydal_id', db.auth_user),
        Field('ks', 'integer'),
        Field('popis'),
        Field('sirka', 'decimal(6,1)'),
        Field('vyska', 'decimal(6,1)'),
        Field('horni', 'decimal(6,1)'),
        Field('pravy', 'decimal(6,1)'),
        Field('dolni', 'decimal(6,1)'),
        Field('levy', 'decimal(6,1)'),
        Field('cena_1ks', 'decimal(8,2)'),
        Field('cena', 'decimal(8,2)'),
        Field('zatim_ne', 'boolean'),
        Field('vyzvednuto', 'datetime'),
        Field('foto', 'upload'),
        Field('poznamka', 'text'),
        )
'''

db.define_table('polozka',
        Field('poptavka_id', db.poptavka, label=TFu('Poptávka'),
                comment=TFu("patří k poptávce"), writable=False),
        Field('postup_id', db.postup, label=TFu('Postup'),
                comment=TFu("postup řídí seznam prací/materiálu"),
                readable=False, writable=False),
        Field('vydal_id', db.auth_user,
                label=TFu("Vydal"), comment=TFu("zákazníkovi předal pracovník"),
                requires=IS_EMPTY_OR(IS_IN_DB(db, db.auth_user.id)),
                writable=False),
        Field('ks', 'integer', default=1, label=TFu('Ks'),
                comment=TFu("shodných kusů")),
        Field('popis', label=TFu('Popis'),
                comment=TFu("vhodná identifikace položky poptávky"),
                requires=IS_NOT_EMPTY()),
        Field('sirka', 'decimal(6,1)', label=TFu('Šířka [cm]')),
        Field('vyska', 'decimal(6,1)', label=TFu('Výška [cm]')),
        Field('horni', 'decimal(6,1)', label=TFu('Horní okraj [cm]')),
        Field('pravy', 'decimal(6,1)', label=TFu('Pravý okraj [cm]')),
        Field('dolni', 'decimal(6,1)', label=TFu('Dolní okraj [cm]')),
        Field('levy', 'decimal(6,1)', label=TFu('Levý okraj [cm]')),
        Field('cena_1ks', 'decimal(8,2)', default=0.0, label=TFu('Cena/ks'),
                comment=TFu("ceníková cena za 1 ks"), writable=False),
        Field('cena', 'decimal(8,2)', default=0.0, label=TFu('Cena'),
                comment=TFu("cena za všechny ks"), writable=False),
        Field('zatim_ne', 'boolean', default=False,
            label=TFu('Zatím odložit realizaci'),
            comment=TFu('zaškrtni, jestliže se zatím nemá tato položka vyrábět'),
            readable=False, writable=False), # dočasně? deaktivováno
        Field('vyzvednuto', 'datetime', label=TFu("Vyzvednuto"),
                comment=TFu("bylo vyzvednuto dne"),
                requires=IS_EMPTY_OR(IS_DATETIME(format=datetimeformat))),
        Field('foto', 'upload', uploadseparate=True, autodelete=True),
        Field('poznamka', 'text', label=TFu("Poznámka")),
        format='%(popis)s',
        )

db.define_table('typprace',
        Field('cinnost_id', db.cinnost, label=TFu('Činnost'),
                readable=False, writable=False),
        Field('hlavni', 'boolean', default=False, label=TFu('Předvolený typ')),
        Field('vyrobce', default='', label=TFu('Výrobce')),
        Field('typ', default='', label=TFu('Typ')),
        Field('nazev', default='', label=TFu('Název')),
        Field('cislo', default='', label=TFu('Číslo')),
        Field('cena', 'decimal(8,2)', default=0.0, label=TFu('Cena')),
        Field('tovarni', default='', label=TFu('Tovární číslo')),
        Field('skladem', 'boolean', default=True, label=TFu('Skladem')),
        Field('maxsirka', 'decimal(6,1)', default=0.0, label=TFu('Max. šířka [cm]')),
        Field('maxdelka', 'decimal(6,1)', default=0.0, label=TFu('Max. délka [cm]')),
        Field('maxvyska', 'decimal(6,1)', default=0.0, label=TFu('Max. výška [cm]')),
        Field('nakupni', 'decimal(8,2)', default=0.0, label=TFu('Nákupní cena')),
        Field('cena2', 'decimal(8,2)', default=0.0, label=TFu('Cena 2 (okraje)')),
        Field('prorez', default='', label=TFu('Prořez')),
        Field('sirka', 'decimal(6,1)', default=0.0, label=TFu('Šířka (tloušťka) [cm]')),
        Field('sirkaprofilu', 'decimal(6,1)', default=0.0,
                label=TFu('Šířka profilu [cm]')),
        Field('vyskaprouzku', 'decimal(6,1)', default=0.0,
                label=TFu('Výška proužku [cm]')),
        Field('samolepka', 'boolean', default=False, label=TFu('Samolepka')),
        Field('bezpecnasirka', 'decimal(6,1)', default=0.0,
                label=TFu('Bezpečná šířka [cm]')),
        Field('bezpecnadelka', 'decimal(6,1)', default=0.0,
                label=TFu('Bezpečná délka [mm]')),
        Field('bezpecnavyska', 'decimal(6,1)', default=0.0,
                label=TFu('Bezpečná výška [cm]')),
        Field('kazeta', default='', label=TFu('Kazeta (vitrína)')),
        Field('gramaz', 'decimal(8,2)', default=0.0, label=TFu('Gramáž (gsm) [g/m2]')),
        format='%(cinnost_id)s: %(nazev)s',
        )

db.define_table('prace',
        Field('poptavka_id', db.poptavka, label=TFu('Poptávka'),
                comment=TFu("patří k poptávce"),
                readable=False, writable=False),
        Field('polozka_id', db.polozka, label=TFu('Položka poptávky'),
                comment=TFu("patří k položce poptávky"),
                readable=False, writable=False),
        Field('typprace_id', db.typprace, label=TFu('Typ práce'),
                comment=TFu("typ práce podle číselníku prací/materiálu"),
                readable=False, writable=False),
        Field('cinnost_id', db.cinnost, label=TFu('Činnost'),
                comment=TFu("pro kterou činnost je zvolen typ práce"),
                readable=False, writable=False),
        Field('info', default='', readable=False, writable=False),
        Field('mnozstvi', 'decimal(6,1)', default=1.0, label=TFu('Množství'),
                comment=TFu("množství této práce nebo materiálu"),
                writable=False),
        Field('cena_1j', 'decimal(8,2)', default=0.0, label=TFu('Cena/jednotku'),
                comment=TFu("ceníková cena za jednotku"), writable=False),
        Field('cena', 'decimal(8,2)', default=0.0, label=TFu('Cena celkem'),
                comment=TFu("cena za tuto práci celkem"), writable=False),
        Field('cena2_1j', 'decimal(8,2)', default=0.0,
                label=TFu('Cena (okraje)/jednotku'),
                comment=TFu("ceníková cena za jednotku (okraje)"),
                writable=False),
        Field('cena2', 'decimal(8,2)', default=0.0, label=TFu('Cena okraje'),
                comment=TFu("cena za tuto práci (za okraje)"), writable=False),
        Field('dokonceno', 'datetime',
                label=TFu("Dokončeno"), comment=TFu("kdy byla práce dokončena"),
                requires=IS_EMPTY_OR(IS_DATETIME(format=datetimeformat)),
                writable=False),
        )

db.define_table('platba',
        Field('zakaznik_id', db.zakaznik, label=TFu("Zákazník")),
        Field('poptavka_id', db.poptavka, label=TFu('Poptávka'),
                comment=TFu("patří k poptávce"),
                readable=False, writable=False),
        Field('prevzal_id', db.auth_user,
                label=TFu("Převzal"),
                comment=TFu("platbu přijal (nebo vydal v případě záporné částky)"),
                writable=False),
        Field('castka', 'decimal(8,2)', default=0.0, label=TFu('Zaplacená částka'),
                comment=TFu("zaplacená částka (záporné pro vrácený přeplatek)"),
                writable=False),
        Field('zaplaceno', 'datetime', label=TFu("Kdy placeno"),
                comment=TFu("bylo placeno dne"),
                requires=IS_EMPTY_OR(IS_DATETIME(format=datetimeformat))),
        )

db.define_table('plus_def',        # výčet ůdajů navíc určité činnosti
        Field('cinnost_id', db.cinnost, label=TFu('Činnost'),
                comment=TFu("práce")),
        Field('poradi', 'integer', default=999999, label=TFu('Pořadí v postupu'),
                comment=TFu("číslovat např. po 100 pro pozdější možné vložení")),
        Field('nazev', label=TFu('Název (caption) údaje')),
        Field('typ', length=20, default='string', label=TFu('Typ')),
        Field('tabulka', length=12, default='string', label=TFu('Tabulka')),
        Field('css_class', length=12, default='string', label=TFu('CSS class')),
        Field('iddefault', 'integer', label=TFu('ID defaultní hodnoty v "tabulka"')),
        Field('volby', label=TFu('(pro integer) Volby selectu (oddělit |)')),
        format='%(nazev)s',
        )
# v plus_def.iddefault může být uvedeno ID záznamu v plus_<tabulka>
#   takový záznam s defaultní hodnotou je potřeba vytvořit ručně (prace_id bude None) 
def def_plus(db, tabulka, typ):
    tbl = 'plus_'+tabulka 
    if not db.has_key(tbl):
        db.define_table(tbl,
            Field('polozka_id', db.polozka, label=TFu('Položka, ke které údaj patří')),
            Field('prace_id', db.prace, label=TFu('Práce, ke které údaj patří')),
            Field('plus_def_id', db.plus_def, label=TFu('Který údaj')),
            Field('hodnota', typ, label=TFu('Hodnota údaje')),
            )
# uložení údajů navíc
plus_def = db(db.plus_def).select()
for plus_def1 in plus_def:
    def_plus(db, plus_def1.tabulka, plus_def1.typ)

def __vybrany_postup():
    if auth.user:
        if session.postup_user!=auth.user_id:
            session.postup_id = 0
            session.postup_user = auth.user_id
        if not session.postup_id:
            if auth.user.postup_id:
                session.postup_id = auth.user.postup_id
            elif auth.user.firma_id:
                firma = db.firma[auth.user.firma_id]
                if firma.postup_id: 
                    session.postup_id = firma.postup_id
            if session.postup_id:
                session.postup_txt = db.postup[session.postup_id].nazev
            else:
                hlavni = db(db.postup.hlavni==True).select().first()
                if not hlavni:
                    hlavni = db(db.postup).select().first()
                session.postup_id = hlavni.id
                session.postup_txt = hlavni.nazev
    else:
        session.postup_user = 0
        session.postup_txt = ''
        return 0
    return session.postup_id
__vybrany_postup()