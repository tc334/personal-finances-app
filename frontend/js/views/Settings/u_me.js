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
    <h1 class="heading-primary">My Profile</h1>
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
        </tr>
      </table>
    </div>

    <h1 class="heading-primary">my entities</h1>
    <div class="table-overflow-wrapper">
      <table id="entities-table">
        <tr>
          <th>id</th>
          <th>name</th>
          <th>selected</th>
          <th>actions</th>
        </tr>
      </table>
    </div>
    
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
    const route = base_uri + "/" + subroute + "/me";
    callAPI(
      jwt,
      route,
      "GET",
      null,
      (response_full_json) => {
        populateUserTable(response_full_json);
      },
      displayMessageToUser
    );

    // Next step is to find all entities this user is part of
    const route2 = base_uri + "/entities/me";
    callAPI(
      jwt,
      route2,
      "GET",
      null,
      (response_full_json) => {
        populateEntitiesTable(response_full_json);
      },
      displayMessageToUser
    );
  }
}

function populateUserTable(user) {
  var table = document.getElementById("user-table");

  var tr = table.insertRow(-1);

  var tabCell = tr.insertCell(-1);
  tabCell.innerHTML = user["id"].substring(0, 4);

  var tabCell = tr.insertCell(-1);
  tabCell.innerHTML = user["first_name"];

  var tabCell = tr.insertCell(-1);
  tabCell.innerHTML = user["last_name"];

  var tabCell = tr.insertCell(-1);
  tabCell.innerHTML = user["email"];

  var tabCell = tr.insertCell(-1);
  tabCell.innerHTML = user["level"];

  var tabCell = tr.insertCell(-1);
  if (user["active"] == true) {
    tabCell.innerHTML = "Active";
  } else {
    tabCell.innerHTML = "Disabled";
  }

  var tabCell = tr.insertCell(-1);
  tabCell.innerHTML = user["confirmed"];
}

function populateEntitiesTable(entities) {
  const current_entity = localStorage.getItem("current_entity");

  var table = document.getElementById("entities-table");

  for (var i = 0; i < entities.length; i++) {
    var tr = table.insertRow(-1);

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = entities[i]["id"].substring(0, 4);

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = entities[i]["name"];

    var tabCell = tr.insertCell(-1);
    if (entities[i]["id"] == current_entity) {
      tabCell.innerHTML = "SELECTED";
    }

    var tabCell = tr.insertCell(-1);

    // Select button
    var btn_sel = document.createElement("button");
    btn_sel.id = entities[i]["id"];
    btn_sel.index = i;
    btn_sel.innerHTML = "Select";
    btn_sel.className += "btn--action";
    btn_sel.addEventListener("click", selectNewEntity);
    tabCell.appendChild(btn_sel);
  }
}

function selectNewEntity(e) {
  const new_entity_id = e.currentTarget.id;
  const current_entity = localStorage.getItem("current_entity");

  if (current_entity != new_entity_id) {
    localStorage.setItem("current_entity", new_entity_id);
    localStorage.setItem("previous_action_message", "Entity updated");
    window.scrollTo(0, 0);
    location.reload();
  }
}
