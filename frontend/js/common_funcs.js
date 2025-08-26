export function callAPI(jwt, route, method, body, func_success, func_fail) {
  let h = new Headers();
  h.append("Accept", "application/json");
  h.append("Authorization", "Bearer " + jwt);

  if (method == "POST" || method == "PUT") {
    h.append("Content-Type", "application/json");
  }

  fetch(route, {
    method: method,
    headers: h,
    body: body,
  })
    .then(async (response) => {
      const isJson = response.headers
        .get("content-type")
        ?.includes("application/json");
      // if response is type 204, there is no data (per spec)
      const data =
        isJson & (response.status != 204) ? await response.json() : null;

      if (!response.ok) {
        const back_end_error_detail =
          "error " + response.status + ", " + data["detail"];

        // There are some error codes we want to take specific actions against
        if (response.status == 401) {
          //Authentication failed. Sending you back to the login page
          const specific_error_message =
            "Error 401 (authentication). Redirecting to login.";
          func_fail(specific_error_message + " " + back_end_error_detail);
          alert(specific_error_message + " " + back_end_error_detail);
          location.href = "login.html";
          return Promise.reject(error);
        } else {
          // Generic error
          console.log(back_end_error_detail);
          func_fail(back_end_error_detail);
          return Promise.reject(back_end_error_detail);
        }
      }

      // if you reached here, response is "ok"
      if (isJson) {
        func_success(data);
      }
    })
    .catch((err) => {
      console.log("HOTEL");
      console.log(err);
    });
}

export function decode_jwt(jwt_in, property = "level") {
  var tokens = jwt_in.split(".");
  const jwt_content = JSON.parse(atob(tokens[1]));
  return jwt_content[property];
}

// Populate the aside depending on user level
export function populate_aside_settings(user_level) {
  // start by clearing the aside
  removeAllChildNodes(document.getElementById("aside-content"));

  // data
  const headings = ["users", "admins"];

  const icons = {
    users: ["img/user.png", "img/log-out.png"],
    admins: ["img/user.png", "img/building.png"],
  };

  const text = {
    users: ["me", "log out"],
    admins: ["users", "entities"],
  };

  const links = {
    users: ["#me", "#logout"],
    admins: ["#users", "#entities"],
  };

  var idx_in = headings.indexOf(user_level);
  if (idx_in == -1) {
    idx_in = headings.length - 1;
  }

  for (var i = 0; i < headings.length; i++) {
    if (i <= idx_in) {
      populateOneLevel(
        headings[i],
        text[headings[i]],
        icons[headings[i]],
        links[headings[i]]
      );
    }
  }

  document.getElementById("main").classList.remove("menu-open");
  document.getElementById("aside-content").style.display = "block";
  document
    .getElementById("btn-aside-menu")
    .addEventListener("click", menuSwitcher);
}

export function populate_aside_accounts() {
  // start by clearing the aside
  removeAllChildNodes(document.getElementById("aside-content"));

  // data
  const headings = [
    "assets",
    "expenses",
    "liabilities",
    "equity",
    "income",
    "dividends",
  ];

  const icons = {
    assets: ["img/cog-wheel.png", "img/cog-wheel.png", "img/cog-wheel.png"],
    expenses: ["img/cog-wheel.png", "img/cog-wheel.png"],
    liabilities: ["img/cog-wheel.png"],
    equity: ["img/cog-wheel.png"],
    income: ["img/cog-wheel.png"],
    dividends: ["img/cog-wheel.png"],
  };

  const text = {
    assets: ["long-term", "short-term", "owed"],
    expenses: ["operating", "COGR"],
    liabilities: ["liabilities"],
    equity: ["equity"],
    income: ["income"],
    dividends: ["dividends"],
  };

  const links = {
    assets: ["#tree", "#tree", "#tree"],
    expenses: ["#tree", "#tree"],
    liabilities: ["#tree"],
    equity: ["#tree"],
    income: ["#tree"],
    dividends: ["#tree"],
  };

  for (var i = 0; i < headings.length; i++) {
    populateOneLevel(
      headings[i],
      text[headings[i]],
      icons[headings[i]],
      links[headings[i]]
    );
  }

  document.getElementById("main").classList.remove("menu-open");
  document.getElementById("aside-content").style.display = "block";
  document
    .getElementById("btn-aside-menu")
    .addEventListener("click", menuSwitcher);
}

