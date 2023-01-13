import './App.css';
import Grid from './components/Grid';
import { firebaseApp, resetGrid } from './Firebase';
import { useState } from 'react';

import Login from './components/Login'
import { BrowserRouter as Router, Switch, Route } from 'react-router-dom'
import LogIn from './components/LogIn';
import { getAuth, onAuthStateChanged } from 'firebase/auth';


function App() {
  const [user, setUser] = useState(null)
  const isAuthenticated = () => {
    return user !== null;
  }
  const auth = getAuth(firebaseApp);
  onAuthStateChanged(auth, (user) => {
    if ((user) && (user.emailVerified)) {
        setUser(user)
      } else {
        setUser(null)
    }
});
  return (
    <div className="App">
      <Grid isAuthenticated={isAuthenticated}/>
      <button onClick={function () { if (user!==null) {resetGrid(32)} }}>Reset</button>
      <LogIn auth={auth} />
    </div>
  );
}

export default App;
