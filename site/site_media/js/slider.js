$(function(){
	//demo 1
	var abc = $('select#speed').selectToUISlider().next();
			
	//demo 2
	$('select#valueA, select#valueB').selectToUISlider();
		
	//demo 3
	$('select#valueAA, select#valueBB').selectToUISlider({
		labels: 12
	});
});
