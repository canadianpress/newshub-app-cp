const config = require("newsroom-core/webpack.config");

config.entry.home_js = [
  config.entry.home_js,
  "./assets/auth/pr-manager-sso.ts",
];
config.entry.firebase_login_js = "./assets/auth/firebase/login.ts";

module.exports = config;
