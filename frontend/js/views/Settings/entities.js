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
var current_entity_id;
const subroute = "entities";

export default class extends AbstractView {
  constructor() {
    super();
  }

  async getHtml() {
    return `<div class="reload-message"></div>
    <h1 class="heading-primary">entities</h1>
    <div class="table-overflow-wrapper">
      <table id="entity-table">
        <tr>
          <th>id</th>
          <th>name</th>
          <th>actions</th>
        </tr>
      </table>
    </div>
    
    <!-- EDIT USER FORM -->
    <h1 class="heading-primary">add/edit entity</h1>
    <form id="add-edit-form" class="edit-form" name="edit-user" netlify>
      <div class="form-data">
        <div class="form-row">
          <label for="entity-id">Entity ID</label>
          <input id="entity-id" type="text" placeholder="n/a" name="id" disabled />
        </div>
    
        <div class="form-row">
          <label for="entity-name">Name</label>
          <input
            id="entity-name"
            type="text"
            placeholder="John & Jane"
            name="name"
            required
          />
        </div>
    
        <span class="button-holder">
          <button class="btn--form" id="btn-add">Add</button>
          <button class="btn--form" id="btn-update" disabled>Update</button>
          <input class="btn--form" type="reset" />
        </span>
      </div>
    </form>

    <br>
    <br>
    <br>
    <h1 class="heading-primary">Current Users</h1>
    <div class="table-overflow-wrapper">
      <table id="users-table">
        <tr>
          <th>id</th>
          <th>name</th>
          <th>actions</th>
        </tr>
      </table>
    </div>

    <br>
    <br>
    <br>
    <h1 class="heading-primary">Add Users to Entity</h1>
    <form id="add-edit-form" class="edit-form" name="edit-user" netlify>
      <div class="form-data">
        <div class="form-row">
          <label for="select-user">User</label>
          <select id="select-user" name="user_id" required>
            <option value=-1>&nbsp;&nbsp;--select user--</option>
          </select>
        </div>

        <span class="button-holder">
          <button class="btn--form" id="btn-add-user" disabled>Add</button>
        </span>
      </div>
    </form>

    `;
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
        getUsers(jwt);
      },
      displayMessageToUser
    );

    document.getElementById("btn-add-user").addEventListener("click", addUser);

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
              data["name"] + " successfully added."
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
      }
    });
  }
}

function getUsers(jwt) {
  // attach the users public-id to the json & send at PUT instead of POST
  const route = base_uri + "/users/active";

  callAPI(
    jwt,
    route,
    "GET",
    null,
    (data) => {
      console.log("Reply from users/active");
      console.log(data);
      populateUserListBox(data);
    },
    displayMessageToUser
  );
}

function populateTable(entities) {
  var table = document.getElementById("entity-table");

  for (var i = 0; i < entities.length; i++) {
    var tr = table.insertRow(-1);

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = entities[i]["id"].substring(0, 4);

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = entities[i]["name"];

    var tabCell = tr.insertCell(-1);

    // Edit button
    var btn_edt = document.createElement("button");
    btn_edt.id = entities[i]["id"];
    btn_edt.index = i;
    btn_edt.innerHTML = "Select";
    btn_edt.className += "btn--action";
    btn_edt.addEventListener("click", populateEdit);
    tabCell.appendChild(btn_edt);
    // Slash
    tabCell.insertAdjacentText("beforeend", "\x2F");
    // Delete button
    var btn_del = document.createElement("button");
    btn_del.id = entities[i]["id"];
    btn_del.innerHTML = "Del";
    btn_del.className += "btn--action";
    btn_del.addEventListener("click", delEntity);
    tabCell.appendChild(btn_del);
  }
}

function populateUsersTable(users, entity_id) {
  var table = document.getElementById("users-table");

  // clear anything already in the table
  const rowCount = table.rows.length;
  for (let i = rowCount - 1; i > 0; i--) {
    table.deleteRow(i);
  }

  for (var i = 0; i < users.length; i++) {
    var tr = table.insertRow(-1);

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = users[i]["id"].substring(0, 4);

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = users[i]["first_name"] + " " + users[i]["last_name"];

    var tabCell = tr.insertCell(-1);

    // Remove button
    var btn_del = document.createElement("button");
    btn_del.user_id = users[i]["id"];
    btn_del.entity_id = entity_id;
    btn_del.innerHTML = "Remove";
    btn_del.className += "btn--action";
    btn_del.addEventListener("click", removeMember);
    tabCell.appendChild(btn_del);
  }
}

function delEntity(e) {
  const route = base_uri + "/" + subroute + "/" + e.currentTarget.id;

  if (window.confirm("You are about to delete an entity. Are you sure?")) {
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

function removeMember(e) {
  const route =
    base_uri +
    "/" +
    subroute +
    "/remove-user/" +
    e.currentTarget.entity_id +
    "/" +
    e.currentTarget.user_id;

  callAPI(
    jwt_global,
    route,
    "DELETE",
    null,
    (data) => {
      localStorage.setItem(
        "previous_action_message",
        "Successful removal of user from entity"
      );
      window.scrollTo(0, 0);
      location.reload();
    },
    displayMessageToUser
  );
}

function populateEdit(e) {
  const i = e.currentTarget.index;
  const entity_id = e.currentTarget.id;

  current_entity_id = entity_id;

  // disable the "Add" and enable the "Update"

  document.getElementById("btn-update").disabled = false;
  document.getElementById("btn-add").disabled = true;

  document.getElementById("entity-id").value = i.toString();
  document.getElementById("entity-name").value = "foo"; //db_data[i]["name"];

  document.getElementById("add-edit-form").scrollIntoView();

  // Find the users with access to this entity
  const route = base_uri + "/" + subroute + "/users/" + entity_id;
  var users;

  callAPI(
    jwt_global,
    route,
    "GET",
    null,
    (data) => {
      populateUsersTable(data, entity_id);
      console.log("BRAVO");
    },
    displayMessageToUser
  );

  // set the add new user button to this entity_id
  document.getElementById("btn-add-user").entity_id = entity_id;
  document.getElementById("btn-add-user").disabled = false;
}

function populateUserListBox(users) {
  var select_property = document.getElementById("select-user");
  for (var i = 0; i < users.length; i++) {
    var option_new = document.createElement("option");
    option_new.innerHTML = users[i]["first_name"] + " " + users[i]["last_name"];
    option_new.value = users[i]["id"];
    select_property.appendChild(option_new);
  }
}

function addUser(e) {
  const user_id = document.getElementById("select-user").value;
  const route =
    base_uri +
    "/" +
    subroute +
    "/add-user/" +
    current_entity_id +
    "/" +
    user_id;

  callAPI(
    jwt_global,
    route,
    "POST",
    null,
    (data) => {
      localStorage.setItem("previous_action_message", "User added to Entity");
      window.scrollTo(0, 0);
      location.reload();
    },
    displayMessageToUser
  );
}
