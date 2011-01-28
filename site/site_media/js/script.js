function CheckAll(element)
{
	inputs = document.getElementsByTagName('input');
	for (i = 0; i < inputs.length; i++)
	{
		if (inputs[i].type=='checkbox')
		{
			if (element.checked==true) 
			{
				inputs[i].checked=true;
			}
			else
			{
				inputs[i].checked=false;
			}
		}
	}
}

var state = 'none';
function toggleDiv(divid) {
	if (state == 'inline') {
		state = 'none';
	}
	else {
		state = 'inline';
	}
	var elem = document.getElementById(divid);
	if (document.layers) { //IS NETSCAPE 4 or below
		elem.display = state;
	}
	else {
		elem.style.display = state;
	}
}
