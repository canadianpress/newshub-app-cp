import { Auth0Client, createAuth0Client } from "@auth0/auth0-spa-js";

let auth0Client: Auth0Client;

async function initAuth0() {
  try {
    auth0Client = await createAuth0Client({
      domain: process.env.AUTH0_DOMAIN,
      clientId: process.env.AUTH0_CLIENT_ID,
      authorizationParams: {
        redirect_uri: process.env.AUTH0_REDIRECT_URI,
      },
    });

    if (
      window.location.search.includes("code=") &&
      window.location.search.includes("state=")
    ) {
      await handleRedirectCallback();
    }
  } catch (err) {
    console.error(err);
  }
}

async function handleRedirectCallback() {
  try {
    await auth0Client.handleRedirectCallback();
    window.history.replaceState({}, document.title, window.location.pathname);
  } catch (err) {
    console.error(err);
  }
}

async function login(connection?: string) {
  try {
    return await auth0Client.loginWithRedirect({
      authorizationParams: { connection },
    });
  } catch (err) {
    console.error(err);
  }
}

initAuth0();

export { login };
