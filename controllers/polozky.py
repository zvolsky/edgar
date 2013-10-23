# coding: utf8

#from gluon.debug import dbg
#dbg.set_trace()

@auth.requires_signature()
def pridej():
    postup_id = request.args[1]!='x' and request.args[1] or None 
    form, map_fld_cinnost, postup, prvku_masky, maska = __factory(1, postup_id)
    form.vars.poptavka_id = request.args[0]
    if form.validate(session=None, formname='polozky'):
        id = db.polozka.insert(
                poptavka_id = request.args[0],
                postup_id = postup_id,
                ks = form.vars.ks, 
                popis = form.vars.popis,
                sirka = form.vars.sirka,
                vyska = form.vars.vyska,
                horni = form.vars.horni,
                pravy = form.vars.pravy,
                dolni = form.vars.dolni,
                levy = form.vars.levy,
                zatim_ne = form.vars.zatim_ne,
                poznamka = form.vars.poznamka)
        __zapis_prace(form, id, map_fld_cinnost)
        __pocet_polozek(request.args[0])
                        # aktualizace redundantního údaje poptavka.polozek_
        redirect(URL('poptavky', 'edit', args=request.args[0],
                user_signature=True))
    response.view = 'polozky/edit.html'
    return dict(form=form, postup=postup, prvku_masky=prvku_masky, maska=maska)

@auth.requires_signature()
def edit():
    polozka = db(db.polozka.id==request.args[1]).select().first()
    dict_polozka = polozka.as_dict()
    id = dict_polozka['id']
    form, map_fld_cinnost, postup, prvku_masky, maska = \
                                        __factory(0, polozka.postup_id)
        # map_fld_cinnost je dict: klíč=cinnost.id, hodnota je list, viz níže
    prace = db(db.prace.polozka_id==request.args[1]).select(
            db.prace.ALL, db.typprace.cinnost_id,
            left=db.typprace.on(db.prace.typprace_id==db.typprace.id))
    for item in dict_polozka.items():
        form.vars[item[0]] = item[1]
    for prace1 in prace:
        if prace1.typprace.cinnost_id:
            # map_fld_cinnost je dict: klíč=cinnost.id, hodnota je list
                #  význam hodnoty:  [0] index jména proměnné
                #                   [1] množství
                #                   [2] typprace.id
            dict_hodnota = map_fld_cinnost[prace1.typprace.cinnost_id] 
            poradi = dict_hodnota[0]
            form.vars['mn%s'%poradi] = dict_hodnota[1] = prace1.prace.mnozstvi
            form.vars['pm%s'%poradi] = dict_hodnota[2] = \
                                                    prace1.prace.typprace_id

    if form.validate(session=None, formname='polozky'):
        polozka.update_record(**dict(form.vars))
        __zapis_prace(form, id, map_fld_cinnost)
        __poptavka_redundantni(request.args[0])
                    # aktualizovat redundantní údaje poptávky
        redirect(URL('poptavky', 'edit', args=request.args[0],
                user_signature=True))
    return dict(form=form, postup=postup, prvku_masky=prvku_masky, maska=maska)

