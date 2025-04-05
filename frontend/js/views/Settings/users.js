import AbstractView from "../AbstractView.js";
import { base_uri } from "../../constants.js";
import {
  callAPI,
  reloadMessage,
  displayMessageToUser,
  populate_aside_settings,
  decode_jwt,
} from "../../common_funcs.js";

var jwt_global;
var db_data;
const subroute = "users";

export default class extends AbstractView {
  constructor() {
    super();
  }

  async getHtml() {
    return `<div class="reload-message"></div>
    <h1 class="heading-primary">users</h1>
    <div class="table-overflow-wrapper">
      <table id="user-table">
        <tr>
          <th>id</th>
          <th>first</th>
          <th>last</th>
          <th>email</th>
          <th>level</th>
          <th>status</th>
          <th>confirmed</th>
          <th>actions</th>
        </tr>
      </table>
    </div>
    
    <!-- EDIT USER FORM -->
    <h1 class="heading-primary">add/edit user</h1>
    <form id="add-edit-form" class="edit-form" name="edit-user" netlify>
      <div class="form-data">
        <div class="form-row">
          <label for="user-id">User ID</label>
          <input id="user-id" type="text" placeholder="n/a" name="id" disabled />
        </div>
    
        <div class="form-row">
          <label for="first-name">First Name</label>
          <input
            id="first-name"
            type="text"
            placeholder="John"
            name="first_name"
            required
          />
        </div>
    
        <div class="form-row">
          <label for="last-name">Last Name</label>
          <input
            id="last-name"
            type="text"
            placeholder="Doe"
            name="last_name"
            required
          />
        </div>
    
        <div class="form-row">
          <label for="email">Email address</label>
          <input
            id="email"
            type="email"
            placeholder="john.doe@domain.com"
            name="email"
            required
          />
        </div>
    
        <div class="form-row">
          <label for="select-level">Membership Level</label>
          <select id="select-level" name="level" required>
            <option value="">Select one</option>
            <option value="USER">User</option>
            <option value="ADMIN">Administrator</option>
          </select>
        </div>
    
        <div class="form-row">
          <label for="select-status">Membership Status</label>
          <select id="select-status" name="active" required>
            <option value="">Select one</option>
            <option value="true">Active</option>
            <option value="false">Inactive</option>
          </select>
        </div>
    
        <div class="form-row">
          <label for="select-confirmed">Email Confirmed</label>
          <select id="select-status" name="confirmed" required>
            <option value="">Select one</option>
            <option value="true">True</option>
            <option value="false">False</option>
          </select>
        </div>
    
        <span class="button-holder">
          <button class="btn--form" id="btn-add">Add</button>
          <button class="btn--form" id="btn-update" disabled>Update</button>
          <input class="btn--form" type="reset" />
        </span>
        </br>
        <button class="btn--form" id="btn-reconfirm">Resend Confirmation</button>
      </div>
    </form>`;
  }

