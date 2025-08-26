import AbstractView from "../AbstractView.js";
import { base_uri } from "../../constants.js";
import {
  callAPI,
  reloadMessage,
  displayMessageToUser,
  populate_aside_journal,
  currency_blur,
  currency_focus,
  currency_cleaner,
  currency_formatter,
} from "../../common_funcs.js";

const subroute = "journal";
var account_list_expense;

export default class extends AbstractView {
  constructor() {
    super();
  }

  async getHtml() {
    return `<div class="reload-message"></div>
    <h2 class="heading-secondary">simple expense entry</h2>
    <form id="form-journal-entry">
      <div class="journal-entry-meta">
        <label class="heading-tertiary-no-bottom-margin">Date (YYYY-MM-DD)</label>
        <input type="text" id="journal-entry-date" style="min-width: 40ch" value="2025-02-01"></input>
        <label class="heading-tertiary-no-bottom-margin">Vendor</label>
        <input type="text" id="journal-entry-vendor" style="min-width: 40ch" value=""></input>
        <label class="heading-tertiary-no-bottom-margin">Description</label>
        <input type="text" id="journal-entry-description" style="min-width: 40ch" value="We pay for VRBO"></input>
      </div>
      <div class="journal-entry-main">
        <div class="journal-entry-column" id="debit">
          <div class="journal-entry-subheading">
            expense categories
          </div>
          <div class="journal-entry-data">
            <div class="journal-entry-data-heading-container">
              <div class="heading-tertiary">
                Account
              </div>
              <div class="heading-tertiary">
                Amount
              </div>
            </div>
            <div class="journal-entry-data-container" id="journal-entry-data-container-debit">
            </div>
            <button class="journal-entry-add-button" id="add-debit">
              Add
            </button>
          </div>
          <div class="journal-entry-subtotal-container">
            <div class="heading-tertiary">
              subtotal
            </div>
            <div class="heading-tertiary journal-entry-subtotal" id="journal-entry-subtotal-debit">
              0.00
            </div>
          </div>
        </div>
        <div class="journal-entry-column" id="debit">
          <div class="journal-entry-subheading">
            payment method
          </div>
          <div class="journal-entry-data">
            <div class="journal-entry-data-heading-container">
              <div class="heading-tertiary">
                Account
              </div>
              <div class="heading-tertiary">
                Amount
              </div>
            </div>
            <div class="journal-entry-data-container" id="journal-entry-data-container-credit">
            </div>
          </div>
          <div class="journal-entry-subtotal-container">
            <div class="heading-tertiary">
              subtotal
            </div>
            <div class="heading-tertiary journal-entry-subtotal" id="journal-entry-subtotal-credit">
              0.00
            </div>
          </div>
        </div>
      </div>  
      <button class="btn--form btn--cntr" id="btn-new-journal-submit">Submit</button>
    </form>`;
  }

  js(jwt) {
    // check for reload message; if exists, display
    reloadMessage();

    populate_aside_journal();
    const current_entity = localStorage.getItem("current_entity");

    populateAccountList(jwt, current_entity);

    // connect "Add" buttons to their functions
    hook_up_add_button("debit");

    // What do do on a submit
    const submitButton = document.getElementById("btn-new-journal-submit");
    submitButton.addEventListener("click", function () {
      // Check for ledger balance
      const debitSum = document.getElementById("journal-entry-subtotal-debit");
      const creditSum = document.getElementById(
        "journal-entry-subtotal-credit"
      );
      if (
        currency_cleaner(debitSum.innerHTML) !=
        currency_cleaner(creditSum.innerHTML)
      ) {
        alert("Debit and credit balances don't match.");
        return;
      }

      // Pull data from form
      const entryDate = document.getElementById("journal-entry-date").value;
      const entryVendor = document.getElementById("journal-entry-vendor").value;
      const entryDescription = document.getElementById(
        "journal-entry-description"
      ).value;

      // Check that date, vendor, and description are all filled out
      if (
        entryDate.length < 1 ||
        entryVendor.length < 1 ||
        entryDescription.length < 1
      ) {
        alert("Incomplete Form!");
        return;
      }

      // Put data into the json format the DB wants
      var post_data = {};

      post_data["new_journal_entry"] = {
        timestamp: entryDate,
        entity_id: current_entity,
        vendor: entryVendor,
        description: entryDescription,
      };

      post_data["ledger_list"] = gather_accounts("debit").concat(
        gather_accounts("credit")
      );

      var json = JSON.stringify(post_data);

      const route = base_uri + "/" + subroute + "/";

      callAPI(
        jwt,
        route,
        "POST",
        json,
        (data) => {
          localStorage.setItem(
            "previous_action_message",
            "Journal entry successfully added."
          );
          window.scrollTo(0, 0);
          location.reload();
        },
        displayMessageToUser
      );
    });
  }
}

