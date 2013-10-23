# coding: utf8

def index():
    redirect(URL('seznam'))

@auth.requires_membership('Admin')
def seznam():
    uzivatele=db().select(db.auth_user.ALL, db.firma.id, db.firma.jmeno,
                left=db.firma.on(db.auth_user.firma_id==db.firma.id),
                orderby=db.auth_user.last_name)

    radmini=db((db.auth_membership.group_id==db.auth_group.id)
                & (db.auth_group.role=='Admin')).select(
                db.auth_membership.user_id)
    admini=[]
    for admin in radmini:
        admini+=[admin.user_id]

    return dict(uzivatele=uzivatele, admini=admini)

@auth.requires_membership('Admin')
def pridej():
    response.view = 'uzivatele/edit.html'
    return dict(form=crud.create(db.auth_user, URL('seznam')))

@auth.requires_membership('Admin')
@auth.requires_signature()
def edit():
    return dict(form=crud.update(db.auth_user, request.args(0), URL('seznam')))

@auth.requires_membership('Admin')
@auth.requires_signature()
def blokace():
    row = db(db.auth_user.id==request.args[0]).select().first()
    row.update_record(registration_key=('' if row.registration_key else 'blocked'))
    redirect(URL('seznam'))

@auth.requires_membership('Admin')
@auth.requires_signature()
def admin_dej():
    admin_group_id = db(db.auth_group.role=='Admin').select().first().id
    db.auth_membership.insert(user_id=request.args[0], group_id=admin_group_id)
    redirect(URL('seznam'))

@auth.requires_membership('Admin')
@auth.requires_signature()
def admin_vezmi():
    admin_group_id = db(db.auth_group.role=='Admin').select().first().id
    db((db.auth_membership.user_id==request.args[0]) & (db.auth_membership.group_id==admin_group_id)).delete()
    redirect(URL('seznam'))

@auth.requires_membership('Admin')
@auth.requires_signature()
def smaz():
    db(db.auth_user.id==request.args[0]).delete()
    redirect(URL('seznam'))
