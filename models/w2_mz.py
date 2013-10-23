# coding: utf8

#---- ne právě ideálně individuality pro Edgara

def cena_zakaznik(poptavka_id, cena_poptavky):
    '''aktualizace poptavka.cena_zakaznik po změně slevy nebo ceny za součet položek''' 
    sleva = db(db.poptavka.id==poptavka_id).select(
            db.poptavka.sleva, db.zakaznik.koeficient,
            left=db.zakaznik.on(db.poptavka.zakaznik_id==db.zakaznik.id)
            ).first() 
    return (cena_poptavky/max(1.0,sleva.zakaznik.koeficient)
                                +sleva.poptavka.sleva)

#-------------------------------------------------

ikony = dict(ed=T("edit"), rm=T("smazat"), cp=T("přidat podobný"),
        fn=T("zvolit obrázek"), fs=T("ukázat přidaný náhled"),
        end=T("dokončení"))

'''
def needargs(pocet_arg):
    if len(request.args)<pocet_arg:
        redirect(URL('default', 'msg', args=1))
'''

def reset_session(vyhradit_pro):
    '''zatím neumím lépe, takže .pocet,.najdi využívám pro všechny tabulky a musím tedy alokovat konkrétní tabulce'''
    if getattr(session, 'vyhrazeno_pro', None) and session.vyhrazeno_pro==vyhradit_pro:
        return
    if getattr(session, 'pocet', None):
        del session.pocet
    if getattr(session, 'najdi', None):
        del session.najdi
    session.vyhrazeno_pro = vyhradit_pro

def dalsi(_class='odsazenoH'):
    pojmenovane = dict(_class=_class) if _class else {}
    form = FORM(INPUT(_type='submit', _value=T("přidej další")), _action=URL("pridej"), **pojmenovane)
    return form

def strankovani_polozky(zaznamu, poradi, page, per_page):
    return (
            (A(T("první"), _href=URL(args=(poradi,0)))) if page>1 else '',
            ' ',
            (A(T("předchozí"), _href=URL(args=(poradi,page-1)))) if page else '',
            SPAN(T("strana %s") % (page+1), _class="odsazeno")
                    if (page or zaznamu>per_page) else '',
            (A(T("další"), _href=URL(args=(poradi,page+1))))
                    if zaznamu>per_page else '',
            )

def strankovani(zaznamu, poradi, page, per_page, _class='odsazeno'):
    return SPAN(strankovani_polozky(zaznamu, poradi, page, per_page), _class=_class)

def priprav_strankovani(per_page=20):
    if len(request.args)>1 and not request.vars['filtr']:   # stránkujeme předchozí dotaz
        page = int(request.args[1])
        pocet = session.pocet
    else:       # nestránkujeme; tato sekce musí nově inicializovat session proměnné
        page = 0
        pocet = -1   # určit později
        if request.vars.najdi:
            session.najdi = request.vars.najdi
        else:
            session.najdi = None
    return pocet, page, per_page, (page*per_page,(page+1)*per_page+1)

def dourci_pocet(pocet, query):
    '''je-li počet záporný, je považován za dosud neurčený / jinak je ponechán původní'''
    if pocet<0:
        pocet = db(query).count()
        session.pocet = pocet
    return pocet

def filtr(default_sorting):
    return FORM(INPUT(_name='najdi'), INPUT(_type='submit', _value=T("najdi")),
            INPUT(_type='submit', _value=T("vše"), _onclick="najdi.value='';")
                             if session.najdi else '',
            _action=URL(args=(request.args and request.args[0] or default_sorting,0),
                    vars={'filtr':'novy'}))

def zobraz_pocet(pocet, _class="strong"):
    return SPAN(SPAN(T("celkem %s" % pocet), _class=_class), (
            session.najdi and SPAN(' %s: ' % T('s textem'), SPAN(session.najdi, _class=_class)) or ''))

def TOGGLE(prvek, zobrazit_jen_pro=None, start_hidden=True, **vice):
    if start_hidden:
        txt1 = '+ %s'%T("rozbalit")
        txt2 = '- %s'%T("sbalit")
    else:
        txt1 = '+ %s'%T("sbalit")
        txt2 = '- %s'%T("rozbalit")
    if zobrazit_jen_pro==None or zobrazit_jen_pro:
        return A(txt1, _href='#', _onclick="$('%s').toggle();$(this).text($(this).text() == '%s' ? '%s' : '%s');return false;"%(prvek, txt1, txt2, txt1), **vice)
    else:
        return ''
