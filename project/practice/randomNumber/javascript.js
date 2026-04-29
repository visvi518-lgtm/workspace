const rangeForm = document.getElementById('range-form');
const rangeNumber = document.getElementById('range-number');
const guessForm = document.getElementById('guess-form');
const guessNumber = document.getElementById('guess-number');
let randomNumber = 0;

const h4 = document.querySelector('h4');
const h3 = document.querySelector('h3');

console.log(randomC);

function rangeNumberSubmit(event) {
  event.preventDefault();

  const rangeNumberEnter = Number(rangeNumber.value);
  console.log('rangeNumberEnter: ', rangeNumberEnter);

  randomNumber = Math.floor(Math.random() * rangeNumberEnter);
  console.log('randomNumber', randomNumber);
}

rangeForm.addEventListener('submit', rangeNumberSubmit);

function guessNumberSubmit(event) {
  event.preventDefault();
  const guessNumberEnter = Number(guessNumber.value);

  console.log('guessNumberEnter: ', guessNumberEnter);

  h4.innerText = `You chose: ${guessNumberEnter}, the machine chose: ${randomNumber}`;

  if (guessNumberEnter !== randomNumber) {
    console.log('incorrect');
    h3.innerText = 'wrong!';
  } else {
    console.log('correct');
    h3.innerText = 'correct!';
  }
}

guessForm.addEventListener('submit', guessNumberSubmit);
