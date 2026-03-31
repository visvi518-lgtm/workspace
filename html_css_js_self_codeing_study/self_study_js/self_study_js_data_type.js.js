


let str = "str : hello";
let str2 = 'str2 : hello'
console.log(str);
console.log(str2);
let str3 = 'str3 : hell"o';
let str4 = "str4 : hell'o";
console.log(str3);
console.log(str4);
let str5 = 'str5 : 문자열은 큰따옴표("") 또는 작은따옴표(' + "'')로 정의 합니다";
console.log(str5);
// \사용
let str6 = 'str6 : 문자열은 큰따옴표("") 또는 작은따옴표(\'\')로 정의 합니다';
//`(백틱기호)
let str7= `str7 : 문자열은 큰따옴표("") 또는 작은따옴표('')로 정의 합니다`;
//변수 치환
const msg = '문자열';
let str8 = `str8 : ${msg}은 큰따옴표("") 또는 작은따옴표('')로 정의 합니다`;
console.log(str6);
console.log(str7);
console.log(str8);

//숫자형

const num = 10;
console.log(num);
const num2 = 0.1 +0.2;
console.log(num2);
const num3 = (0.1*10 + 0.2*10)/10;
console.log(num3);


//논리형

const bool = 10 <30;

//언디파인드

let numun1;
console.log(numun1);

let numun2 = null;
console.log(numun2)

//객체 자료형

//배열

let array = [10,20,'a'];
console.log(array[2]);

//단항 산술연산자

//대입연산자
let x = 10;
x+=5;
console.log(x);
let y = 1;
y-=5;
console.log(y);
let z = 10;
z *=5;
console.log(z);

//비교연산자
//bool값으로 나옴

let i = 10;
let j = 20;
let result = i > j;
console.log(result);

let k = 10;
let l = '10';
let result1 = k == l;
console.log(result1);

let result2 = k === l;
console.log(result2);

//논리연산자

let resule3 = true || false;
console.log(resule3);

//삼항연산자

let resule4 = 10<20 ? '참입니다':'거짓입니다';  //참이면 ?앞에 있는것을 실행하고 거짓이면 ?뒤에 있는것을 실행
console.log(resule4);