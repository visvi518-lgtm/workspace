const stopWatch = document.querySelector("h1#watch");
const startButton = document.getElementById("startBtn");
const stopButton = document.getElementById("stopBtn");

let nowTime = 0;
let intervalId = null;

function formatTime(milliseconds){
    const totalSeconds = Math.floor(milliseconds /1000);

    const milliSeconds = String(milliseconds%1000).padStart(2, "0");
    const hours = String(Math.floor(totalSeconds / 3600)).padStart(2,"0");
    const minutes = String(Math.floor((totalSeconds % 3600)/60)).padStart(2, "0");
    const seconds = String(totalSeconds % 60).padStart(2,"0");

    return `${hours}:${minutes}:${seconds}.${milliSeconds}`;
}

function startButtonClick(){

    if(intervalId !== null){
        return;
    }

    console.log("start click");
    nowTime = new Date();

    console.log(nowTime);

    intervalId = setInterval(function() {
        const newTime = new Date();
        const watchTime = newTime - nowTime;

        console.log(watchTime);
        stopWatch.innerText = formatTime(watchTime);
    },50);

}

function stopButtonClick(){
    console.log("stop click")

    clearInterval(intervalId);
    intervalId = null;

    stopWatch.innerText = "00:00:00";
}

startButton.addEventListener("click", startButtonClick);

stopButton.addEventListener("click", stopButtonClick);