def __zapis_prace(form, polozka_id, map_fld_cinnost):
    zmena = False   # je změna?
    for cinnost in map_fld_cinnost:
                #  význam hodnoty:  [0] index jména proměnné
                #                   [1] množství
                #                   [2] typprace.id
        dict_hodnota = map_fld_cinnost[cinnost]
        poradi = dict_hodnota[0]
        if form.vars['mn%s'%poradi]!=dict_hodnota[1] or \
                    form.vars['pm%s'%poradi]!=str(dict_hodnota[2]):
                    # změnilo se množství nebo typ práce pro tuto činnost
            zmena = True
            break
    if zmena:
        # zatím to řeším brutální silou - smažu vše a znovu naplním:
        db(db.prace.polozka_id==polozka_id).delete()
        polozka = db(db.polozka.id==polozka_id).select().first()
        cena_polozky = 0    # polozka.cena_1ks
        for cinnost in map_fld_cinnost:
                    #  význam hodnoty:  [0] index jména proměnné
                    #                   [1] množství
                    #                   [2] typprace.id
            dict_hodnota = map_fld_cinnost[cinnost]
            poradi = dict_hodnota[0]
            mnozstvi = form.vars['mn%s'%poradi]
            if mnozstvi>0:
                typprace_id = form.vars['pm%s'%poradi]
                if typprace_id:
                    poptavka_id = db(db.polozka.id==polozka_id).select(
                            db.polozka.poptavka_id).first().poptavka_id 
                    typprace = db(db.typprace.id==typprace_id).select(
                            db.typprace.cena, db.typprace.cena2).first()
                    cena = typprace.cena*mnozstvi
                    cena2 = typprace.cena2*2*(polozka.vyska+polozka.sirka)
                    cena_polozky += cena + cena2
                    db.prace.insert(
                            poptavka_id=poptavka_id,
                            polozka_id=polozka_id,
                            typprace_id=typprace_id,
                            cinnost_id=cinnost,
                            mnozstvi=mnozstvi,
                            cena_1j=typprace.cena,
                            cena2_1j=typprace.cena2,
                            cena=cena,
                            cena2=cena2
                            )
        if db.polozka.cena_1ks!=cena_polozky: 
            polozka.update_record(cena_1ks=cena_polozky,
                        cena=polozka.ks*cena_polozky)
                # pole pro stanovení ceny: 
                    # polozka: ks, cena_1ks, cena
                    # prace: mnozstvi, cena_1j, cena, cena2_1j, cena2
                    # typprace: cena, cena2

@auth.requires_signature()
def kopie():
    polozka = db(db.polozka.id==request.args[1]).select().first()
    del polozka.id
    id = db.polozka.insert(**polozka.as_dict())
    prace = db(db.prace.polozka_id==request.args[1]).select()
    for prace1 in prace:
        del prace1.id
        prace1.polozka_id = id
        db.prace.insert(**prace1.as_dict())
    __pocet_polozek(request.args[0]) # aktualizace redundantního údaje
    redirect(URL('edit', args=(request.args[0], id), user_signature=True))

