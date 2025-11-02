// Παίρνουμε τα στοιχεία από το HTML
var divisor = document.getElementById("divisor");
var slider = document.getElementById("slider");

// συνάρτηση που καλείται όταν κινείται το slider
function moveDivisor() {
  // Αλλάζουμε το πλάτος του div με βάση την τιμή του slider
  divisor.style.width = slider.value + "%";
}