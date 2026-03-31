/* const str = 'abc';
console.log(str.length); */

/* const email = 'test@naver.com';
if(email.includes("@") ===false) {
    console.log('@가 없습니다');
} */



/* const email = 'test@naver.com';
console.log(email.indexOf('t'));    
 */



/* const email = 'testnaver.com';
if(email.indexOf("@")=== -1){
    console.log('@가 없습니다');
}
 */


//앞뒤 공백
/* const email = ' test@naver.com';
console.log(email.trim()); */


//replaceAll
/* const email = 'test naver.com';
console.log(email.replaceAll(' ', '')); */


//array

//파괴적 메서드
/* const arr = ['a', 'b', 'c'];
arr.pop();
console.log(arr); */

/* const arr = ['a','b', 'c'];
const popResult = arr.pop();
arr.pop();
console.log(arr); */

//파괴적 메서드는 사용할수록 원본데이터에 손상이 생김


/* const arr = ['a', 'b', 'c'];
arr.push('d');
console.log(arr); */




//비파괴적 메서드
/* const arr = ['a', 'b', 'c'];
arr.forEach(function(v){
    console.log(v);
});
console.log(arr); */



//날짜
/* const date = new Date();
console.log(date.getFullYear());
 */


//math객체
/* const random = Math.random();
console.log(random);

const random2 = Math.random()*20;
console.log(random2);

const random3 = Math.random()*20;
console.log(Math.floor(random3));

const random4 = Math.random()*80;
console.log(Math.floor(random4)); */
