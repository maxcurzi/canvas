import './App.css';
import Grid from './components/Grid';
import './websafe_colors.css'
import { firebaseApp, resetGrid } from './Firebase';
import { useState } from 'react';

import LogIn from './components/LogIn';
import { getAuth, onAuthStateChanged } from 'firebase/auth';

import { getPerformance } from "firebase/performance";


function App() {
  const [user, setUser] = useState(null)
  const gridSize = 64;
  const isAuthenticated = () => {
    return user !== null;
  }
  const auth = getAuth(firebaseApp);

  const perf = getPerformance(firebaseApp);
  onAuthStateChanged(auth, (user) => {
    if ((user) && (user.emailVerified)) {
        setUser(user)
      } else {
        setUser(null)
    }
});
  return (
    <div className="App">
      <Grid isAuthenticated={isAuthenticated} gridSize={gridSize} user={user} />
      {user && user.uid === "UNWpWi32gPXW35xGEM08l2Tli9i2" ? <button onClick={function () { if (user !== null) { resetGrid(gridSize) } }}>Reset</button> : null}
      <LogIn auth={auth} />
    </div>
  );
}

export default App;