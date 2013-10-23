# coding: utf8

def index():
    redirect(URL('aktivni'))

@auth.requires_login()
def seznam(query, pocet, page, per_page, limitby):
    '''voláno z vse,poptavky,vyroba,kompletace,aktivni,vydano'''
    pocet = dourci_pocet(pocet, query)

    trideni = dict(c=db.poptavka.zapsano_dne,
                    p=db.poptavka.popis,
                    d=db.poptavka.ma_byt_dne,
                    z=db.zakaznik.jmeno)                    # možná pořadí
    poradi = len(request.args) and request.args[0] or 'c'   # aktivní pořadí
    
    poptavky = db(query).select(db.poptavka.ALL, db.zakaznik.ALL,
            left = db.zakaznik.on(db.zakaznik.id==db.poptavka.zakaznik_id),
            orderby=trideni[poradi] if poradi.islower()
                    else ~trideni[poradi.lower()],
            limitby=limitby)

    response.view = 'poptavky/seznam.html'
    return dict(filtr=filtr('c'), pocet=zobraz_pocet(pocet), poptavky=poptavky,
            strankovani=strankovani(len(poptavky), poradi, page, per_page),
            per_page=per_page)

@auth.requires_login()
def vse():
    reset_session('poptavky_vse')
    pocet, page, per_page, limitby = priprav_strankovani() # pozor, nastavuje session.najdi
    if session.najdi:
        query = db.poptavka
    else:
        query = db.poptavka
    return seznam(query, pocet, page, per_page, limitby)

@auth.requires_login()
def poptavky():
    reset_session('poptavky_poptavky')
    pocet, page, per_page, limitby = priprav_strankovani()
                            # pozor, nastavuje session.najdi
    if session.najdi:
        query = ((db.poptavka.stav=='p') |
        (db.poptavka.cast_ne==True)) & (db.poptavka.zakaznik_id==db.zakaznik.id)
    else:
        query = ((db.poptavka.stav=='p') |
        (db.poptavka.cast_ne==True)) & (db.poptavka.zakaznik_id==db.zakaznik.id)
    return seznam(query, pocet, page, per_page, limitby)

@auth.requires_login()
def vyroba():
    reset_session('poptavky_vyroba')
    pocet, page, per_page, limitby = priprav_strankovani(per_page=100)
                            # pozor, nastavuje session.najdi
    if session.najdi:
        query = (db.poptavka.stav=='v') & (
                                db.poptavka.zakaznik_id==db.zakaznik.id)
    else:
        query = (db.poptavka.stav=='v') & (
                                db.poptavka.zakaznik_id==db.zakaznik.id)
    return seznam(query, pocet, page, per_page, limitby)

@auth.requires_login()
def kompletace():
    reset_session('poptavky_kompletace')
    pocet, page, per_page, limitby = priprav_strankovani(per_page=100)
                            # pozor, nastavuje session.najdi
    if session.najdi:
        query = (db.poptavka.stav=='k') & (
                                db.poptavka.zakaznik_id==db.zakaznik.id)
    else:
        query = (db.poptavka.stav=='k') & (
                                db.poptavka.zakaznik_id==db.zakaznik.id)
    return seznam(query, pocet, page, per_page, limitby)

@auth.requires_login()
def aktivni():
    reset_session('poptavky_aktivni')
    pocet, page, per_page, limitby = priprav_strankovani(per_page=100)
                            # pozor, nastavuje session.najdi
    if session.najdi:
        query = ((db.poptavka.stav=='v') |
            (db.poptavka.stav=='k')) & (db.poptavka.zakaznik_id==db.zakaznik.id)
        #query = db.zakaznik.jmeno.contains(session.najdi
        #            ) | db.zakaznik.telefon.contains(session.najdi)
    else:
        query = ((db.poptavka.stav=='v') |
            (db.poptavka.stav=='k')) & (db.poptavka.zakaznik_id==db.zakaznik.id)
    return seznam(query, pocet, page, per_page, limitby)

