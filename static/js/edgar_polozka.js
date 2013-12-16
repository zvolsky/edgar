$(function(){
  $('#sirka').focus();
  /* $('form:first *:input[type!=hidden]:first').focus();
     $('*:input:visible:enabled:first').focus();
     $("form:first *:input,select,textarea").filter(":not([readonly='readonly']):not([disabled='disabled']):not([type='hidden'])").first().focus(); */
  
  $('#levy').blur(function(){
    if ($('#levy').val()<=0) { 
      $('#levy').val(0)};
    if ($('#pravy').val()<=0) { 
      $('#pravy').val(+$(this).val())};
    if ($('#horni').val()<=0) { 
      $('#horni').val(+$(this).val())};
    if ($('#dolni').val()<=0) { 
      $('#dolni').val(+$(this).val()+1.0)};
    });

  /* $('#horni').blur(function(){
    if ($('#dolni').val()<=0) { 
    $('#dolni').val($(this).val())}}); */

  $('select.typprace').change(function(){cena();});
  
  $('*').blur(function(){cena();});

  var poznCls=''; var poznTxt='';
  $('.modalPozn').blur(function(){
    if ($(this).val()) {poznCls='modalLink poznamka'; poznTxt=$(this).val();}
                  else {poznCls='modalLink pozn'; poznTxt='připiš poznámku';}; 
    $('#a'+$(this).attr('id')).text(poznTxt).attr('class', poznCls);
    });

  $('.modalLink').modal({
    trigger: '.modalLink',
    olay:'div.overlay',
    modals:'div.modal',
    animationEffect: 'slidedown',
    animationSpeed: 200,
    moveModalSpeed: 'slow',
    background: '00c2ff',
    opacity: 0.8,
    openOnLoad: false,
    docClose: true,
    closeByEscape: true,
    moveOnScroll: true,
    resizeWindow: true,
    close:'.closeBtn'
    })
  });

function cena() {
  var sirka = +$('#sirka').val()||0;
  var vyska = +$('#vyska').val()||0;
  var levy = +$('#levy').val()||0;
  var horni = +$('#horni').val()||0;
  var pravy = +$('#pravy').val()||0;
  var dolni = +$('#dolni').val()||0;
  var obvod_vnitrni = ((sirka + vyska) / 50).toFixed(3);
  var obvod_vnejsi = ((sirka + vyska + levy + horni + pravy + dolni) / 50
                      ).toFixed(3);
  var plocha_vnitrni = (sirka*vyska*0.0001).toFixed(4);
  var plocha_vnejsi = ((sirka+levy+pravy)*(vyska+horni+dolni)*0.0001).toFixed(4);
  var cena=0;
  $('select.typprace').each(function(sindex) {
        $(this).children('option').each(function(oindex) {
              var cena1 = +$(this).attr('cena')||0;
              if ($(this).attr('selected')||''=='selected') {
                  cena += cena1 * plocha_vnejsi};
                  });
        });
  cena = (cena * $('#ks').val()).toFixed(0);
  
  $('#obvod_vnitrni').text(obvod_vnitrni);
  $('#obvod_vnejsi').text(obvod_vnejsi);
  $('#plocha_vnitrni').text(plocha_vnitrni);
  $('#plocha_vnejsi').text(plocha_vnejsi);
  $('#cena').text(cena);
  };
