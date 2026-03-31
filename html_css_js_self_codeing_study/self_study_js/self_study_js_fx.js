/* for (let j = 1; j<=9;j++){
for (let i = 1; i<=9;i++){
    console.log(`${j} * ${i} = ${j*i}`);

}
} */

//함수 선언문
/* function gugudan(){
    for (let i = 1;i<=9;i++){
        console.log(`3 * ${i} = ${3*i}`);
    }
}
gugudan(); */

/* 
function gugudan1(dan, dan2, dan3){
    for (let i = 1;i<=9;i++){
        console.log(`3 * ${i} = ${3*i}`);
    }
}
gugudan1(3); */
//매개변수와 인수의 갯수가 반드시 일치하지 않아도 됌
/* 
function gugudan(dan){
    for(let i = 1;i<=9;i++){
        console.log(`${dan} * ${i} = ${dan * i}`);
    }
}

gugudan(4);
 */

/* 
//함수 표현식
const gugudanExpress = function gugudanExpress(){
    for (let i = 1;i<=9;i++){
        console.log(`3 * ${i} = ${3*i}`);
    }    
}
gugudanExpress();

//화살표 함수
const gugudanArrowFunc = () => {
    for (let i = 1;i<=9;i++){
        console.log(`3 * ${i} = ${3*i}`);
    }    
}
gugudanArrowFunc(); */



//리턴문

function sum(num1, num2){
    const result = num1 + num2;
    return result;
    console.log(result);
}

const result1 = sum(10, 20);
const result2 = sum(50, 100);

console.log(result1 + result2);
