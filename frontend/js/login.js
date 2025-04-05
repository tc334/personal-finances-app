import { base_uri } from "./constants.js";
import { callAPI } from "./common_funcs.js";

const form_login = {
  email: document.querySelector("#inp-login-email"),
  password: document.querySelector("#inp-login-password"),
  submit: document.querySelector("#btn-login-submit"),
  reset: document.querySelector("#inp-login-reset"),
};

async function postData() {
  const url = base_uri + "/token";
  let formData = new FormData();
  formData.append("username", form_login.email.value);
  formData.append("password", form_login.password.value);
  const data = new URLSearchParams(formData);

  try {
    const response = await fetch(url, {
      method: "POST",
      body: data,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const responseData = await response.json();
    console.log("Success:", responseData);
    if (!(responseData == null)) {
      localStorage.setItem("token", responseData["access_token"]);
      location.href = "index.html";
    }
  } catch (error) {
    console.error("Error:", error);
  }
}

let button = form_login.submit.addEventListener("click", (e) => {
  e.preventDefault();
  postData();
});

document.getElementById("btn-passwordreset").addEventListener("click", (e) => {
  let email = prompt(
    "Enter the email address associated with your account, and a password reset link will be sent to you."
  );
  if (email == null || email == "") {
    return;
  }

  const route = base_uri + "/password_reset_request";
  const method = "POST";
  const body = JSON.stringify({
    email: email,
  });

  callAPI(
    null,
    route,
    method,
    body,
    (data) => {
      console.log("Submit appears to have succeeded");
    },
    (data) => {
      reportFail("div-signup-response", data);
    }
  );
});

function reportFail(id, msg) {
  document.getElementById(id).innerHTML = msg;
}

// Clear the on-screen error messages when user clicks reset
form_login.reset.addEventListener("click", (e) => {
  document.getElementById("div-login-response").innerHTML = "";
});