// Populate the alternate aside for the stats menu
export function populate_aside_journal() {
  // start by clearing the aside
  removeAllChildNodes(document.getElementById("aside-content"));

  // data
  const headings = ["journal"];

  const icons = {
    journal: ["img/add_circle.png", "img/easy.png", "img/paper.png"],
  };

  const text = {
    journal: ["new entry", "simple expense entry", "view journal"],
  };

  const links = {
    journal: ["#nav_journal_new", "#nav_journal_simple", "#nav_journal"],
  };

  const idx_in = 1;

  for (var i = 0; i < headings.length; i++) {
    if (i <= idx_in) {
      populateOneLevel(
        headings[i],
        text[headings[i]],
        icons[headings[i]],
        links[headings[i]]
      );
    }
  }

  document.getElementById("main").classList.remove("menu-open");
  document.getElementById("aside-content").style.display = "block";
  document
    .getElementById("btn-aside-menu")
    .addEventListener("click", menuSwitcher);
}

function populateOneLevel(heading, text, images, links) {
  var aside = document.getElementById("aside-content");

  // heading
  var div = document.createElement("div");
  div.className += "aside-heading";
  div.innerHTML = heading;
  aside.appendChild(div);

  // unordered list
  var ul = document.createElement("ul");
  ul.className = "aside-list";

  // links
  for (var i = 0; i < text.length; i++) {
    // icon image
    var img = document.createElement("img");
    img.className = "aside-icon";
    img.src = images[i];

    // navigation text
    div = document.createElement("div");
    div.className = "aside-item-text";
    div.innerHTML = text[i];

    // anchor
    var a = document.createElement("a");
    a.href = links[i];
    a.appendChild(img);
    a.appendChild(div);

    // list item
    var li = document.createElement("li");
    li.appendChild(a);

    ul.appendChild(li);
  }

  aside.appendChild(ul);
}

export function removeAllChildNodes(parent) {
  while (parent.firstChild) {
    parent.removeChild(parent.firstChild);
  }
}

export function displayMessageToUser(msg) {
  document.querySelector(".reload-message").innerHTML = msg;
}

export function reloadMessage() {
  // check for reload message; if exists, display
  const new_msg = localStorage.getItem("previous_action_message");
  if (new_msg) {
    document.querySelector(".reload-message").innerHTML = new_msg;
    localStorage.removeItem("previous_action_message");
  }
}

export const formatDate = (date) => {
  let d = new Date(date);
  let month = (d.getMonth() + 1).toString();
  let day = d.getDate().toString();
  let year = d.getFullYear();
  if (month.length < 2) {
    month = "0" + month;
  }
  if (day.length < 2) {
    day = "0" + day;
  }
  return [year, month, day].join("-");
};

export function dateConverter_http(from_db, month_first = false) {
  // converts HTTP date to year, month, day w/o regard to timezone
  const myArray = from_db.split(" ");
  const year = myArray[3];
  const day = myArray[1];
  const month_long = myArray[2];
  if (month_first) {
    return monthConverter(month_long) + "/" + day + "/" + year;
  } else {
    return year + "-" + monthConverter(month_long) + "-" + day;
  }
}

export function dateConverter_iso(from_db, month_first = false) {
  // converts HTTP date to year, month, day w/o regard to timezone
  const myArray = from_db.split("-");
  const year = myArray[0];
  const day = myArray[2];
  const month = myArray[1];
  if (month_first) {
    return month + "/" + day + "/" + year;
  } else {
    return year + "-" + month_long + "-" + day;
  }
}

