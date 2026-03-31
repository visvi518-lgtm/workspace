/* let a = 10;
function sum(){
    console.log(`함수 내부에서 a 참조 : ${a}`);
}
sum();
console.log(`함수 외부에서 a 참조 : ${a}`);
 */


//전역 스코프, 지역 스코프 비교
/* let a = 20;
function sum(){
    let a = 10;
    console.log(`함수 내부에서 a 참조 : ${a}`);
}
sum();
console.log(`함수 외부에서 a 참조 : ${a}`);
 */

//호이스팅
PrintName();
function PrintName(){
    console.log(`수코딩`);
}

/* const init = () =>{
    console.log('init');
}
init(); */

//전역함수가 오염되었음을 알아야함

//이때 즉시 실행함수를 사용하면 해결할수 있음
//즉시 시행함수는 한번만 사용하고 안쓰는 함수이기때문

(function init() {
    console.log(`init`);
})
();

function init(){
    console.log(`init2`);
}

console.log(init());