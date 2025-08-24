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
var account_list;

export default class extends AbstractView {
  constructor() {
    super();
  }

  async getHtml() {
    return `<div class="reload-message"></div>
    <h2 class="heading-secondary">new journal entry</h2>
    <form id="form-journal-entry">
      <div class="journal-entry-meta">
        <label class="heading-tertiary-no-bottom-margin">Date (YYYY-MM-DD)</label>
        <input type="text" id="journal-entry-date" style="min-width: 40ch" value="2025-02-01"></input>
        <label class="heading-tertiary-no-bottom-margin">Vendor (optional)</label>
        <input type="text" id="journal-entry-vendor" style="min-width: 40ch" value=""></input>
        <label class="heading-tertiary-no-bottom-margin">Description</label>
        <input type="text" id="journal-entry-description" style="min-width: 40ch" value="We pay for VRBO"></input>
      </div>
      <div class="journal-entry-main">
        <div class="journal-entry-column" id="debit">
          <div class="journal-entry-subheading">
            Debit
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
            Credit
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
            <button class="journal-entry-add-button" id="add-credit">
              Add
            </button>
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
    hook_up_add_button("credit");

    // What do do on a submit
    const myForm = document.getElementById("btn-new-journal-submit");
    myForm.addEventListener("click", function (e) {
      e.preventDefault();

      // Check for ledger balance
      /*
      const debitSum = document.getElementById("journal-entry-subtotal-debit");
      const creditSum = document.getElementById(
        "journal-entry-subtotal-credit"
      );
      if (
        currency_cleaner(debitSum.value) != currency_cleaner(creditSum.value)
      ) {
        alert("Debit and credit balances don't match.");
        return;
      }
      */

      // Pull data from form and put it into the json format the DB wants
      var post_data = {};

      post_data["new_journal_entry"] = {
        timestamp: document.getElementById("journal-entry-date").value,
        entity_id: current_entity,
        vendor: document.getElementById("journal-entry-vendor").value,
        description: document.getElementById("journal-entry-description").value,
      };

      post_data["ledger_list"] = gather_accounts("debit").concat(
        gather_accounts("credit")
      );

      console.log(post_data);
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
  // API route for this stats page
  const route =
    base_uri + "/accounts/list_of_accounts?entity_id=" + current_entity;

  callAPI(
    jwt,
    route,
    "GET",
    null,
    (data) => {
      account_list = data["accounts"];
      add_acount("journal-entry-data-container-debit");
      add_acount("journal-entry-data-container-credit");
    },
    displayMessageToUser
  );
}

function add_acount(id) {
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
  var btn_remove = document.createElement("button");
  btn_remove.innerHTML = "-";
  btn_remove.className += "btn--action";
  btn_remove.addEventListener("click", removeRow);
  new_div.appendChild(btn_remove);

  container.appendChild(new_div);
}

function hook_up_add_button(postfix) {
  var btn_add = document.getElementById("add-" + postfix);
  btn_add.addEventListener("click", add_listener);
  btn_add.dataset.parentId = "journal-entry-data-container-" + postfix;
}

function add_listener(e) {
  add_acount(e.currentTarget.dataset.parentId);
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
