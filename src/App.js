import './App.css';
import { firebaseApp } from './Firebase';
import React, { useState } from 'react';
import Grid from './components/Grid';
import LogIn from './components/LogIn';
import { getAuth, onAuthStateChanged } from 'firebase/auth';
import useWebSocket from 'react-use-websocket';
import CookieConsent from "react-cookie-consent";
import Share from './Share';

const WS_URL = 'wss://canvas.maxcurzi.com/wss/';
const SHAREURL = "Join me at www.pixels.today today!"
const gridSize = 64;
function App() {
  const [grid, setGrid] = useState(Array(gridSize * gridSize).fill(0));
  const [owners, setOwners] = useState(Array(gridSize * gridSize).fill(""));
  const { sendMessage, readyState, getWebSocket } = useWebSocket(WS_URL, {
    onOpen: () => {
      console.log('WebSocket connection established!');
    },
    onMessage: e => {
      let msg = JSON.parse(e.data)
      setGrid(msg.pixels)
      setOwners(msg.owners)
    },
    shouldReconnect: () => true,
  });
  const [user, setUser] = useState(null)
  const isAuthenticated = () => {
    return user !== null;
  }

  const auth = getAuth(firebaseApp);
  const webSocket = getWebSocket()
  onAuthStateChanged(auth, (user) => {
    if ((user) && (user.emailVerified)) {
      setUser(user)
    } else {
      setUser(null)
    }
  });

  return (
    <div className="App">
      <Grid height={gridSize} width={gridSize} imageData={grid} user={user} isAuthenticated={isAuthenticated} owners={owners} sendMessage={sendMessage} webSocket={webSocket} readyState={readyState} />
      <LogIn auth={auth} />
      <Share shareurl={SHAREURL} />
      <CookieConsent style={{ background: "#03C" }}>This website uses cookies to enhance the user experience.</CookieConsent>
    </div>
  );
}

export default App;
