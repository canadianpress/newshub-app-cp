import { signInWithCustomToken } from "firebase/auth";
import { auth } from "newsroom-core/assets/auth/firebase/init";
import { login } from "./auth0";

declare const prManagerEnabled: boolean;

const handlePrManagerClick = (event: Event) => {
  event.preventDefault();
  const target = event.currentTarget as HTMLAnchorElement;
  const destination = target.href;
  fetch("/firebase_credentials")
    .then((r) => r.json())
    .then(({ token }) => signInWithCustomToken(auth, token))
    .then((userCredential) =>
      userCredential.user
        .getIdToken()
        .then((token) => ({ email: userCredential.user.email, token })),
    )
    .then(({ email, token }) =>
      login(email, token, {
        redirectTo: destination,
      }),
    )
    .catch(() => login(null, null, { redirectTo: destination }));
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
} else if (prManagerEnabled) {
  prManagerObserver.observe(document.body, {
    childList: true,
    subtree: true,
  });
}
