# coding: utf8

# import textwrap - v polozka()

@auth.requires_login()
def nova():
    postup_id = request.args(0) or session.postup_id
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

@auth.requires_login()
def polozka():
    import textwrap
    if not len(request.args):
        session.flash = "požadovaná položka poptávky nebyla nalezena"
        redirect(URL('default', 'index'))
    
    polozka = db.polozka[request.args[0]]
    prace = db(db.prace.polozka_id==polozka.id).select(
            db.prace.ALL, db.cinnost.nazev, db.cinnost.chybi, db.typprace.ALL,
            left=(db.cinnost.on(db.cinnost.id==db.prace.cinnost_id),
                db.typprace.on(db.typprace.id==db.prace.typprace_id))
            )
    typyprace = db(db.typprace).select()  # výběr typů prací pro SELECT-OPTION 
    plus_defs = db(db.plus_def).select()  # pole navíc pro jednotlivé práce

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
    nactene_plus = {}
    inputy_plus = []  # pro zpětný zápis po .accepted
    for prace1 in prace:
        # SELECT
        uz_vybrano = prace1.prace.typprace_id and prace1.typprace.nazev
        selected = prace1.prace.typprace_id if uz_vybrano else 0
        options = [OPTION(prace1.cinnost.chybi, _value=0, _cena=0)]
        for typprace in typyprace.find(
                        lambda row: row.cinnost_id==prace1.prace.cinnost_id):
            options.append(OPTION(typprace.zobrazit, _value=typprace.id,
                          _cena=typprace.cena))
            if not uz_vybrano and typprace.hlavni:
                selected = typprace.id
        controls_prace = [SELECT(*options, _name='p%s'%prace1.prace.id,
                value=selected, _class="typprace", _id='p%s'%prace1.prace.id)]

        # doplňující údaje SELECTu (resp. této prace1)
        for plus_def in plus_defs.find(
                        lambda row: row.cinnost_id==prace1.prace.cinnost_id):
            tbl = plus_def.tabulka
            input_name = 'n%s'%plus_def.id  
            if not nactene_plus.get(tbl): # ještě jsme z db nevzali
                nactene_plus[tbl] = db(
                          db.get('plus_'+tbl).polozka_id==polozka.id).select()
            old_value = nactene_plus[tbl].find(
                        lambda row: row.plus_def_id==plus_def.id
                                  and row.prace_id==prace1.prace.id)
            if len(old_value):            # hodnota už je vyplněna
                tbl_id = old_value[0].id
                old_value = old_value[0].hodnota
            else:                         # není, tak najít defaultní
                tbl_id = 0
                if plus_def.iddefault:
                    old_value = db.get('plus_'+tbl)[plus_def.iddefault].hodnota
                else:
                    old_value = None  
            inputy_plus.append((input_name, tbl, tbl_id, prace1.prace.id,
                        plus_def.id, old_value)) # pro zpětný zápis po .accepted
            controls_prace.append(plus_def.nazev)
            controls_prace.append(
                INPUT(_name=input_name, _value=old_value,
                      _class=plus_def.css_class, _id='id%s'%plus_def.id))
        
        # poznámka
        poznamka = textwrap.wrap(prace1.prace.poznamka
                    or TFu('připiš poznámku'), 60)
        controls_prace.append(A(
                poznamka[0] + (len(poznamka)>1 and ' ...' or ''),
                _href="#modal%s" % prace1.prace.id,
                _id="apozn%s" % prace1.prace.id,
                _class='modalLink %s' %
                  ('poznamka' if prace1.prace.poznamka else 'pozn')))  
        controls_prace.append(DIV(
                TEXTAREA(prace1.prace.poznamka or '',
                    _name='pozn%s'%prace1.prace.id,
                    _class="text modalPozn",
                    _id='pozn%s'%prace1.prace.id),
                _class="modal", _id="modal%s" % prace1.prace.id,
                     _focus="#pozn%s" % prace1.prace.id))
        '''    
                    <a class="modalLink" href="#">Click Me
                    <div class="overlay"></div>
                    <div class="modal">
                    <a href="#" class="closeBtn">Close Me</a>
                    <!-- content here -->
                    </div>
        '''
                
        controls += [TR(
              TD(DIV('%s %s'%(prace1.cinnost.nazev.split('[')[0].strip(), 
                        prace1.typprace.nazev if uz_vybrano else ''),
                        _class="shrnuti")),
              TD(DIV(*controls_prace, _class="zadani"))
              ),]

        '''
        db.define_table('plus_def',        # výčet ůdajů navíc určité činnosti
                Field('cinnost_id', db.cinnost, label=TFu('Činnost'),
                        comment=TFu("práce")),
                Field('poradi', 'integer', default=999999, label=TFu('Pořadí v postupu'),
                        comment=TFu("číslovat např. po 100 pro pozdější možné vložení")),
                Field('nazev', label=TFu('Název (caption) údaje')),
                Field('typ', length=20, default='string', label=TFu('Typ')),
                Field('tabulka', length=12, default='string', label=TFu('Tabulka')),
                Field('css_class', length=12, default='string', label=TFu('CSS class')),
                Field('iddefault', 'integer', label=TFu('ID defaultní hodnoty v "tabulka"')),
                Field('volby', label=TFu('(pro integer) Volby selectu (oddělit |)')),
                format='%(nazev)s',
                )
        # v plus_def.iddefault může být uvedeno ID záznamu v plus_<tabulka>
        #   takový záznam s defaultní hodnotou je potřeba vytvořit ručně (prace_id bude None) 
        def def_plus(db, tabulka, typ):
            tbl = 'plus_'+tabulka 
            if not db.has_key(tbl):
                db.define_table(tbl,
                    Field('polozka_id', db.prace, label=TFu('Položka, ke které údaj patří')),
                    Field('prace_id', db.prace, label=TFu('Práce, ke které údaj patří')),
                    Field('plus_def_id', db.plus_def, label=TFu('Který údaj')),
                    Field('hodnota', typ, label=TFu('Hodnota údaje')),
                    )
        '''


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
        # SELECTy prací
        for prace1 in prace:
            hodnota = form.vars.get('p%s'%prace1.prace.id)
            prace1.prace.update_record(typprace_id=hodnota or None,
                    poznamka=form.vars.get('pozn%s'%prace1.prace.id))
        # přídavné údaje prací 
        for input_plus in inputy_plus:
            # .append((input_name,tbl,tbl.id,prace.id,plus_def.id,old_value))
            nova_hodnota = form.vars.get(input_plus[0]) 
            if input_plus[2]:   # už bylo dříve uloženo v plus tabulkách
                if nova_hodnota!=old_value: 
                    db.get('plus_'+input_plus[1])[input_plus[2]] = dict(
                                hodnota=nova_hodnota)
            else:               # první zápis do plus tabulky
                db.get('plus_'+input_plus[1])[0] = dict(
                            polozka_id=polozka.id,
                            prace_id=input_plus[3],
                            plus_def_id=input_plus[4],
                            hodnota=nova_hodnota)
        redirect(URL('default', 'index'))
    return dict(form=form, prace=prace, polozka=polozka)
        