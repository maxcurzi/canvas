import React, {useEffect, useState} from 'react';
import * as firebaseui from 'firebaseui';
import 'firebaseui/dist/firebaseui.css';
import {
    getAuth,
    EmailAuthProvider,
    GoogleAuthProvider,
    signOut,
    onAuthStateChanged,
    sendEmailVerification,
} from 'firebase/auth';

const LogIn = (props) => {
    const [user, setUser] = useState(null)
    useEffect(() => {
        if (user){
        }
        else{
            const ui = firebaseui.auth.AuthUI.getInstance() || new firebaseui.auth.AuthUI(props.auth);
            ui.start('#firebaseui-auth-container', uiConfig);
        }
    })

    // Listen to the current Auth state
    onAuthStateChanged(props.auth, (user) => {
        if ((user) && (user.emailVerified)) {
            setUser(user)
        } else {
            setUser(null)
        }
    });

    const uiConfig = {
        credentialHelper: firebaseui.auth.CredentialHelper.NONE,
        signInOptions: [
          // Email / Password Provider.
          EmailAuthProvider.PROVIDER_ID,
        ],
        callbacks: {
            signInSuccessWithAuthResult: function (authResult, redirectUrl) {
                var user = authResult.user;
                if (authResult.additionalUserInfo.isNewUser)
                {
                    sendEmailVerification(user);
                }
                // Handle sign-in.
                return false;
            },
        },
    };

    return (
        <div className='authbox'>
            {user ? <button onClick={() => signOut(props.auth)}>Logout</button> : <section id={'firebaseui-auth-container'}></section>}
            {user ? <h3></h3> : <h3>Log in and verify your email to be able to update the grid.</h3>}
        </div>
    )
}

export default LogIn