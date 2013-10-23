# coding: utf8

def index():
    redirect(URL('seznam'))

@auth.requires_login()
def seznam():
    reset_session('zakaznik')
    pocet, page, per_page, limitby = priprav_strankovani()
                            # pozor, nastavuje session.najdi
    if session.najdi:
        query = db.zakaznik.jmeno.contains(session.najdi
                    ) | db.zakaznik.telefon.contains(session.najdi)
    else:
        query = db.zakaznik
    pocet = dourci_pocet(pocet, query)

    trideni = dict(j=db.zakaznik.jmeno, t=db.zakaznik.telefon) # možná pořadí
    poradi = len(request.args) and request.args[0] or 'j'      # aktivní pořadí
    
    zakaznici = db(query).select(db.zakaznik.ALL,
            orderby=trideni[poradi] if poradi.islower()
                    else ~trideni[poradi.lower()],
            limitby=limitby)

    return dict(filtr=filtr('j'),
            pocet=zobraz_pocet(pocet),
            zakaznici=zakaznici,
            strankovani=strankovani(len(zakaznici), poradi, page, per_page),
            per_page=per_page)

@auth.requires_signature()
def edit():
    return dict(form=crud.update(db.zakaznik, request.args(0),
            len(request.args)>1 and request.args[1]=='np'
                        and URL('zadani','poptavka',user_signature=True)
            or len(request.args)>1 and request.args[1]=='ep'
                        and URL('poptavky','edit',args=request.args[2],
                            user_signature=True) 
            or URL('seznam', args=request.args[1:])))

@auth.requires_login()
def pridej():
    response.view = 'zakaznici/edit.html'
    form = SQLFORM(db.zakaznik)
    if form.process().accepted:
        if len(request.args)>0 and request.args[0]=='np':
            session.zakaznik_id = form.vars.id
            redirect(URL('zadani', 'poptavka', user_signature=True))
        else:
            redirect(URL('seznam', args=request.args))
    return dict(form=form)

@auth.requires_signature()
def smaz():
    # zde ještě musí být kontrola, zda nemá zakázky
    db(db.zakaznik.id==request.args[0]).delete()
    session.pocet -= 1
    redirect(URL('seznam', args=request.args[1:]))

'''
def seznam():
    zakaznici = db().select(db.zakaznik.ALL, orderby=db.zakaznik.jmeno)
    return dict(pocet=len(zakaznici), zakaznici=zakaznici)

def seznam2():
    grid = SQLFORM.grid(db.zakaznik,
            fields = [db.zakaznik.jmeno, db.zakaznik.telefon, db.zakaznik.koeficient, db.zakaznik.staly],
            links = [dict(header='Změnit',body=lambda row: A(IMG(_src=URL('static','images/edit.png'))))],
            search_widget=None,
            csv = False,
            showbuttontext = False,
            )
    #grid = SQLFORM.smartgrid(db.zakaznik, linked_tables=['poptavka'])
    return locals()
'''
