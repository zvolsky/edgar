# coding: utf8

@auth.requires_login()
def postupy():
    postupy = db(db.postup).select()
    return dict(postupy=postupy)

def jen_zmenit():
    session.postup_id = request.args(0) or session.postup_id
    session.postup_txt = db.postup[session.postup_id].nazev
    redirect(URL('postupy'))
        