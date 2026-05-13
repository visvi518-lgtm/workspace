const clock = document.querySelector("h2#clock");
const timeGreeting = document.querySelector("h1#timeGreeting");

function getClock(){
    const date = new Date();
    const hourNumber = date.getHours();
    const hours = String(hourNumber).padStart(2,"0");
    const minutes = String(date.getMinutes()).padStart(2,"0");
    const seconds = String(date.getSeconds()).padStart(2,"0");
/*     const milliseconds = String(date.getMilliseconds()).padStart(3,"0"); */
/* :${milliseconds} */
    clock.innerText = (`${hours}:${minutes}:${seconds}`);

    /* console.log(hourNumber) */


    if (hourNumber <= 9 && hourNumber >=5 ){
        /* console.log("morning"); */
        timeGreeting.innerText = "Good Morning!";
    }else if(hourNumber > 9 && hourNumber<=11){
        /* console.log("afternoon"); */
        timeGreeting.innerText = "Good afternoon!";
    }else if(hourNumber >11 && hourNumber<=20){
        /* console.log("evening"); */
        timeGreeting.innerText = "Good evening!";
    }else if(hourNumber >20 || hourNumber<5){
        /* console.log("night"); */
        timeGreeting.innerText ="Good night!";
    }

}


getClock();
setInterval(getClock, 1000);
