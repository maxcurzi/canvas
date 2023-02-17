import React, { useState, useRef } from 'react';
import Recaptcha from 'react-invisible-recaptcha';

const UserVerification = (props) => {
    const captchaRef = useRef(null);
    const [user, setUser] = useState("");

    const onSubmit = () => {
        captchaRef.current.execute();
        setUser("");
    }
    const onResolved= () => {
      alert( captchaRef.current.getResponse() );
    }

    return (
        <div>
          <input
            type="text"
            placeholder='Choose a username'
            value={ user }
            onChange={ event => setUser (event.target.value ) } />
              <button onClick={onSubmit} disabled={'' === user}>Submit</button>
          <Recaptcha
            ref={captchaRef}
            sitekey="6LfLzFckAAAAAJKw0slf6J2cydgGCD4J4mKEt-nu"
            onResolved={ onResolved } />
        </div>
      );
}

export default UserVerification;