import './App.css';
import { firebaseApp } from './Firebase';
import React, { useState } from 'react';
import Grid from './components/Grid';
// import LogIn from './components/LogIn';
import { getAuth, onAuthStateChanged } from 'firebase/auth';
import useWebSocket from 'react-use-websocket';
import CookieConsent from 'react-cookie-consent';
import Share from './Share';

const WS_URL = 'ws://localhost:8765/'; // process.env.REACT_APP_WS_URL || 'wss://canvas.maxcurzi.com/wss/';
const SHAREURL = 'Join me at www.pixels.today today!';
function App() {
  const [gridSize, setGridSize] = useState({ width: 64, height: 64 });
  const [grid, setGrid] = useState(Array(64 * 64).fill(0));
  const [owners, setOwners] = useState(Array(64 * 64).fill(''));
  const { sendMessage, readyState, getWebSocket } = useWebSocket(WS_URL, {
    onOpen: () => {
      console.log('WebSocket connection established!');
    },
    onMessage: (e) => {
      let msg = JSON.parse(e.data);

      // Handle full messages (includes metadata on connection)
      if (msg.type === 'full') {
        // Update canvas size if metadata present
        if (msg.meta && msg.meta.width && msg.meta.height) {
          setGridSize({ width: msg.meta.width, height: msg.meta.height });
        }
        // Set full state - convert owners object to array if needed
        setGrid(msg.pixels);
        if (
          msg.owners &&
          typeof msg.owners === 'object' &&
          !Array.isArray(msg.owners)
        ) {
          // Convert owners object to array by index
          const ownersArray = new Array(msg.pixels.length).fill('');
          Object.entries(msg.owners).forEach(([idx, owner]) => {
            ownersArray[parseInt(idx)] = owner;
          });
          setOwners(ownersArray);
        } else {
          setOwners(msg.owners || new Array(msg.pixels.length).fill(''));
        }
      } else if (msg.type === 'delta') {
        // Apply differential update (assumes canvas size is already set)
        setGrid((prevGrid) => {
          const newGrid = [...prevGrid];
          if (msg.pixels) {
            Object.entries(msg.pixels).forEach(([idx, value]) => {
              newGrid[parseInt(idx)] = value;
            });
          }
          return newGrid;
        });
        setOwners((prevOwners) => {
          if (!Array.isArray(prevOwners)) {
            return prevOwners;
          }
          const newOwners = [...prevOwners];
          if (msg.owners) {
            Object.entries(msg.owners).forEach(([idx, owner]) => {
              newOwners[parseInt(idx)] = owner;
            });
          }
          return newOwners;
        });
      }
    },
    shouldReconnect: () => true,
  });
  const [user, setUser] = useState(null);
  const isAuthenticated = () => {
    return true;
    // return user !== null;
  };

  const auth = getAuth(firebaseApp);
  const webSocket = getWebSocket();
  onAuthStateChanged(auth, (user) => {
    if (user && user.emailVerified) {
      setUser(user);
    } else {
      setUser(null);
    }
  });

  return (
    <div
      className="App"
      style={{
        margin: '4%',
      }}
    >
      <Grid
        height={gridSize.height}
        width={gridSize.width}
        imageData={grid}
        user={user}
        isAuthenticated={isAuthenticated}
        owners={owners}
        sendMessage={sendMessage}
        webSocket={webSocket}
        readyState={readyState}
      />
      {/* <LogIn auth={auth} /> */}
      <Share shareurl={SHAREURL} />
      <CookieConsent style={{ background: '#03C' }}>
        This website uses cookies to enhance the user experience.
      </CookieConsent>
    </div>
  );
}

export default App;
