# coding: utf8

def index():
    '''přidá potřebné firmy,
    není-li v seznamu uživatelů žádný Admin, přidá jako admina prvního uživatele'''
    response.view = 'default/msg.html'
    firmy = (('Obrázkárna','O'), ('Rámy-Pasparty','RP'), ('Fotonova','F'),)
    for firma in firmy:
        if not db(db.firma.jmeno==firma[0]).select().first():
            db.firma.insert(jmeno=firma[0], obprefix=firma[1])

    if not db(db.auth_group.role=='Admin').select().first():
        db.auth_group.insert(role='Admin')

    admin_group_id = db(db.auth_group.role=='Admin').select().first().id
    if not db(db.auth_membership.group_id==admin_group_id).select().first():
        any_user = db().select(db.auth_user.ALL).first()
        if any_user:
            any_user.update_record(registration_key='')
            db.auth_membership.insert(user_id=any_user.id, group_id=admin_group_id)
            return dict(msg=T('%s je nyní Admin') % any_user.username)
        else:
            return dict(msg=
                T('Použij [Přihlásit se], zaregistruj prvního uživatele, a opakuj uzivatele/priprav'))
    return dict(msg=
     T('Mezi uživateli už je Admin. Nemůže-li se přihlásit a roli admina nutně potřebujete, kontaktujte podporu.'))
