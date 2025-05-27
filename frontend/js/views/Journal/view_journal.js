import AbstractView from "../AbstractView.js";
import { base_uri } from "../../constants.js";
import {
  callAPI,
  reloadMessage,
  displayMessageToUser,
  populate_aside_journal,
  round,
  removeAllChildNodes,
  sortTable,
} from "../../common_funcs.js";

const subroute = "journal";

export default class extends AbstractView {
  constructor() {
    super();
  }

  async getHtml() {
    return `<div class="reload-message"></div>
    <h2 class="heading-secondary">Filters</h2>
    <form id="form-filter">
      <div class="filter-container">
        <section class="filter-date">
          <div class="custom-date">
            <input type="checkbox" name="chk-filter-date" id="chk-filter-date">
            <label for="filter-date">Transaction Dates</label>
          </div>
          <div class="custom-date">
            <input type="date" class="inp-date-filter" value="2025-01-01" name="date-start" id="date-start">
            <label for="date-start">start</label>
          </div>
          <div class="custom-date">
            <input type="date" class="inp-date-filter" value="2030-01-01" name="date-end" id="date-end">
            <label for="date-end">end</label>
          </div>
        </section>
        <section class="filter-max-ret-val">
          <ul class="filter-list">
            <li>
              <input type="radio" name="filter-max-ret-val" id="radio-max-1000" value="1000" checked>
              <label for="radio-max-1000">Max 1000</label>
            </li>
            <li>
              <input type="radio" name="filter-max-ret-val" id="radio-max-100" value="100">
              <label for="radio-just-me">Max 100</label>
            </li>
            <li>
              <input type="radio" name="filter-max-ret-val" id="radio-max-10" value="10">
              <label for="radio-just-me">Max 10</label>
            </li>
          </ul>
        </section>
        <section class="filter-account">
          <label for="select-account">Specific Account</label>
          <select id="select-account" name="account_id" style="margin-top:0.5em">
            <option value=-1>--select account--</option>
          </select>
        </section>
      </div>  
      <button class="btn--form btn--cntr" id="btn-filter-refresh">Apply</button>
    </form>
    <h1 class="heading-primary" id="stats-heading">Journal Entries</h1>
    <div class="table-overflow-wrapper">
      <table id="data-table">
        <thead>
          <tr>
            <th>date</th>
            <th>user</th>
            <th>vendor</th>
            <th>description</th>
            <th>debits</th>
            <th>credits</th>
          </tr>
        </thead>
        <tbody id="tb-journal">
        </tbody>
      </table>
    </div>`;
  }

  js(jwt) {
    // check for reload message; if exists, display
    reloadMessage();

    populate_aside_journal();
    const current_entity = localStorage.getItem("current_entity");

    populateAccountList(jwt, current_entity);

    // What do do on a submit
    const myForm = document.getElementById("form-filter");
    myForm.addEventListener("submit", function (e) {
      e.preventDefault();

      // Pull data from form and put it into the json format the DB wants
      const formData = new FormData(this);

      var object = {};
      formData.forEach((value, key) => (object[key] = value));

      // API route for this stats page
      var query_str = "entity_id=" + current_entity;

      // Append account query, if an account is selected
      const select_accounts = document.getElementById("select-account");
      if (select_accounts.value != -1) {
        query_str += "&account_name=" + select_accounts.value;
      }

      // Check which return value count limit radio button is selected
      var ele = document.getElementsByName("filter-max-ret-val");
      for (var i = 0; i < ele.length; i++) {
        if (ele[i].checked) query_str += "&max_rows=" + ele[i].value;
      }

      // Add date constraints, if selected
      const chk_custom_date = document.getElementById("chk-filter-date");
      if (chk_custom_date.checked == true) {
        const start_date = document.getElementById("date-start");
        query_str += "&start_date=" + start_date.value;
        const stop_date = document.getElementById("date-end");
        query_str += "&stop_date=" + stop_date.value;
      }

      const route = base_uri + "/" + subroute + "/?" + query_str;

      callAPI(
        jwt,
        route,
        "GET",
        null,
        (data) => {
          populateTable(data["journal_entries"]);
        },
        displayMessageToUser
      );
    });
  }
}

function nestedTable(entries) {
  var html = "<table class='inner-table'>";
  for (var i = 0; i < entries.length; i++) {
    html +=
      "<tr><td style='background-color:#fff'>" +
      entries[i]["account"] +
      "</td><td class='cell-fixed-width-2' style='background-color:#fff'>" +
      entries[i]["amount"] +
      "</td></tr>";
  }
  html += "</table>";
  return html;
}

function populateTable(db_data) {
  var table = document.getElementById("tb-journal");
  removeAllChildNodes(table);

  for (var i = 0; i < db_data.length; i++) {
    var tr = table.insertRow(-1);

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["date"];

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["user"];

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["vendor"];

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = db_data[i]["description"];

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = nestedTable(db_data[i]["debits"]);

    var tabCell = tr.insertCell(-1);
    tabCell.innerHTML = nestedTable(db_data[i]["credits"]);
  }
}

function populateAccountList(jwt, current_entity) {
  // API route for this stats page
  const route =
    base_uri + "/accounts/list_of_names?entity_id=" + current_entity;

  callAPI(
    jwt,
    route,
    "GET",
    null,
    (data) => {
      populateAccountList_aux(data["account_names"]);
    },
    displayMessageToUser
  );
}

function populateAccountList_aux(db_data) {
  // sort alphabetically
  db_data.sort(function (left, right) {
    return left > right ? 1 : -1;
  });
  const select_accounts = document.getElementById("select-account");
  for (var i = 0; i < db_data.length; i++) {
    var new_opt = document.createElement("option");
    new_opt.innerHTML = db_data[i];
    select_accounts.appendChild(new_opt);
  }
}
