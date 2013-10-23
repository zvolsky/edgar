# coding: utf8

# chtělo by to automaticky z databáze, bohužel tak neumím zveřejněné funkce generovat
def index():
    redirect(URL('obrazkarna'))
@auth.requires_membership('Admin')
def obrazkarna():
    return seznam('O')
@auth.requires_membership('Admin')
def ramy_pasparty():
    return seznam('RP')
@auth.requires_membership('Admin')
def fotonova():
    return seznam('F')

def seznam(firma):
    response.view = "typypraci/seznam.html"
    firmy = db().select(db.firma.ALL)
    firma_id = firmy.find(lambda row: row.obprefix==firma)[0].id
    cinnosti = db(db.cinnost.firma_id==firma_id).select(db.cinnost.ALL)
    popisy = db().select(db.popis.ALL, db.vlastnost.ALL,
            left=db.vlastnost.on(db.popis.vlastnost_id==db.vlastnost.id))
    typy_praci = db(
            (db.typprace.cinnost_id==db.cinnost.id) &
                (db.cinnost.firma_id==firma_id)).select(db.typprace.ALL,
            orderby=db.typprace.cinnost_id)
    return dict(firmy=firmy, cinnosti=cinnosti, popisy=popisy, typy_praci=typy_praci)

@auth.requires_membership('Admin')
@auth.requires_signature()
def pridej():
    response.view = "typypraci/edit.html"
    hodnoty = zakazat_vlastnosti(request.args[1])
    hodnoty['form'] = crud.create(db.typprace, URL(request.args[0]),
        onvalidation=onval_ins)
    return hodnoty
def onval_ins(form):
    form.vars.cinnost_id = request.args[1]

@auth.requires_membership('Admin')
@auth.requires_signature()
def edit():
    hodnoty = zakazat_vlastnosti(request.args[1])
    hodnoty['form'] = crud.update(db.typprace, request.args[2], URL(request.args[0]))
    return hodnoty

def zakazat_vlastnosti(cinnost):
    '''volá pridej a edit pro potlačení nerelevantních vlastností'''
    nazev_cinnosti = db(db.cinnost.id==cinnost).select(db.cinnost.nazev).first().nazev
    popisy = db(db.popis.cinnost_id==cinnost).select(db.popis.vlastnost_id)
    povolene = []
    for popis in popisy:
        povolene.append(popis.vlastnost_id)
    vlastnosti = db().select(db.vlastnost.ALL)
    for vlastnost in vlastnosti:
        if not vlastnost.id in povolene:
            db.typprace.__dict__[vlastnost.strojovy].readable = False
            db.typprace.__dict__[vlastnost.strojovy].writable = False
            # místo toho by asi bylo lepší sestavit pro SQLFORM parametr 'fields'
    return dict(titulek='%s %s'%(T('položka číselníku'),nazev_cinnosti))

@auth.requires_membership('Admin')
@auth.requires_signature()
def smaz():
    db(db.typprace.id==request.args[2]).delete()
    redirect(URL(request.args[0]))

'''
<a href="http://edgar.ine.cz/typy-prace/obrazkarna#form-pridej-typ-prace-tiskovy-material" onclick="$(&#39;.novy-typ-prace form&#39;).hide();$(&#39;#tmpEditDiv&#39;).remove();$(&#39;.form-pridej-typ-prace-tiskovy-material input[type=text]&#39;).val(&#39;&#39;);$(&#39;ul.formErrors&#39;).remove();$(&#39;.formErrors&#39;).removeClass(&#39;formErrors&#39;);$(&#39;.form-pridej-typ-prace-tiskovy-material&#39;).show();$(document).scrollTop($(&#39;.form-pridej-typ-prace-tiskovy-material&#39;).offset().top - 130);return false;" class="table-top-right">nová položka</a>
<a href="http://edgar.ine.cz/typy-prace/obrazkarna#" onclick="$(&#39;table#databaze-typu-prace-tiskovy-material tbody&#39;).toggle();if($(this).text() != &#39;+ rozbalit&#39;) $(&#39;.form-pridej-typ-prace-tiskovy-material&#39;).hide();$(this).text($(this).text() == &#39;+ rozbalit&#39; ? &#39;– sbalit&#39; : &#39;+ rozbalit&#39;);$(this).blur();return false;" class="table-top-right">+ rozbalit</a>
'''
