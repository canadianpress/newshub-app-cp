import { login } from "./auth0";

const handlePrManagerClick = (event: Event) => {
  event.preventDefault();
  const target = event.currentTarget as HTMLAnchorElement;
  const destination = target.href;
  login(localStorage.getItem("fb_email"), localStorage.getItem("fb_token"), {
    redirectTo: destination,
  });
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
if (element) element.addEventListener("click", handlePrManagerClick);
else
  prManagerObserver.observe(document.body, {
    childList: true,
    subtree: true,
  });
