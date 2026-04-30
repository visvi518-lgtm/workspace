const colorButton = document.querySelector("button");

const colors = [
  '#ef5777',
  '#575fcf',
  '#4bcffa',
  '#34e7e4',
  '#0be881',
  '#f53b57',
  '#3c40c6',
  '#0fbcf9',
  '#00d8d6',
  '#05c46b',
  '#ffc048',
  '#ffdd59',
  '#ff5e57',
  '#d2dae2',
  '#485460',
  '#ffa801',
  '#ffd32a',
  '#ff3f34',
];

const upDownRightLeft =[`to right`, `to bottom`];

console.log(colors.length)
console.log(colors[Math.floor(Math.random()*colors.length)])


function changeBackgroundColor(){
    console.log("click");
    const randomNumber1 = Math.floor(Math.random()*colors.length);
    const randomNumber2 = Math.floor(Math.random()*colors.length);
    const randomNumber3 = Math.floor(Math.random()*upDownRightLeft.length);
    console.log(`colorRight`,randomNumber1);
    console.log(`colorLeft`, randomNumber2);
    console.log(`colorUpDownRightLeft`, randomNumber3);

    const colorRight = colors[randomNumber1];
    const colorLeft = colors[randomNumber2];
    const colorUpDownRightLeft = upDownRightLeft[randomNumber3];

    console.log(colorRight);
    console.log(colorLeft);
    console.log(colorUpDownRightLeft);

    console.log(`linear-gradient(${colorRight}, ${colorLeft})`)
    document.body.style.background = `linear-Gradient(${colorUpDownRightLeft}, ${colorRight}, ${colorLeft})`;

}

colorButton.addEventListener("click", changeBackgroundColor);