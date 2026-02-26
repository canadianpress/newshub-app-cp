import { signInWithEmailAndPassword, signOut } from "firebase/auth";
import { auth } from "newsroom-core/assets/auth/firebase/init";

const form = document.getElementById("formLogin") as HTMLFormElement;
const firebaseStatus = document.getElementById(
  "firebase-status",
) as HTMLInputElement;
const params = new URLSearchParams(window.location.search);
if (params.get("email")) {
  form["email"].value = params.get("email");
}

const sendTokenToServer = (token: string) => {
  window.location.replace(`/firebase_auth_token?token=${token}`);
};

auth.onAuthStateChanged((user) => {
  if (user != null) {
    if (params.get("user_error") === "1") {
      return;
    }

    if (params.get("logout") === "1") {
      signOut(auth);
      return;
    }

    const tokenError = params.get("token_error");

    user.getIdToken(tokenError === "1").then(sendTokenToServer);
  }
});

form.onsubmit = (event) => {
  event.preventDefault();

  const data = new FormData(form);
  const email = data.get("email") as string;
  const password = data.get("password") as string;

  signInWithEmailAndPassword(auth, email, password)
    .then((userCredential) => userCredential.user.getIdToken())
    .then((token) => sendTokenToServer(token))
    .catch((reason) => {
      firebaseStatus.value = reason.code;
      form.submit();
    });

  return false;
};
