import './App.css';
import GridWs from './components/GridWs';
import './websafe_colors.css'
import { firebaseApp, resetGrid } from './Firebase';
import React, { useState } from 'react';

import LogIn from './components/LogIn';
import { getAuth, onAuthStateChanged } from 'firebase/auth';

import { getPerformance } from "firebase/performance";

import useWebSocket from 'react-use-websocket';
const WS_URL = 'ws://127.0.0.1:8777';

const gridSize = 64;
function AppWs() {
  const [grid, setGrid] = useState(JSON.stringify(Array(gridSize * gridSize).fill(0)));
  const [owners, setOwners] = useState(JSON.stringify(Array(gridSize * gridSize).fill("")));
  const { sendMessage, readyState } = useWebSocket(WS_URL, {
    onOpen: () => {
      console.log("A")
      console.log('WebSocket connection established!');
    },
    onMessage: e => {
      let msg = JSON.parse(e.data)
      setGrid(JSON.stringify(msg.pixels))
      setOwners(JSON.stringify(msg.owners))
    },
    shouldReconnect: (_closeEvent) => true,
  });
  // const sendMessage = null
  // const readyState = null
  const [user, setUser] = useState(null)
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
        <LogIn auth={auth} />
    // <div className="AppWs">
    //   <GridWs isAuthenticated={isAuthenticated} gridSize={gridSize} user={user} gridData={grid} owners={owners} sendMessage={sendMessage} readyState={readyState} />
    //   {/* <div className="float-container"> */}
    //     {user && user.uid === "UNWpWi32gPXW35xGEM08l2Tli9i2" ? <button onClick={function () { if (user !== null) { resetGrid(gridSize) } }}>Reset</button> : null}
    //     {/* </div> */}
    // </div>
  );
}

export default AppWs;
