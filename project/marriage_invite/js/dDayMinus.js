//디데이 마이너스
function getDday() {
            const targetDate = new Date("2026-11-29T00:00:00+09:00");
            const nowDate = new Date();
            const difference = targetDate - nowDate;

            const dday = Math.ceil(difference / (1000 * 60 * 60 * 24));
            document.getElementById("dday-count").innerText = `D-${dday}`;
        }

        getDday();
        setInterval(getDday, 1000);
