import AbstractView from "../AbstractView.js";
import { base_uri } from "../../constants.js";
import {
  callAPI,
  reloadMessage,
  displayMessageToUser,
  populate_aside_accounts,
  decode_jwt,
} from "../../common_funcs.js";

var jwt_global;
var amounts;
const subroute = "accounts";

const css_levels = ["level-0", "level-1", "level-2"];

export default class extends AbstractView {
  constructor() {
    super();
  }

  async getHtml() {
    return `<div class="reload-message"></div>
    <form id="form-keys">
      <div class="key-container">
        <ul class="master_type_key">
          <div class="key-sub-container">
            <li>
              <input type="radio" name="master_type_key" id="radio-asset-long" value="ASSET_LONG" checked>
              <label for="radio-asset-long">Assets, Long Term</label>
            </li>
            <li>
              <input type="radio" name="master_type_key" id="radio-asset-short" value="ASSET_SHORT">
              <label for="radio-asset-short">Assets, Short Term</label>
            </li>
            <li>
              <input type="radio" name="master_type_key" id="radio-asset-owed" value="ASSET_OWED">
              <label for="radio-asset-short">Assets, Owed</label>
            </li>
          </div>
          <div class="key-sub-container">
            <li>
              <input type="radio" name="master_type_key" id="radio-expense-operating" value="EXPENSE_OPERATING">
              <label for="radio-expense-operating">Expenses, Operating</label>
            </li>
            <li>
              <input type="radio" name="master_type_key" id="radio-expense-cogr" value="EXPENSE_COGR">
              <label for="radio-expense-cogr">Expenses, COGR</label>
            </li>
          </div>
          <div class="key-sub-container">
            <li>
              <input type="radio" name="master_type_key" id="radio-equity" value="EQUITY">
              <label for="radio-equity">Equity</label>
            </li>
            <li>
              <input type="radio" name="master_type_key" id="radio-liability" value="LIABILITY">
              <label for="radio-liability">Liability</label>
            </li>
            <li>
              <input type="radio" name="master_type_key" id="radio-income" value="INCOME">
              <label for="radio-income">Income</label>
            </li>
          </div>
        </ul>
      </div>  
      <button class="btn--form btn--cntr" id="btn-filter-refresh">Apply</button>
    </form>

    <h1 class="heading-primary" id="header-title">TBD</h1>
    <div class="table-overflow-wrapper">
      <table id="tree-table">
        <tr>
          <th>Account</th>
          <th>Amount</th>
        </tr>
      </table>
    </div>    
    `;
  }

  js(jwt) {
    // this variable is copied into the higher namespace so I can get it
    // into the delete function
    jwt_global = jwt;
    const current_entity = localStorage.getItem("current_entity");

    // check for reload message; if exists, display
    reloadMessage();

    populate_aside_accounts();

    // What do do on a submit
    const myForm = document.getElementById("form-keys");
    myForm.addEventListener("submit", function (e) {
      e.preventDefault();

      // Pull data from form and put it into the json format the DB wants
      const formData = new FormData(this);

      var object = {};
      formData.forEach((value, key) => (object[key] = value));

      // API route for this stats page
      const route =
        base_uri +
        "/" +
        subroute +
        "/master?entity_id=" +
        current_entity +
        "&" +
        new URLSearchParams(object).toString();

      callAPI(
        jwt,
        route,
        "GET",
        null,
        (account_tree_json) => {
          // Now call second function to get amounts
          const route2 =
            base_uri + "/" + subroute + "/amounts?entity_id=" + current_entity;

          callAPI(
            jwt,
            route2,
            "GET",
            null,
            (amounts_json) => {
              amounts = amounts_json;
              updateTitle(account_tree_json["name"], -99);
              populateTreeTable(account_tree_json["children"]);
            },
            displayMessageToUser
          );
        },
        displayMessageToUser
      );
    });
  }
}

function oneRow(table, level, account) {
  var tr = table.insertRow(-1);

  var tabCell = tr.insertCell(-1);
  tabCell.innerHTML = account["name"];
  tabCell.classList.add("left");
  tabCell.id = css_levels[level];

  var tabCell = tr.insertCell(-1);
  if (account["id"] in amounts) {
    tabCell.innerHTML = amounts[account["id"]];
  } else {
    tabCell.innerHTML = 0.0;
  }
  tabCell.classList.add("right");
  tabCell.id = css_levels[level];

  for (var i = 0; i < account["children"].length; i++) {
    oneRow(table, level + 1, account["children"][i]);
  }
}

function populateTreeTable(tree) {
  var table = document.getElementById("tree-table");

  // clear anything already in the table
  const rowCount = table.rows.length;
  for (let i = rowCount - 1; i > 0; i--) {
    table.deleteRow(i);
  }

  for (var i = 0; i < tree.length; i++) {
    oneRow(table, 0, tree[i]);
  }
}

function updateTitle(name, amount) {
  var title = document.getElementById("header-title");
  title.innerHTML = name + ", $" + amount;
}
