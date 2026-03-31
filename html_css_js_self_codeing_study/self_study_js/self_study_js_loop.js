

//반복문 다루기


/* 
let num = 1;
while(num <=9999){
    console.log(num);
    num++;
} */

/* let num = 1;
do{
//조건문이 참이면 실행할 구문
console.log('do');
}while(false) */


/* for(초깃값; 저건식; 증감식){
} */

/* for(let i =0; i<=5;i++){
    console.log(i);
} */

for (let i = 0; i <= 2; i++){
    console.log(`i : ${i}`);    //백틱 조심
    for (let k = 0; k <= 2; k++){
    console.log(`k : ${k}`);
    }
}


//for문의 배열
/* const arr = ['apple','banana', 'orange'];
const obj = {
    name : '철수',
    age : 20,
};
for (let h=0;h<arr.length;h++){
    console.log(arr[h]);
}

for (let index in arr){
    console.log(arr[index]);
}

for (let key in obj){
    console.log(obj[key]);
} */

//break, continue

for(let i=0;i<5;i++){
    if(i===3){
        continue;
    }
    console.log(i);
}