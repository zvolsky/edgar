# coding: utf8

db.poptavka.zakaznik_id.widget = SQLFORM.widgets.autocomplete(
         request, db.zakaznik.jmeno, id_field=db.zakaznik.id,
         limitby=(0,14), min_length=2)
         # help_fields=[db.zakaznik.telefon,])
# bug: Autocomplet widget defined after '@auth.requires_signature()' doesn't work  

def index():
    redirect(URL('zadani_clear'))

@auth.requires_signature()
def poptavka():
    if not auth.user.firma_id:
        response.view = 'default/msg.html'
        return dict(msg=T("Před zadáváním poptávek požádej administrátora o zařazení k některé firmě (změna se projeví po opakovaném přihlášení)."))
        
    if getattr(session, 'zakaznik_id', None):
        zakaznik = db(db.zakaznik.id==session.zakaznik_id).select().first()
        form_zmen = FORM(INPUT(_type='submit', _value=T('Zvolit jiného zákazníka')),
                _action=URL('zadani_clear'))
        form_zvol = form_novy = None
        db.poptavka.stav.default = 'v'
        db.poptavka.stav.requires=(IS_IN_SET((('p',T('zatím nerealizovat')),
                ('v',T('výroba')))),IS_NOT_EMPTY())
        form_vice = SQLFORM(db.poptavka,
                fields = ['popis', 'stav', 'urgentni', 'ma_byt_dne', 'poznamka'],
                submit_button = T('Založit poptávku'),
                )
        if form_vice.validate():
            rok_Y, cislo, cislo_evid = __cisluj()
            id = db.poptavka.insert(
                    zakaznik_id=session.zakaznik_id,
                    zadal_id=auth.user_id,
                    firma_id=auth.user.firma_id,
                    obrok_=rok_Y,
                    obno_=cislo,
                    cislo=cislo_evid,
                    zakaznik_=zakaznik.jmeno,
                    **dict(form_vice.vars))
            db.commit()
            redirect(URL('poptavky', 'edit', args=id, user_signature=True))
    else:
        #db.poptavka.zakaznik_id.widget = SQLFORM.widgets.autocomplete(
        #     request, db.zakaznik.jmeno, id_field=db.zakaznik.id,
        #     limitby=(0,14), min_length=2)
        #     # help_fields=[db.zakaznik.telefon,])
        form_zvol = SQLFORM(db.poptavka, fields=['zakaznik_id'], submit_button = T('Zvolit výše uvedeného'))
        form_novy = FORM(INPUT(_type='submit', _value=T('Přidat zákazníka, kterého nemáme v evidenci')),
                _action=URL('zakaznici','pridej',args='np'))
        if form_zvol.validate():
            session.zakaznik_id = form_zvol.vars.zakaznik_id
            redirect(URL(user_signature=True))
        form_zmen = form_vice = zakaznik = None
    return dict(form_zvol=form_zvol, form_novy=form_novy, form_zmen=form_zmen,
             form_vice=form_vice, zakaznik=zakaznik)

@auth.requires_login()
def zadani_clear():
    session.zakaznik_id = None
    redirect(URL('poptavka', user_signature=True))

def __cisluj():
    '''číslování pro založení poptávky'''
    from datetime import date
    rok_Y = date.today()
    rok_y = rok_Y.strftime('%y')  # 13
    rok_Y = rok_Y.year            # 2013
    firma = db(db.firma.id==auth.user.firma_id).select().first()
    if firma.obrok==rok_Y:
        cislo = firma.obno + 1
        firma.update_record(obno=cislo)
    else:
        mx = db.poptavka.obno_.max()
        cislo = db(db.poptavka.obrok_==rok_Y).select(mx).first()[mx]
        cislo = cislo and cislo+1 or 1
        firma.update_record(obno=cislo, obrok=rok_Y)
    cislo_evid = '%s%s/%s' % (firma.obprefix, rok_y, cislo)
    return rok_Y, cislo, cislo_evid
            # dict(obrok_=rok_Y, obno_=cislo, cislo=cislo_evid)
