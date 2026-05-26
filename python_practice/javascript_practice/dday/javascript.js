const clockTitle = document.querySelector('.js-clock');
let dday = `000D 00h 00m 00s`;

function getDDay() {
  const targetDay = new Date('2026-12-25T00:00:00');
  const nowDay = new Date();
  const difference = targetDay - nowDay;

  console.log('targetDay:', targetDay);
  console.log('nowDay:', nowDay);
  console.log(`difference: `, targetDay - nowDay);

  const day = Math.floor(difference / (1000 * 60 * 60 * 24));
  const hour = String(
    Math.floor((difference % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
  ).padStart(2, '0');
  const minuite = String(
    Math.floor((difference % (60 * 60 * 1000)) / (1000 * 60))
  ).padStart(2, '0');
  const second = String(Math.floor((difference % (60 * 1000)) / 1000)).padStart(
    2,
    '0'
  );

  const dday = `${day}D ${hour}h ${minuite}m ${second}s`;

  if (difference > -86400000 && difference <= 0) {
    clockTitle.innerText = `D-day!!`;
  } else if (difference <= 86400000 && difference > 0) {
    clockTitle.innerText = `Christmas eve!`;
  } else if (difference <= -86400000) {
    clockTitle.innerText = `time over...`;
  } else {
    clockTitle.innerText = `D-day : ${dday}`;
  }
}

getDDay();
setInterval(getDDay, 1000);
