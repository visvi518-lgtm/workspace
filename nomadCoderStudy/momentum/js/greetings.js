const loginForm = document.querySelector("#login-form");
const loginInput = document.querySelector("#login-form input");
const greeting = document.querySelector("#greeting");
const usernameDeleteButton = document.querySelector("#usernameDelete");

const HIDDEN_CLASSNAME = "hidden";
const USERNAME_KEY = "username";

const date = new Date();

function onLoginSubmit(event) {
    event.preventDefault();
    loginForm.classList.add(HIDDEN_CLASSNAME);
    const username = loginInput.value;
    localStorage.setItem(USERNAME_KEY, username);
    paintGreetings(username);
    
    /* 로그남기기 */
    console.log(`console log : user login`)
    console.log(`login time : ${date}`);
    console.log(`username : "${username}"`);
    console.log(`localstorage.username : "${localStorage.username}"`);
    console.log(`coment : "Hello ${username}"`);
}


function paintGreetings(username){
    greeting.innerText = `Hello ${username}!!`;
    greeting.classList.remove(HIDDEN_CLASSNAME);
    usernameDeleteButton.classList.remove(HIDDEN_CLASSNAME);
}

function enterUsername(){
    loginForm.classList.remove(HIDDEN_CLASSNAME);
    loginForm.addEventListener("submit", onLoginSubmit);
    console.log(`savedUsername : ${savedUsername}`);
}

const savedUsername = localStorage.getItem(USERNAME_KEY);


if(savedUsername === null) {
    //show the form
    enterUsername(savedUsername);
    console.log(`usernameNotExist`);
}else{
    //show the greeting
    paintGreetings(savedUsername);
    console.log(`savedUsername : ${savedUsername}`);
}

function usernameDeleteHandle(event){
    alert(`username deleted`);
    localStorage.removeItem(USERNAME_KEY);
    console.log(`deletedUsername`);
    console.log(`savedUsername : ${savedUsername}`);
}


usernameDeleteButton.addEventListener("click", usernameDeleteHandle);