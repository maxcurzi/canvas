import React, {useEffect, useState} from 'react';
import 'firebaseui/dist/firebaseui.css';
import {
  // getAuth,
  EmailAuthProvider,
  GoogleAuthProvider,
  signOut,
  onAuthStateChanged,
  sendEmailVerification,
} from 'firebase/auth';

var firebaseui = require('firebaseui');

const LogIn = (props) => {
  const [user, setUser] = useState(null)
  const [userVerified, setUserVerified] = useState(false)

  useEffect(() => {
    const uiConfig = {
      credentialHelper: firebaseui.auth.CredentialHelper.NONE,
      signInOptions: [
        // Email / Password Provider.
        EmailAuthProvider.PROVIDER_ID,
        {
          provider: GoogleAuthProvider.PROVIDER_ID,
          scopes: [
            'https://www.googleapis.com/auth/contacts.readonly'
          ],
          customParameters: {
            // Forces account selection even when one account
            // is available.
            prompt: 'select_account'
          }
        },
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

    if (user) {
    }
    else{
      const ui = firebaseui.auth.AuthUI.getInstance() || new firebaseui.auth.AuthUI(props.auth);
      ui.start('#firebaseui-auth-container', uiConfig);
    }
  },[user, props.auth])

  // Listen to the current Auth state
  onAuthStateChanged(props.auth, (user) => {
    setUser(user)
    if (user) {
      setUserVerified(user.emailVerified)
    }
  });

  return (
    <div>
      {user ? <button onClick={() => signOut(props.auth)}>LogOut</button> : <section className='authbox left-aligned' id={'firebaseui-auth-container'}></section>}
      {userVerified ? null : <h3 className='authbox left-aligned'>Verify your email and refresh this page to be able to play.</h3>}
    </div>
  )
}

export default LogIn;