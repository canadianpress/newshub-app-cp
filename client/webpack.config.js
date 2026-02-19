const config = require('newsroom-core/webpack.config');

config.entry.firebase_login_js = [config.entry.firebase_login_js, './assets/auth/firebase/login.ts'];

module.exports = config;
