

//조건문 다루기

let num =10;
if(num == 0){
    console.log('num은 0 입니다');
}else if(num%2==0){
    console.log('num은 짝수 입니다');
}else{
    console.log('num은 홀수 입니다');
}

//스위치 문
let food ='melon';
switch(food){
    case 'melon':
        console.log('fruit');
        break;
    case 'apple':
        console.log('fruit');
        break;
    case 'banana':
        console.log('fruit');
        break;
    case 'carrot':
        console.log('vegetable');
        break;
    default:
        console.log("it's not fruits and vegetable");
        break;
}

