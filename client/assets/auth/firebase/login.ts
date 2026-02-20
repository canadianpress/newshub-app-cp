import { getAuth, signInWithEmailAndPassword } from "firebase/auth";
import { login as auth0Login } from "./auth0";

const auth = getAuth();

const form = document.getElementById("formLogin") as HTMLFormElement;
const firebaseStatus = document.getElementById(
  "firebase-status",
) as HTMLInputElement;

const sendTokenToServer = async (token: string) =>
  fetch(`/firebase_auth_token?token=${token}`);

form.onsubmit = (event) => {
  event.preventDefault();

  const data = new FormData(form);
  const email = data.get("email") as string;
  const password = data.get("password") as string;

  signInWithEmailAndPassword(auth, email, password)
    .then((userCredential) => userCredential.user.getIdToken())
    .then((token) => sendTokenToServer(token).then(() => token))
    .then((token) => auth0Login(token))
    .catch((reason) => {
      firebaseStatus.value = reason.code;
      form.submit();
    });

  return false;
};
