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
  const [userVerified, setUserVerified] = useState(false)
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
    setUser(user)
    if (user) {
      setUserVerified(user.emailVerified)
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
    <div>
      {user ? <button onClick={() => signOut(props.auth)}>Logout</button> : <section className='authbox left-aligned' id={'firebaseui-auth-container'}></section>}
      {userVerified ? <h3></h3> : <h3 className='authbox left-aligned'>Verify your email and refresh this page to be able to play.</h3>}
    </div>
  )
}

export default LogIn;