  js(jwt) {
    // this variable is copied into the higher namespace so I can get it
    // into the delete function
    jwt_global = jwt;

    // check for reload message; if exists, display
    reloadMessage();

    const user_level = decode_jwt(jwt);
    populate_aside_settings(user_level);

    // First step is to pull data from DB
    const route = base_uri + "/" + subroute;
    callAPI(
      jwt,
      route,
      "GET",
      null,
      (response_full_json) => {
        populateTable(response_full_json);
      },
      displayMessageToUser
    );

    // When the "reset" button is hit, only "add" should be enabled
    // "update" will get enabled if a user hits an "edit" in the main table
    const myForm = document.getElementById("add-edit-form");
    myForm.addEventListener("reset", function (e) {
      document.getElementById("btn-add").disabled = false;
      document.getElementById("btn-update").disabled = true;
    });

    // What do do on a submit
    myForm.addEventListener("submit", function (e) {
      e.preventDefault();

      // Pull data from form and put it into the json format the DB wants
      const formData = new FormData(this);

      var new_user = {};
      formData.forEach((value, key) => (new_user[key] = value));
      var json = JSON.stringify(new_user);

      if (e.submitter.id == "btn-add") {
        const route = base_uri + "/" + subroute;

        callAPI(
          jwt,
          route,
          "POST",
          json,
          (data) => {
            localStorage.setItem(
              "previous_action_message",
              data["first_name"] + " successfully added."
            );
            window.scrollTo(0, 0);
            location.reload();
          },
          displayMessageToUser
        );
      } else if (e.submitter.id == "btn-update") {
        // attach the users public-id to the json & send at PUT instead of POST
        const route = base_uri + "/" + subroute + "/" + e.submitter.public_id;

        callAPI(
          jwt,
          route,
          "PUT",
          json,
          (data) => {
            localStorage.setItem("previous_action_message", data["message"]);
            window.scrollTo(0, 0);
            location.reload();
          },
          displayMessageToUser
        );
      } else if (e.submitter.id == "btn-reconfirm") {
        // attach the users public-id to the json & send at PUT instead of POST
        const route =
          base_uri + "/" + subroute + "/reconfirm/" + e.submitter.public_id;

        callAPI(
          jwt,
          route,
          "PUT",
          json,
          (data) => {
            localStorage.setItem("previous_action_message", data["message"]);
            window.scrollTo(0, 0);
            location.reload();
          },
          displayMessageToUser
        );
      }
    });
  }
}

function populateTable(users) {
  var table = document.getElementById("user-table");

  for (var i = 0; i < users.length; i++) {
    var tr = table.insertRow(-1);

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = users[i]["id"].substring(0, 4);

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = users[i]["first_name"];

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = users[i]["last_name"];

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = users[i]["email"];

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = users[i]["level"];

    var tabCell = tr.insertCell(-1);
    if (users[i]["active"] == true) {
      tabCell.innerHTML = "Active";
    } else {
      tabCell.innerHTML = "Disabled";
    }

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = users[i]["confirmed"];

    var tabCell = tr.insertCell(-1);

    // Edit button
    var btn_edt = document.createElement("button");
    btn_edt.id = users[i]["id"];
    btn_edt.index = i;
    btn_edt.innerHTML = "Edit";
    btn_edt.className += "btn--action";
    btn_edt.addEventListener("click", populateEdit);
    tabCell.appendChild(btn_edt);
    // Slash
    tabCell.insertAdjacentText("beforeend", "\x2F");
    // Delete button
    var btn_del = document.createElement("button");
    btn_del.id = users[i]["id"];
    btn_del.innerHTML = "Del";
    btn_del.className += "btn--action";
    btn_del.addEventListener("click", delMember);
    tabCell.appendChild(btn_del);
  }
}

function delMember(e) {
  const route = base_uri + "/" + subroute + "/" + e.currentTarget.id;

  if (window.confirm("You are about to delte a member. Are you sure?")) {
    callAPI(
      jwt_global,
      route,
      "DELETE",
      null,
      (data) => {
        localStorage.setItem(
          "previous_action_message",
          "Successful delete of user"
        );
        window.scrollTo(0, 0);
        location.reload();
      },
      displayMessageToUser
    );
  }
}

function populateEdit(e) {
  const i = e.currentTarget.index;

  // attach the public_id to the "Update" button
  var btn_update = document.getElementById("btn-update");
  btn_update.public_id = db_data[i]["public_id"];
  var btn_reconfirm = document.getElementById("btn-reconfirm");
  btn_reconfirm.public_id = db_data[i]["public_id"];

  // disable the "Add" and enable the "Update"
  btn_update.disabled = false;
  document.getElementById("btn-add").disabled = true;

  document.getElementById("user-id").value = i.toString();
  document.getElementById("first-name").value = db_data[i]["first_name"];
  document.getElementById("last-name").value = db_data[i]["last_name"];
  document.getElementById("email").value = db_data[i]["email"];
  document.getElementById("select-level").value = db_data[i]["level"];
  document.getElementById("select-status").value = db_data[i]["status"];

  document.getElementById("add-edit-form").scrollIntoView();
}
