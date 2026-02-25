import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";

declare const firebaseConfig: {
  apiKey: string;
  authDomain: string;
  projectId: string;
  messagingSenderId: string;
};

export const app = initializeApp(firebaseConfig);
export const auth = getAuth();
