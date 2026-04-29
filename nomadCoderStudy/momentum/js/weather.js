const API_KEY = '954015734f3550ccfb1e522f7be5a85b';

function onGeoOk(position){
    const lat = position.coords.latitude;
    const lon = position.coords.longitude;
    console.log(`weather.log.Geo.location.You live in : `, lat, ` , `, lon);
    const url = `https://api.openweathermap.org/data/2.5/weather?lat=${lat}&lon=${lon}&appid=${API_KEY}&units=metric`;
    console.log(url);
    fetch(url)
    .then(Response => Response.json())
    .then((data) => {
        const weather = document.querySelector("#weather span:first-child")
        const city = document.querySelector("#weather span:last-child")
        city.innerText = data.name;
        weather.innerText = `${data.weather[0].main} / ${data.main.temp}`
    });
}
function onGeoError(){
    alert(`Can't find you. No weather for you.`)
}

navigator.geolocation.getCurrentPosition(onGeoOk, onGeoError);
