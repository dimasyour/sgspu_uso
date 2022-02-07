var selectedDevice = null,
      category1 = document.getElementById('category1'),
      category2 = document.getElementById('category2');
function onChangeSelect(select) {
  selectedDevice = this.options[this.selectedIndex].innerHTML;
  if (selectedDevice == "Студент") {
  	(category1.style.display = 'block');
    document.getElementById('faculty').hidden = false;
  }
  else {
    (category1.style.display = 'none');
    document.getElementById('faculty').hidden = true;
    document.getElementById('faculty').value = 'Ytn af';
  }
}
document.getElementById('you').addEventListener('change', onChangeSelect);