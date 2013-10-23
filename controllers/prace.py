# coding: utf8

def index():
    redirect(URL('seznam'))

@auth.requires_login()
def seznam():
    from datetime import date
    prace=db((db.polozka.zatim_ne==False)&(
                db.poptavka.stav.belongs(('v', 'k')))
            ).select(db.prace.ALL, db.polozka.popis, db.polozka.ks,
                  db.polozka.sirka, db.polozka.vyska,
                  db.poptavka.id, db.poptavka.popis, db.poptavka.cislo,
                  db.poptavka.ma_byt_dne, db.typprace.nazev, db.cinnost.nazev,
                left=(db.polozka.on(db.prace.polozka_id==db.polozka.id),
                    db.poptavka.on(db.polozka.poptavka_id==db.poptavka.id),
                    db.typprace.on(db.prace.typprace_id==db.typprace.id),
                    db.cinnost.on(db.typprace.cinnost_id==db.cinnost.id)),
                orderby=db.poptavka.ma_byt_dne)
    return dict(prace=prace, date=date)

@auth.requires_signature()
def dokonceni():
    prace1 = db(db.prace.id==request.args[0]).select(db.prace.ALL).first()
    prace1.update_record(dokonceno=None if prace1.dokonceno else datetime.now())
    redirect(URL('seznam'))
