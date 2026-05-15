const stopWatch = document.querySelector("h1#watch");
const startButton = document.getElementById("start-btn");
const stopButton = document.getElementById("stop-btn");
const pauseButton = document.getElementById("pause-btn");
const clearButton = document.getElementById("clear-btn");

const HIDDEN_CLASSNAME = "hidden";

let nowTime = 0;
let intervalId = null;
let watchTime = 0;

function formatTime(milliseconds){
    const totalSeconds = Math.floor(milliseconds /1000);

    const milliSeconds = String(milliseconds%1000).padStart(2, "0");
    const hours = String(Math.floor(totalSeconds / 3600)).padStart(2,"0");
    const minutes = String(Math.floor((totalSeconds % 3600)/60)).padStart(2, "0");
    const seconds = String(totalSeconds % 60).padStart(2,"0");

    return `${hours}:${minutes}:${seconds}.${milliSeconds}`;
}

let isAlerted = false;

function startButtonClick(){

    isAlerted = false;

    if(intervalId !== null){
        return;
    }

    pauseButton.classList.remove(HIDDEN_CLASSNAME);

    console.log("start click");
    nowTime = new Date();

    console.log(nowTime);

    intervalId = setInterval(function() {
        const newTime = new Date();
        watchTime = newTime - nowTime;

        console.log(watchTime);
        stopWatch.innerText = formatTime(watchTime);

        if (watchTime >= 5000 && isAlerted ===false){
            alert("over 5sec")
            isAlerted = true;
        }
    },50);



}

function stopButtonClick(){
    console.log("stop click")

    clearInterval(intervalId);
    intervalId = null;
    pauseButton.classList.add(HIDDEN_CLASSNAME)

    stopWatch.innerText = "00:00:00";

}

const pauseList = document.getElementById("pause-list");

function pauseButtonClick(){
    clearButton.classList.remove(HIDDEN_CLASSNAME);
    console.log("pause click");
    const li = document.createElement("li");
    li.innerText = formatTime(watchTime);

    pauseList.appendChild(li);
}

function clearButtonClick(){
    console.log("clear click");
    pauseList.innerHTML = "";
    clearButton.classList.add(HIDDEN_CLASSNAME);
}



startButton.addEventListener("click", startButtonClick);
stopButton.addEventListener("click", stopButtonClick);
pauseButton.addEventListener("click", pauseButtonClick);
clearButton.addEventListener("click", clearButtonClick);