def __factory(is_new, postup_id=None):
    '''připraví SQLFORM.factory,
    postup.id==None:pro všechny práce; postup.id:pro práce tohoto postupu
    is_new = default množství při editaci (volat: 1 pro přidání, 0 edit)
    '''
    postup = db(db.postup.id==postup_id).select(
                db.postup.ALL).first()
    cinnosti_query = postup.hardcoded_as!='*' and postup_id and \
            (db.cinnost.id==db.krok.cinnost_id)&(db.krok.postup_id==postup_id) \
            or None
    
    cinnosti = db(cinnosti_query).select(db.cinnost.ALL)
    typy_praci = db().select(
            db.typprace.id, db.typprace.nazev, db.typprace.cinnost_id,
            orderby=db.typprace.cinnost_id)

    flds_kroky = []
    map_fld_cinnost = {}
    for poradi, cinnost in enumerate(cinnosti):
        vyber = typy_praci.find(lambda row: row.cinnost_id==cinnost.id)
        show_mnozstvi = True if cinnost.mn_vyznam else False
        #show_mnozstvi = True
            # True if..else False: Zobrazí se jen při vyplnění cinnost.mn_vyznam
            # True: není-li cinnost.mn_vyznam vyplněno, zobrazí se "Množství"   
        flds_kroky.extend([
                Field('mn%s'%poradi, 'double', default=is_new,
                        label=cinnost.mn_vyznam or T("Množství"),
                        readable=show_mnozstvi, writable=show_mnozstvi),
                Field('pm%s'%poradi, 'integer', label=cinnost.nazev,
                        comment=cinnost.cmt,
                        requires=IS_EMPTY_OR(IS_IN_SET(
                                    [(item.id, item.nazev) for item in vyber]))
                        )
                        # label=cinnost.lbl /zakomentováním asi zbytečný sloupec
                ])
        map_fld_cinnost[cinnost.id] = [poradi, 1.0, '']
                    
    db.polozka.poptavka_id.readable = False
    db.polozka.cena_1ks.readable = False
    db.polozka.cena.readable = False
    db.polozka.vyzvednuto.readable = db.polozka.vyzvednuto.writable = False
    db.polozka.foto.readable = db.polozka.foto.writable = False

    __hard_maska(postup)
            #__set_maska(postup, flds_kroky.extend(db.polozka))
            # nelze db.polozka.extend(flds_kroky), protože db.polozka je Table          

    #maska_flds = postup.maska_flds.replace(' ','').split(',')
    maska_flds = postup.maska_flds.replace(',',' ').replace('(',' ').replace(
                                            ')',' ').split()
       # nevím, jestli to lze lépe; umím ještě leda:
        # import string
        # string.translate("(ks,bz)lz,",string.maketrans(',()','   ')).split()
    prvku_masky = len(maska_flds)
    
    factory_flds = []
    # napřed zařadíme pole masky v pořadí, jak je v masce definujeme
    #   bohužel to umím jen s vnořením cyklů; ale snad to bude dost rychlé
    for fldm in maska_flds:
        for fldd in db.polozka:
            if fldd.name==fldm:
                factory_flds.append(fldd)
                break
        else: 
          for fldd in flds_kroky:
              if fldd.name==fldm:
                  factory_flds.append(fldd)
                  break
    # pak doplníme všechna pole, která v masce nejsou
    for fldd in db.polozka:
        if not fldd.name in maska_flds: 
            factory_flds.append(fldd) 
    for fldd in flds_kroky:
        if not fldd.name in maska_flds: 
            factory_flds.append(fldd) 

    form = SQLFORM.factory(*factory_flds)

    if prvku_masky>0:
        maska = postup.maska
        
        prvky = []
        for pole in form[0].components[:prvku_masky]:
            prvky.extend((pole[0][0], pole[1][0])) #form[0].components[0][1][0]
        prvky = __hardcoded(CAT(prvky), postup.hardcoded_as)
        maska = XML(maska % tuple(prvky))
    else:
        maska = ''

    return form, map_fld_cinnost, postup, prvku_masky, maska

    '''
    #form = SQLFORM.factory(db.polozka, *flds)
    #form[0].insert(0, DIV(_id='maska'))
    #form[0].append(form[0].components.pop(1))
    #del form[0][0]
    #form[0].insert(0, DIV(XML('<table><tr id="no_table_ks__row"><td class="w2p_fl"><label for="no_table_ks" id="no_table_ks__label">Ks: </label></td><td class="w2p_fw"><input class="integer" id="no_table_ks" name="ks" type="text" value="1" /></td><td class="w2p_fc">shodných kusů</td></tr></table>'), _id='maska'))
    '''

@auth.requires_signature()
def foto():
    #import os
    #db.polozka.foto.uploadfolder = os.path.join(
    #            request.folder,
    #            'uploads',
    #            db(db.poptavka.id==request.args[0]).select(
    #                db.poptavka.cislo).first().cislo)
    form = SQLFORM(db.polozka, request.args[1], showid=False, fields=['foto'],
                upload=URL('default', 'download'))
    if form.process().accepted:
        __poptavka_foto(request.args[0])        
        redirect(URL(
                'poptavky', 'edit', args=request.args[0], user_signature=True))
    return dict(form=form)

@auth.requires_signature()
def foto_show():
    foto = db(db.polozka.id==request.args[1]).select(
                db.polozka.foto).first().foto
    return dict(fotos=[foto])

