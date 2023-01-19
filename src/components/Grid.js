import './styles/grid.css';
import { firebaseApp, resetGrid } from '../Firebase';
import { getDatabase, ref, set, onValue ,push, get, child, update} from 'firebase/database';
import React from 'react';

// async function handleClick(x, y) {
//   const username = "your_username"; //  get it from your authentication context
//   const response = await fetch('http://your_server_url:8000/update_pixel/', {
//       method: 'POST',
//       headers: { 'Content-Type': 'application/json' },
//       body: JSON.stringify({ x, y, username }),
//   });
//   const json = await response.json();
//   if (!response.ok) {
//       throw new Error(json.message);
//   }
//   // do something with the json response
// }

class Grid extends React.Component{
  constructor(props) {
    super(props);
    this.state = {
      pixelArray: Array(props.gridSize * props.gridSize).fill(0),
      gridSize: props.gridSize,
      lastClickTime: 0,
    };
    const db = getDatabase(firebaseApp);
    const dbRef = ref(db);
    get(child(dbRef, 'pixels')).then((snapshot) => {
      // update the state with the data from the Firebase database
      // or set it to a default value if it's null
      this.state = { pixelArray: snapshot.val() || Array(this.state.gridSize*this.state.gridSize).fill(0) };
      if (snapshot.val() === null) {
        console.log("database empty, reinitialize state");
        resetGrid();
      }
      // set(ref(db,'/'), {
      //   pixels: this.state.pixelArray
      // })
    });
  }
  handleClick = async (x_value, y_value, user_value) => {
    console.log(this.props.user.displayName)
    let data = {x: x_value, y: y_value, user: user_value};
    let jsoninfo = JSON.stringify(data);
    console.log(jsoninfo)
    const response = await fetch('http://127.0.0.1:8000/update_pixel/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: jsoninfo
    });
    const json = await response.json();
    if (!response.ok) {
        console.log("Unsuccessful request!");
        throw new Error(json.message);
    }
    console.log("Successful request!");
  }

  handleClick_direct_to_server(event, index) {
    if (this.props.isAuthenticated()) {
      // process the click event and update Firebase database
      const db = getDatabase(firebaseApp);
      const dbRef = ref(db);
      const pixels = {};
      // pixels['/pixels/' + index] = (this.state.pixelArray[index]+1)%8;
      // update(dbRef, pixels);
      const postListRef = ref(db, 'requests');
      const newPostRef = push(postListRef);
      set(newPostRef, {
        userId: this.props.user.uid,
        userDisplayName: this.props.user.displayName,
        timestamp: Date.now(),
        pixelReq: index,
      });


    } else {
        console.log("User is not authenticated.");
    }
  }

  componentDidMount() {
    const db = getDatabase(firebaseApp);
    const dbRef = ref(db, 'pixels');
    onValue(dbRef, (snapshot) => {
      let newPixels = Object.values(snapshot.val())
      this.setState({ pixelArray: newPixels});
    });
  }

  render() {
    return (
      <div className="grid" style={{
        'gridTemplateColumns': `repeat(${this.state.gridSize}, 1fr)`,
        'gridTemplateRows': `repeat(${this.state.gridSize}, 1fr)`
      }}>
        {this.state.pixelArray.map((pixel, index) => {
          const x = index  % this.state.gridSize
          const y = Math.floor(index / this.state.gridSize)
          return <div
            className={`box color${pixel}`}
            onClick={(event) => {
              let now_t = Date.now()
              if ( now_t - this.state.lastClickTime > 1000) {
                this.state.lastClickTime = now_t
                this.handleClick(x, y, this.props.user.uid == null ? "UID_NA" : this.props.user.uid)
              }
              else {
                console.log("You're clicking too fast!")
              }
            }}
            key={index}
          />
        })}
      </div>
        )
  }
};

export default Grid;
