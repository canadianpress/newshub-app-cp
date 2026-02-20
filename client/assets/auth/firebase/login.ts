import { getAuth, signInWithEmailAndPassword } from "firebase/auth";

const form = document.getElementById("formLogin") as HTMLFormElement;
const firebaseStatus = document.getElementById(
  "firebase-status",
) as HTMLInputElement;

const sendTokenToServer = async (token: string) =>
  fetch(`/firebase_auth_token?token=${token}`);

if (form)
  form.onsubmit = (event) => {
    event.preventDefault();
    const data = new FormData(form);
    const email = data.get("email") as string;
    const password = data.get("password") as string;

    signInWithEmailAndPassword(getAuth(), email, password)
      .then((userCredential) => userCredential.user.getIdToken())
      .then((token) => sendTokenToServer(token).then(() => token))
      .then((token) => {
        localStorage.setItem("fb_email", email);
        localStorage.setItem("fb_token", token);
        window.location.replace("/");
      })
      .catch((reason) => {
        firebaseStatus.value = reason.code;
        form.submit();
      });

    return false;
  };
