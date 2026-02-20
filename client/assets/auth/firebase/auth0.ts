import { Auth0Client, createAuth0Client } from "@auth0/auth0-spa-js";

let auth0Client: Auth0Client;

async function initAuth0() {
  try {
    auth0Client = await createAuth0Client({
      domain: "",
      clientId: "",
      authorizationParams: {
        redirect_uri: "http://localhost:5050",
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

async function login(token: string) {
  try {
    return await auth0Client.loginWithRedirect({ authorizationParams: { token } });
  } catch (err) {
    console.error(err);
  }
}

initAuth0();

export { login };
