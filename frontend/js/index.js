// functions, constants imported from other javascript files
import { base_uri } from "./constants.js";
import { callAPI, displayMessageToUser } from "./common_funcs.js";
import users from "./views/Settings/users.js";
import entities from "./views/Settings/entities.js";
import logout from "./views/Settings/u_logout.js";
import me from "./views/Settings/u_me.js";
import tree from "./views/Accounts/tree.js";
import journal_view from "./views/Journal/journal_view.js";
import journal_new from "./views/Journal/journal_new.js";
import journal_simple from "./views/Journal/journal_simple.js";

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
    {
      path: "#nav_journal",
      view: journal_view,
    },
    {
      path: "#nav_journal_new",
      view: journal_new,
    },
    {
      path: "#nav_journal_simple",
      view: journal_simple,
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

  goto_route(new match.route.view(), jwt);
};

// call to router for initial page load
router();

// call to router for subsequent page loads
window.addEventListener("hashchange", function (e) {
  router();
});
