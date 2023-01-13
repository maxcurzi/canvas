import React, { useState , useEffect} from 'react'
import {
    getAuth,
    EmailAuthProvider,
    GoogleAuthProvider,
    signInWithPopup,
    signOut,
    onAuthStateChanged,
} from 'firebase/auth';
import { firebaseApp } from '../Firebase';
const Login = () => {
    const auth = getAuth(firebaseApp);
    const signInWithGoogle = () => {
        // Sign in using a popup.
        const provider = new GoogleAuthProvider();
        const result = signInWithPopup(auth, provider);
        console.log(result);

        // The signed-in user info.
        const user = result.user;
        console.log(user);
    };
    return (
        <div className="login-buttons">
            <button onClick={signInWithGoogle}>
                <img src="https://developers.google.com/static/identity/images/btn_google_signin_light_normal_web.png" alt="google icon" />
            </button>
        </div>
    )
};

export default Login