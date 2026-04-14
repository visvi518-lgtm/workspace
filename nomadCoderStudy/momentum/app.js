const loginForm = document.querySelector("#login-form");
const loginInput = document.querySelector("#login-form input");
const link = document.querySelector("a");

function onLiginSubmit(event){
    event.preventDefault();
    console.log(loginInput.value);
}

function handleLinkClick(event){
    event.preventDefault();
    console.log(event)
    console.dir(event);

}

loginForm.addEventListener("submit", onLiginSubmit);
link.addEventListener("click", handleLinkClick);