@auth.requires_signature()
def smaz():
    db(db.polozka.id==request.args[1]).delete()
    db(db.prace.polozka_id==request.args[1]).delete() # nezabere-li db integrita
    __pocet_polozek(request.args[0])
            # aktualizace redundantního údaje poptavka.polozek_
    __poptavka_foto(request.args[0])        
            # aktualizace redundantního údaje poptavka.foto_
    redirect(URL('poptavky', 'edit', args=request.args[0], user_signature=True))

def __pocet_polozek(poptavka_id):
    sum = db.polozka.ks.sum()
    pocet = db(db.polozka.poptavka_id==poptavka_id).select(sum).first()[sum]
    #pocet = db(db.polozka.poptavka_id==poptavka_id).count()
    db(db.poptavka.id==poptavka_id).update(polozek_=pocet)
    __poptavka_redundantni(poptavka_id)

def __poptavka_redundantni(poptavka_id):
    cast_ne = db((db.polozka.poptavka_id==poptavka_id)&
                (db.polozka.zatim_ne==True)).count()!=0
    ceny_polozek = db(db.polozka.poptavka_id==poptavka_id).select(
                db.polozka.cena)
    cena_poptavky = 0
    for polozka in ceny_polozek:
        cena_poptavky += polozka.cena
    db(db.poptavka.id==poptavka_id).update(cast_ne=cast_ne,
            cena=cena_poptavky,
            cena_zakaznik=cena_zakaznik(poptavka_id, cena_poptavky))

def __poptavka_foto(poptavka_id):
    ma_byt = db((db.polozka.poptavka_id==poptavka_id) &
            (db.polozka.foto>0)).count()>0
    je = db(db.poptavka.id==poptavka_id).select(
            db.poptavka.foto_).first().foto_
    if ma_byt!=je:
        db(db.poptavka.id==poptavka_id).update(foto_=ma_byt)