export function monthConverter(month_long) {
  if (month_long == "Jan") return "01";
  else if (month_long == "Feb") return "02";
  else if (month_long == "Mar") return "03";
  else if (month_long == "Apr") return "04";
  else if (month_long == "May") return "05";
  else if (month_long == "Jun") return "06";
  else if (month_long == "Jul") return "07";
  else if (month_long == "Aug") return "08";
  else if (month_long == "Sep") return "09";
  else if (month_long == "Oct") return "10";
  else if (month_long == "Nov") return "11";
  else if (month_long == "Dec") return "12";
  else return "00";
}

export function sortIndexes(test) {
  var test_with_index = [];
  test.forEach((element, index) => test_with_index.push([element, index]));
  test_with_index.sort(function (left, right) {
    return left[0] > right[0] ? -1 : 1;
  });
  var indexes = [];
  //test = [];
  for (var j in test_with_index) {
    //test.push(test_with_index[j][0]);
    indexes.push(test_with_index[j][1]);
  }
  return indexes;
}

export function round(value, precision) {
  var multiplier = Math.pow(10, precision || 0);
  return Math.round(value * multiplier) / multiplier;
}

export function sortTable(e) {
  const id = "data-table";
  const n = e.currentTarget.column_index;
  const is_numeric = e.currentTarget.is_numeric;
  var table,
    rows,
    switching,
    i,
    x,
    y,
    shouldSwitch,
    dir,
    temp1,
    temp2,
    switchcount = 0;
  table = document.getElementById(id);
  switching = true;
  // Set the sorting direction to ascending:
  dir = "asc";
  /* Make a loop that will continue until
  no switching has been done: */
  while (switching) {
    // Start by saying: no switching is done:
    switching = false;
    rows = table.rows;
    /* Loop through all table rows (except the
    first, which contains table headers): */
    for (i = 1; i < rows.length - 1; i++) {
      // Start by saying there should be no switching:
      shouldSwitch = false;
      /* Get the two elements you want to compare,
      one from current row and one from the next: */
      x = rows[i].getElementsByTagName("TD")[n];
      y = rows[i + 1].getElementsByTagName("TD")[n];
      /* Check if the two rows should switch place,
      based on the direction, asc or desc: */
      if (is_numeric) {
        temp1 = +x.innerHTML;
        temp2 = +y.innerHTML;
      } else {
        temp1 = x.innerHTML.toLowerCase();
        temp2 = y.innerHTML.toLowerCase();
      }
      if (dir == "asc") {
        if (temp1 > temp2) {
          // If so, mark as a switch and break the loop:
          shouldSwitch = true;
          break;
        }
      } else if (dir == "desc") {
        if (temp1 < temp2) {
          // If so, mark as a switch and break the loop:
          shouldSwitch = true;
          break;
        }
      }
    }
    if (shouldSwitch) {
      /* If a switch has been marked, make the switch
      and mark that a switch has been done: */
      rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
      switching = true;
      // Each time a switch is done, increase this count by 1:
      switchcount++;
    } else {
      /* If no switching has been done AND the direction is "asc",
      set the direction to "desc" and run the while loop again. */
      if (switchcount == 0 && dir == "asc") {
        dir = "desc";
        switching = true;
      }
    }
  }
}

export function menuSwitcher() {
  var main_main = document.getElementById("main");
  if (main_main.classList.contains("menu-open")) {
    main_main.classList.remove("menu-open");
  } else {
    main_main.classList.add("menu-open");
  }
}

export function selectAll(e) {
  var input = e.currentTarget;
  var len_of_val = input.value.length;
  input.setSelectionRange(0, len_of_val);
}

export function currency_blur(e) {
  this.value = currency_formatter(this.value);
}

export function currency_formatter(clean) {
  let value = parseFloat(clean);
  if (!isNaN(value)) {
    return value.toLocaleString("en-US", {
      style: "currency",
      currency: "USD",
    });
  } else {
    return clean;
  }
}

export function currency_focus(e) {
  this.value = currency_cleaner(this.value);
}

export function currency_cleaner(dirty) {
  let value = dirty.replace(/[^0-9.-]+/g, ""); // Remove non-numeric characters
  return parseFloat(value) || ""; // Convert back to number or clear if invalid
}
