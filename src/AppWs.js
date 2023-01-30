import './App.css';
import GridWs from './components/GridWs';
import './websafe_colors.css'
import { firebaseApp, resetGrid } from './Firebase';
import React, { useState } from 'react';
import Image from './components/GridWs2';
import LogIn from './components/LogIn';
import { getAuth, onAuthStateChanged } from 'firebase/auth';

import { getPerformance } from "firebase/performance";

import useWebSocket from 'react-use-websocket';
const WS_URL = 'wss://canvas.maxcurzi.com/wss/';

const gridSize = 64;
function AppWs() {
  const [grid, setGrid] = useState(JSON.stringify(Array(gridSize * gridSize).fill(0)));
  const [owners, setOwners] = useState(JSON.stringify(Array(gridSize * gridSize).fill("")));
  const { sendMessage, lastMessage, readyState, getWebSocket } = useWebSocket(WS_URL, {
    onOpen: () => {
      console.log('WebSocket connection established!');
    },
    onMessage: e => {
      let msg = JSON.parse(e.data)
      setGrid(JSON.stringify(msg.pixels))
      setOwners(JSON.stringify(msg.owners))
    },
    shouldReconnect: (_closeEvent) => true,
  });
  const [user, setUser] = useState(null)
  const isAuthenticated = () => {
    return user !== null;
  }

  const auth = getAuth(firebaseApp);
  getPerformance(firebaseApp);
  const webSocket = getWebSocket()
  onAuthStateChanged(auth, (user) => {
    if ((user) && (user.emailVerified)) {
      setUser(user)
    } else {
      setUser(null)
    }
  });

  return (
    <div className="AppWs">
      {/* <GridWs isAuthenticated={isAuthenticated} gridSize={gridSize} user={user} gridData={grid} owners={owners} sendMessage={sendMessage} webSocket={webSocket} readyState={readyState} /> */}
      <LogIn auth={auth} />
      <Image height={64} width={64} imageData={grid}></Image>
    </div>
  );
}

export default AppWs;
