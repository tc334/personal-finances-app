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
          <ul class="filter-list">
            <li>
              <input type="radio" name="filter-date" id="radio-current-season" value="current-season" checked>
              <label for="radio-current-season">current season</label>
            </li>
            <li>
              <input type="radio" name="filter-date" id="radio-all-records" value="all-records">
              <label for="radio-all-records">all records</label>
            </li>
            <li>
              <input type="radio" name="filter-date" id="radio-custom-date" value="custom-range">
              <label for="radio-custom-date">custom date range:</label>
            </li>
          </ul>
          <div class="custom-date">
            <input type="date" class="inp-date-filter" value="2022-03-01" name="date-start" id="date-start">
            <label for="date-start">start</label>
          </div>
          <div class="custom-date">
            <input type="date" class="inp-date-filter" value="2023-03-01" name="date-end" id="date-end">
            <label for="date-end">end</label>
          </div>
        </section>
        <section class="filter-member">
          <ul class="filter-list">
            <li>
              <input type="radio" name="filter-member" id="radio-whole-club" value="whole-club" checked>
              <label for="radio-whole-club">whole club</label>
            </li>
            <li>
              <input type="radio" name="filter-member" id="radio-just-me" value="just-me">
              <label for="radio-just-me">just me</label>
            </li>
          </ul>
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

    // API route for this stats page
    const route2 = base_uri + "/" + subroute + "/?entity_id=" + current_entity;

    callAPI(
      jwt,
      route2,
      "GET",
      null,
      (data) => {
        console.log("ALPHA");
        console.log(data);
        populateTable(data["journal_entries"]);
      },
      displayMessageToUser
    );

    // What do do on a submit
    const myForm = document.getElementById("form-filter");
    myForm.addEventListener("submit", function (e) {
      e.preventDefault();

      // Pull data from form and put it into the json format the DB wants
      const formData = new FormData(this);

      var object = {};
      formData.forEach((value, key) => (object[key] = value));

      // API route for this stats page
      const route =
        base_uri +
        "/journal/get" +
        "?" +
        new URLSearchParams(object).toString();

      callAPI(
        jwt,
        route,
        "GET",
        null,
        (data) => {
          //console.log(data["stats"]);
          populateTable(data["stats"]);
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
