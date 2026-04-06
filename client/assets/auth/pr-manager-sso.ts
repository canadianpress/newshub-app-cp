import { signInWithCustomToken } from "firebase/auth";
import { auth } from "newsroom-core/assets/auth/firebase/init";
import { getConfig } from "newsroom-core/assets/utils";
import { login } from "./auth0";

const handlePrManagerClick = (event: Event) => {
  event.preventDefault();
  fetch("/firebase_credentials")
    .then((r) => r.json())
    .then(({ token }) => signInWithCustomToken(auth, token))
    .then((userCredential) =>
      userCredential.user
        .getIdToken()
        .then((token) => ({ email: userCredential.user.email, token })),
    )
    .then(({ email, token }) => login(email, token))
    .catch(() => login(null, null));
};

const prManagerObserver = new MutationObserver((_, observer) => {
  const element = document.querySelector(
    '[data-test-id="sidenav-link-pr_manager"]',
  );
  if (element) {
    observer.disconnect();
    element.addEventListener("click", handlePrManagerClick);
  }
});

const element = document.querySelector(
  '[data-test-id="sidenav-link-pr_manager"]',
);
if (element) {
  element.addEventListener("click", handlePrManagerClick);
} else if (getConfig("prManagerSidenavEnabled")) {
  prManagerObserver.observe(document.body, {
    childList: true,
    subtree: true,
  });
}