@auth.requires_login()
def vydano():
    reset_session('poptavky_vydano')
    pocet, page, per_page, limitby = priprav_strankovani()
                            # pozor, nastavuje session.najdi
    if session.najdi:
        query = (db.poptavka.vyzvednuto.year()<2000) & (
                                db.poptavka.zakaznik_id==db.zakaznik.id)
    else:
        query = (db.poptavka.vyzvednuto.year()<2000) & (
                                db.poptavka.zakaznik_id==db.zakaznik.id)
    return seznam(query, pocet, page, per_page, limitby)

@auth.requires_signature()
def edit():
    zadal = db.auth_user.with_alias('zadal')
    vydal = db.auth_user.with_alias('vydal')
    poptavka = db(db.poptavka.id==request.args[0]).select(
            db.poptavka.ALL, db.zakaznik.ALL, zadal.username, vydal.username,
            left = (db.zakaznik.on(db.zakaznik.id==db.poptavka.zakaznik_id),
                zadal.on(zadal.id==db.poptavka.zadal_id),
                vydal.on(vydal.id==db.poptavka.vydal_id))
            ).first()

    if request.post_vars.postup: # odstraněné tlačítko:  or .post_vars.komplet
        redirect(URL('polozky', 'pridej',
          args=(poptavka.poptavka.id,
                request.post_vars.postup and request.post_vars.vybrany_postup
                or 'x'),
          user_signature=True)) # přidat novou položku (buttonem formuláře)

    polozky = db(db.polozka.poptavka_id==poptavka.poptavka.id).select()
    postupy = db().select(db.postup.ALL, orderby=db.postup.nazev)
    default_postup_id = postupy.first().id
            # defaultní hodnota předvoleného postupu pro případ,
            #  že u poptávky chybí firma nebo u firmy defaultní postup
    if poptavka.poptavka.firma_id:
        default_postup_id = db(db.firma.id==poptavka.poptavka.firma_id
                    ).select(db.firma.postup_id).first().postup_id
    select_postup = SELECT([OPTION(postup.nazev, _value=postup.id)
                    for postup in postupy],
                    value=default_postup_id, _name='vybrany_postup')
    return dict(poptavka=poptavka, polozky=polozky, postup=select_postup)

@auth.requires_signature()
def edithdr():
    poptavka = db(db.poptavka.id==request.args[0]).select().first()
    db.poptavka.zakaznik_id.readable = False
    db.poptavka.zakaznik_id.writable = False
    db.poptavka.vydal_id.readable = False
    db.poptavka.zapsano_dne.readable = False
    db.poptavka.vyzvednuto.readable = False
    db.poptavka.vyzvednuto.writable = False
    if poptavka.stav!='p' and not poptavka.cast_ne:
        db.poptavka.cast_ne.readable = False
        db.poptavka.cast_ne.writable = False
    return dict(form=crud.update(db.poptavka, request.args[0],
            URL('edit', args=request.args[0], user_signature=True)))

@auth.requires_signature()
def smaz():
    polozky = db(db.polozka.poptavka_id==request.args[0]).select(db.polozka.id)
    for polozka in polozky:
        db(db.prace.polozka_id==polozka.id).delete()
    db(db.prace.poptavka_id==request.args[0]).delete() # duplicitní, ale proč ne
    db(db.polozka.poptavka_id==request.args[0]).delete()
    db(db.poptavka.id==request.args[0]).delete()
    redirect(URL('vse'))

@auth.requires_signature()
def foto_show():
    fotos = db((db.polozka.poptavka_id==request.args[0]) &
                (db.polozka.foto>0)).select(
                db.polozka.foto).as_list()
    fotos = [item['foto'] for item in fotos]
    response.view = 'polozky/foto_show.html'
    return dict(fotos=fotos)
