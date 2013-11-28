# coding: utf8

@auth.requires_login()
def nova():
    postup_id = __vybrany_postup()
    polozka_id = db.polozka.insert(
          postup_id=postup_id,
          )
    kroky = db(db.krok.postup_id==postup_id).select(
          db.krok.ALL, db.cinnost.ALL,
          left=db.cinnost.on(db.cinnost.id==db.krok.cinnost_id),
          orderby=db.krok.poradi
          )
    for krok in kroky:
        predvoleny_typ = db((db.typprace.cinnost_id==krok.cinnost.id)&
                        (db.typprace.hlavni==True)).select().first()
        prace_id = db.prace.insert(
              polozka_id=polozka_id,
              cinnost_id=krok.cinnost.id
              )
        if predvoleny_typ:
            db.prace[prace_id] = dict(
                  typprace_id=predvoleny_typ.id,
                  info=('%s %s %s'%(predvoleny_typ.nazev, predvoleny_typ.cislo,
                        predvoleny_typ.tovarni)).strip(),
                  cena_1j=predvoleny_typ.cena,
                  cena2_1j=predvoleny_typ.cena2
                  )
    redirect(URL('polozka', args=polozka_id))

def polozka():
    if not len(request.args):
        session.flash = "požadovaná položka poptávky nebyla nalezena"
        redirect(URL('default', 'index'))
    
    polozka = db.polozka[request.args[0]]
    prace = db(db.prace.polozka_id==polozka.id).select(
            db.prace.ALL, db.cinnost.nazev, db.cinnost.chybi, db.typprace.ALL,
            left=(db.cinnost.on(db.cinnost.id==db.prace.cinnost_id),
                db.typprace.on(db.typprace.id==db.prace.typprace_id))
            )
    typyprace = db(db.typprace).select()

    controls = [
        TR(
          TD(DIV(('%s x'%polozka.ks if polozka.ks>0 else 'počet'), _class="shrnuti", _id='s_pocet')),
          TD(DIV(
          INPUT(_name='ks', _value=polozka.ks, _class="integer", _id='ks'),
            _class="zadani", _id='pocet'))),
        TR(
          TD(DIV(('%s x %s cm'%(polozka.sirka or '?', polozka.vyska or '?')
              if (polozka.sirka or polozka.vyska) else 'rozměry'), _class="shrnuti", _id='s_rozmery')),
          TD(DIV(
            INPUT(_name='sirka', _value=polozka.sirka, _class='rozmer decimal', _id='sirka'),
            ' x ',
            INPUT(_name='vyska', _value=polozka.vyska, _class='rozmer decimal', _id='vyska'),
            _class="zadani", _id='rozmery'))),
        TR(
          TD(DIV(('%s< \'%s >%s _%s'%(polozka.levy, polozka.horni,
                                        polozka.pravy, polozka.dolni)
              if (polozka.levy or polozka.horni or polozka.pravy or
                  polozka.dolni) else 'okraje'), _class="shrnuti", _id='s_okraje')),
          TD(DIV(
            INPUT(_name='levy', _value=polozka.levy, _class='okraj decimal', _id='levy'),
            INPUT(_name='horni', _value=polozka.horni, _class='okraj decimal', _id='horni'),
            INPUT(_name='pravy', _value=polozka.pravy, _class='okraj decimal', _id='pravy'),
            INPUT(_name='dolni', _value=polozka.dolni, _class='okraj decimal', _id='dolni'),
            _class="zadani", _id='okraje')))
        ]
    for prace1 in prace:
        uz_vybrano = prace1.prace.typprace_id and prace1.typprace.nazev
        selected = prace1.prace.typprace_id if uz_vybrano else 0
        options = [OPTION(prace1.cinnost.chybi, _value=0, _cena=0)]
        for typprace in typyprace.find(
                        lambda row: row.cinnost_id==prace1.prace.cinnost_id):
            options.append(OPTION(typprace.nazev, _value=typprace.id,
                          _cena=typprace.cena))
            if not uz_vybrano and typprace.hlavni:
                selected = typprace.id 
        controls += [TR(
              TD(DIV('%s %s'%(prace1.cinnost.nazev.split('[')[0].strip(), 
                        prace1.typprace.nazev if uz_vybrano else ''),
                        _class="shrnuti")),
              TD(DIV(
                SELECT(*options, _name='p%s'%prace1.prace.id, value=selected,
                      _class="typprace", _id='p%s'%prace1.prace.id),
                _class="zadani"))),
              ]
    controls = [TABLE(*controls)]
    controls.append(INPUT(_type='submit'))
    form = FORM(*controls, _class="polozka")
    if form.process().accepted:
        polozka.update_record(
                ks=form.vars.ks,
                sirka=form.vars.sirka,
                vyska=form.vars.vyska,
                levy=form.vars.levy,
                horni=form.vars.horni,
                pravy=form.vars.pravy,
                dolni=form.vars.dolni,
                )
        for prace1 in prace:
            hodnota = form.vars.get('p%s'%prace1.prace.id)
            prace1.prace.update_record(typprace_id=hodnota or None) 
        redirect(URL('default', 'index'))
    return dict(form=form, prace=prace, polozka=polozka)

def __vybrany_postup(): 
    if not session.postup_id:
        uzivatel = db.auth_user[auth.user_id]
        if uzivatel.postup_id:
            session.postup_id = uzivatel.postup_id
        elif uzivatel.firma_id:
            firma = db.firma[uzivatel.firma_id]
            if firma.postup_id: 
                session.postup_id = firma.postup_id
        if not session.postup_id:
            hlavni = db(db.postup.hlavni==True).select().first()
            if not hlavni:
                hlavni = db(db.postup).select().first()
            session.postup_id = hlavni.id
    return session.postup_id        