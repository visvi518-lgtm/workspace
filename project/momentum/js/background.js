const images = [
    "background img1.jpg",
    "background img2.jpg",
    "background img3.jpg"
];

const imageRandomNumber = Math.floor(Math.random()*images.length);
const chosenImg = images[imageRandomNumber];
/* const bdImage = document.createElement("img");

bdImage.src = `img/${chosenImg}`;

document.body.appendChild(bdImage); */

document.body.style.backgroundImage = `URL("img/${chosenImg}")`;


function randomImageLog(){
    console.log(imageRandomNumber+1, `번째 사진`);
    console.log(chosenImg);
}

randomImageLog()
