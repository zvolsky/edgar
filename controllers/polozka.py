# coding: utf8

@auth.requires_login()
def nova():
    postup_id = __vybrany_postup()
    polozka_id = db.polozka.insert()
    ...............................................
    redirect(URL('polozka'), args=polozka_id)

def polozka():
    if not len(request.args):
        session.flash = "požadovaná položka poptávky nebyla nalezena"
        redirect(URL('default', 'index'))
    polozka = db.polozka[request.args[0]]
    prace = db(db.prace.polozka_id==polozka.id).select()
    return dict(polozka=polozka, prace=prace)

def __vybrany_postup(): 
    if not session.postup_id:
        uzivatel = db.auth_user[auth.user_id]
        if uzivatel.postup_id:
            session.postup_id = uzivatel.postup_id
        elif uzivatel.firma_id:
            firma = dbfirma[user.firma_id]
            if firma.postup_id: 
                session.postup_id = firma.postup_id
        if not session.postup_id:
            hlavni = db(db.postup.hlavni==True).select().first()
            if not hlavni:
                hlavni = db(db.postup).select().first()
            session.postup_id = hlavni.id
            