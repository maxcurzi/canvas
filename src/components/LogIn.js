import React, {useEffect, useState} from 'react';
import 'firebaseui/dist/firebaseui.css';
import {
  EmailAuthProvider,
  signOut,
  onAuthStateChanged,
  sendEmailVerification,
} from 'firebase/auth';

import * as firebaseui from "firebaseui"

const LogIn = (props) => {
  const [user, setUser] = useState(null)
  const [userVerified, setUserVerified] = useState(false)

  useEffect(() => {
    const uiConfig = {
      credentialHelper: firebaseui.auth.CredentialHelper.NONE,
      signInOptions: [
        EmailAuthProvider.PROVIDER_ID,
      ],
      callbacks: {
        signInSuccessWithAuthResult: function (authResult) {
          var user = authResult.user;
          if (authResult.additionalUserInfo.isNewUser)
          {
            sendEmailVerification(user);
          }
          return false;
        },
      },
    };

    if (user===null) {
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
      {userVerified ? null : <h3 className='authbox center-aligned'>Verify your email and refresh this page to be able to play.</h3>}
    </div>
  )
}

export default LogIn;