#def __set_maska(postup):
def __hard_maska(postup):
    if postup.hardcoded_as:
        if postup.hardcoded_as=='*':
            maska = ('<div>%s%s %s%s</div> <div>%s%s %s%s</div>'
                    '<div>%s%s %s%s %s%s %s%s</div>'
                    '<div>%s%s</div><div>%s%s</div>'
                    '<div>%s%s</div><div>%s%s</div>'
                    '<div>%s%s</div><div>%s%s</div>'
                    '<div>%s%s</div><div>%s%s</div>'
                    '<div>%s%s</div><div>%s%s</div>'
                    '<div>%s%s</div><div>%s%s</div>'
                    '<div>%s%s</div><div>%s%s</div>'
                    '<div>%s%s</div><div>%s%s</div>'
                    '<div>%s%s</div><div>%s%s</div>'
                    '<div>%s%s</div><div>%s%s</div>'
                    '<div>%s%s</div><div>%s%s</div>'
                    '<div>%s%s</div><div>%s%s</div>'
                    '<div>%s%s</div><div>%s%s</div>'
                    '<div>%s%s</div>'
                    '<div>%s%s</div>')
            flds = ('ks, popis, sirka, vyska, '
                    'horni, pravy, dolni, levy, '
                    'pm0,pm1,pm2,pm3,pm4,pm5,pm6,pm7,pm8,pm9,pm10,pm11, '
                    'pm12,pm13,pm14,pm15,pm16,pm17,pm18,pm19,pm20,pm21,pm22, '
                    'pm23,pm24,pm25,pm26, ' 
                    'poznamka')
        elif postup.hardcoded_as=='o':
            maska = ('<div>%s%s %s%s</div> <div>%s%s %s%s</div> '
                    '<div>%s%s %s%s %s%s %s%s</div> '
                    '<div class="left">%s%s</div> '
                    '<div class="left">%s%s</div> '
                    '<div>%s%s</div> <div>%s%s</div> '
                    '<div>%s%s</div>')
            flds = ('ks, popis, sirka, vyska, '
                    'horni, pravy, dolni, levy, '
                    'pm0, pm1, pm2, pm3, poznamka')
        elif postup.hardcoded_as=='r':
            maska = ('<div>%s%s %s%s</div> <div>%s%s %s%s</div>'
                    '<div>%s%s %s%s %s%s %s%s</div>'
                    '<div>%s%s</div><div>%s%s</div>'
                    '<div>%s%s</div><div>%s%s</div>'
                    '<div>%s%s</div><div>%s%s</div>'
                    '<div>%s%s</div><div>%s%s</div>'
                    '<div>%s%s</div><div>%s%s</div>'
                    '<div>%s%s</div><div>%s%s</div>'
                    '<div>%s%s</div></table>')
            flds = ('ks, popis, sirka, vyska, '
                    'horni, pravy, dolni, levy, '
                    'pm0,pm1,pm2,pm3,pm4,pm5,pm6,pm7,pm8,pm9,pm10,pm11, ' 
                    'poznamka')
        elif postup.hardcoded_as=='f':
            maska = ('<div>%s%s %s%s</div> <div>%s%s %s%s</div>'
                    '<div>%s%s %s%s %s%s %s%s</div>'
                    '<div>%s%s</div><div>%s%s</div>'
                    '<div>%s%s</div><div>%s%s</div>'
                    '<div>%s%s</div><div>%s%s</div>'
                    '<div>%s%s</div><div>%s%s</div>'
                    '<div>%s%s</div><div>%s%s</div>'
                    '<div>%s%s</div>'
                    '<div>%s%s</div>')
            flds = ('ks, popis, sirka, vyska, '
                    'horni, pravy, dolni, levy, '
                    'pm0,pm1,pm2,pm3,pm4,pm5,pm6,pm7,pm8,pm9,pm10, ' 
                    'poznamka')
        if flds!=postup.maska_flds:
            postup.update_record(maska_flds=flds)
        if maska!=postup.maska:
            postup.update_record(maska=maska)
    '''
    elif postup.maska_flds:
        flds = postup.maska_flds
    else:
        flds = ''
        prvku_masky = 0

    if flds:
        #prvku_masky = flds.count(',')+1 if flds else 0   # před povolením (,)
        prvku_masky = len(flds.replace(',','').replace('(','').replace(')',''
                        ).split())
         # nevím, jestli to lze lépe; umím ještě leda:
          # import string
          # string.translate("(ks,bz)lz,",string.maketrans(',()','   ')).split()

    return postup, prvku_masky
    '''

def __hardcoded(maska, hardcoded_as):
    if hardcoded_as:
        maska.element('input#no_table_sirka')['_placeholder'] = T('šířka')
        maska.element('input#no_table_vyska')['_placeholder'] = T('výška')
        maska.element('input#no_table_horni')['_placeholder'] = T('horní')
        maska.element('input#no_table_pravy')['_placeholder'] = T('pravý')
        maska.element('input#no_table_dolni')['_placeholder'] = T('dolní')
        maska.element('input#no_table_levy')['_placeholder'] = T('levý')
        maska.element('label#no_table_sirka__label')[0] = T('Rozměry [mm]')
        maska.element('label#no_table_vyska__label')[0] = 'x'
        maska.element('label#no_table_vyska__label')[1] = ''  # -- ':'
        maska.element('label#no_table_horni__label')[0] = T('Okraje [mm]')
        maska.element('label#no_table_pravy__label')[0] = ''  # -- label
        maska.element('label#no_table_pravy__label')[1] = ''  # -- ':'
        maska.element('label#no_table_dolni__label')[0] = ''  # -- label
        maska.element('label#no_table_dolni__label')[1] = ''  # -- ':'
        maska.element('label#no_table_levy__label')[0] = ''  # -- label
        maska.element('label#no_table_levy__label')[1] = ''  # -- ':'
        # maska.element('label#no_table_zatim_ne__label')[1] = ''  # -- ':'
    return maska