function populateAccountList(jwt, current_entity) {
  // Expense account list
  const route =
    base_uri +
    "/accounts/list_of_accounts?entity_id=" +
    current_entity +
    "&account_type=EXPENSE";

  callAPI(
    jwt,
    route,
    "GET",
    null,
    (data) => {
      account_list_expense = data["accounts"];
      add_account("journal-entry-data-container-debit");
    },
    displayMessageToUser
  );

  // Short term assets
  const route2 =
    base_uri +
    "/accounts/master_list?entity_id=" +
    current_entity +
    "&master_type_key=ASSET_SHORT" +
    "&b_only_childless=true";

  callAPI(
    jwt,
    route2,
    "GET",
    null,
    (data_assets) => {
      // Short term liabilities
      const route3 =
        base_uri +
        "/accounts/master_list?entity_id=" +
        current_entity +
        "&master_type_key=LIABILITY_SHORT" +
        "&b_only_childless=true";

      callAPI(
        jwt,
        route3,
        "GET",
        null,
        (data_liabilities) => {
          add_account_aux(
            "journal-entry-data-container-credit",
            data_assets["accounts"].concat(data_liabilities["accounts"]),
            false
          );
        },
        displayMessageToUser
      );
    },
    displayMessageToUser
  );
}

function add_account(id) {
  add_account_aux(id, account_list_expense, true);
}

function add_account_aux(id, account_list, b_removable) {
  var container = document.getElementById(id);
  var new_div = document.createElement("div");
  new_div.classList.add("journal-entry-data-row");
  new_div.id = Math.random().toString(36).substring(2, 8);

  // Account dropdown
  var new_select = document.createElement("select");
  new_select.classList.add("journal-entry-account-select");
  // add default "select account" option
  var new_opt = document.createElement("option");
  new_opt.innerHTML = "--select account--";
  new_opt.setAttribute("value", -1);
  new_select.appendChild(new_opt);
  for (var i = 0; i < account_list.length; i++) {
    var new_opt = document.createElement("option");
    new_opt.innerHTML = account_list[i]["account.name"];
    new_opt.setAttribute("value", account_list[i]["account.id"]);
    new_select.appendChild(new_opt);
  }
  new_select.setAttribute("value", -1); // sets to "select account"
  new_div.appendChild(new_select);

  // Amount entry field
  var new_input = document.createElement("input");
  new_input.classList.add("journal-entry-amount");
  //new_input.setAttribute("type", "number");
  new_input.setAttribute("step", "0.01");
  new_input.setAttribute("min", "0");
  new_input.addEventListener("focus", currency_focus);
  new_input.addEventListener("blur", currency_blur);
  new_input.addEventListener("blur", compute_subtotal_aux);
  new_div.appendChild(new_input);

  // Remove button
  if (b_removable == true) {
    var btn_remove = document.createElement("button");
    btn_remove.innerHTML = "-";
    btn_remove.className += "btn--action";
    btn_remove.addEventListener("click", removeRow);
    new_div.appendChild(btn_remove);
  }

  container.appendChild(new_div);
}

function hook_up_add_button(postfix) {
  var btn_add = document.getElementById("add-" + postfix);
  btn_add.addEventListener("click", add_listener);
  btn_add.dataset.parentId = "journal-entry-data-container-" + postfix;
}

function add_listener(e) {
  add_account(e.currentTarget.dataset.parentId);
}

function removeRow(e) {
  const removeButton = e.currentTarget;
  const rowDiv = removeButton.parentElement;
  const listDiv = rowDiv.parentElement;
  listDiv.removeChild(rowDiv);
  compute_subtotal(listDiv);
}

function compute_subtotal_aux(event) {
  const thisInput = event.target;
  const this_row = thisInput.parentElement;
  const row_parent = this_row.parentElement;
  compute_subtotal(row_parent);
}

function compute_subtotal(row_parent) {
  const row_list = row_parent.children;
  var subtotal = 0.0;
  for (var i = 0; i < row_list.length; i++) {
    const amountInput = row_list[i].querySelectorAll(".journal-entry-amount");
    const temp = currency_cleaner(amountInput[0].value);
    subtotal += temp;
  }
  const row_grandparent = row_parent.parentElement;
  const row_greatgrandparent = row_grandparent.parentElement;
  const container = row_greatgrandparent.querySelector(
    ".journal-entry-subtotal-container"
  );
  const subtotalElement = container.querySelector(".journal-entry-subtotal");
  subtotalElement.innerHTML = currency_formatter(subtotal);
}

function gather_accounts(postfix) {
  const row_list = document.getElementById(
    "journal-entry-data-container-" + postfix
  ).children;
  var ledger_list = [];
  for (var i = 0; i < row_list.length; i++) {
    const amountInput = row_list[i].querySelector(".journal-entry-amount");
    if (amountInput == "") {
      alert("Cannot have blank amount for any account");
      return;
    }
    const amount = currency_cleaner(amountInput.value);
    if (amount <= 0.0) {
      alert("Cannot have negative or zero amount");
      return;
    }

    const accountSelector = row_list[i].querySelector(
      ".journal-entry-account-select"
    );
    const account_id = accountSelector.value;
    if (account_id == -1) {
      alert("Invalid account selected");
      return;
    }

    const ledger = {
      amount: amount,
      direction: postfix.toUpperCase(),
      account_id: account_id,
    };

    ledger_list.push(ledger);
  }
  return ledger_list;
}
