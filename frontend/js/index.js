// functions, constants imported from other javascript files
import { base_uri } from "./constants.js";
import { callAPI, displayMessageToUser } from "./common_funcs.js";
import users from "./views/Settings/users.js";
import entities from "./views/Settings/entities.js";
import logout from "./views/Settings/u_logout.js";
import me from "./views/Settings/u_me.js";
import tree from "./views/Accounts/tree.js";

// only do this once
const jwt = localStorage.getItem("token");
if (!jwt) {
  // If there isn't a JWT present, kick user back to login
  location.href = "login.html";
}

const goto_route = async (view, jwt) => {
  document.querySelector("#div-main").innerHTML = await view.getHtml();
  view.js(jwt);
};

const router = async () => {
  const routes = [
    {
      path: "/",
      view: me,
    },
    {
      path: "#nav_settings",
      view: me,
    },
    {
      path: "#me",
      view: me,
    },
    {
      path: "#logout",
      view: logout,
    },
    {
      path: "#users",
      view: users,
    },
    {
      path: "#entities",
      view: entities,
    },
    {
      path: "#tree",
      view: tree,
    },
  ];

  // Test each route for potential match
  const potentialMatches = routes.map((route) => {
    return {
      route: route,
      isMatch: location.hash === route.path,
    };
  });

  let match = potentialMatches.find((potentialMatch) => potentialMatch.isMatch);

  // replace this my own custom 404
  if (!match) {
    match = {
      route: routes[0],
      isMatch: true,
    };
  }

  // for Hunts only, we have a branching view
  if (match.route.path == "#nav_hunt") {
    hunt_branch(jwt);
  } else {
    goto_route(new match.route.view(), jwt);
  }

  // This updates the view
  //const view = new match.route.view();
  //document.querySelector("#div-main").innerHTML = await view.getHtml();
  //view.js(jwt);
};

// call to router for initial page load
router();

// call to router for subsequent page loads
window.addEventListener("hashchange", function (e) {
  router();
});

// this is a special test used for the "Hunt" screen to route
// the page to either:
// signup-open, signup-closed, draw-complete: pre-hunt
// hunt-open: live-hunt
// else: no-hunt
function hunt_branch(jwt) {
  const route = base_uri + "/hunts/active";
  callAPI(
    jwt,
    route,
    "GET",
    null,
    (response_full_json) => {
      if (response_full_json["hunts"]) {
        const hunts_dict = response_full_json["hunts"];
        // logic
        if (hunts_dict.length == 1) {
          if (
            hunts_dict[0]["status"] == "signup_open" ||
            hunts_dict[0]["status"] == "signup_closed" ||
            hunts_dict[0]["status"] == "draw_complete"
          ) {
            goto_route(new h_pre(), jwt);
          } else if (hunts_dict[0]["status"] == "hunt_open") {
            goto_route(new h_live(), jwt);
          } else {
            goto_route(new h_no(), jwt);
          }
        } else {
          // this is an error condition. there should never be more than 1 hunt active
          goto_route(new h_no(), jwt);
        }
      } else {
        //console.log(data);
      }
    },
    displayMessageToUser
  );
}
