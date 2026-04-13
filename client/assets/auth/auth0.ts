import {
  Auth0Client,
  createAuth0Client,
  RedirectLoginOptions,
} from "@auth0/auth0-spa-js";

let auth0Client: Auth0Client;

async function initAuth0() {
  try {
    auth0Client = await createAuth0Client({
      domain: "cpe-stage.ca.auth0.com",
      clientId: "TDNfUa1qEqpm51LCFdNI6ryiihYJ40Y9",
      authorizationParams: {
        redirect_uri: "https://stgadmin.prgloo.com/cp",
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

async function login(
  loginHint: string | null,
  token: string | null,
  appState?: RedirectLoginOptions["appState"],
) {
  try {
    return await auth0Client.loginWithRedirect({
      authorizationParams: {
        ...(loginHint && { login_hint: loginHint }),
        ...(token && { token }),
      },
      appState,
    });
  } catch (err) {
    console.error(err);
  }
}

initAuth0();

export { login };
