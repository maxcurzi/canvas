import './styles/grid.css';
import { firebaseApp, resetGrid } from '../Firebase';
import { getDatabase, ref, onValue ,get, child} from 'firebase/database';
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
// const tooltipStyle = {
//   display: this.state.hover ? 'block' : 'none'
// }

class Grid extends React.Component{
  constructor(props) {
    super(props);
    this.state = {
      pixelArray: Array(props.gridSize * props.gridSize).fill(0),
      owners: Array(props.gridSize * props.gridSize).fill(""),
      gridSize: props.gridSize,
      lastClickTime: 0,
    };
    const db = getDatabase(firebaseApp);
    const dbRef = ref(db);
    get(child(dbRef, 'pixels')).then((snapshot) => {
      // update the state with the data from the Firebase database
      // or set it to a default value if it's null
      this.state = {...this.state, pixelArray: snapshot.val() || Array(this.state.gridSize * this.state.gridSize).fill(0) };
      if (snapshot.val() === null) {
        // console.log("database empty, reinitialize state");
        resetGrid();
      }
    });
  }
  handleClick = async (x_value, y_value, user_value) => {
    // console.log(this.props.user.displayName)
    let data = {x: x_value, y: y_value, user: user_value};
    let jsoninfo = JSON.stringify(data);
    // const response = await fetch('http://127.0.0.1:8080/update_pixel/', {
    // const response = await fetch('https://canvas-backend-j4zsynltia-ew.a.run.app:8080/update_pixel/', {
    const response = await fetch('https://10.132.0.2:8080/update_pixel/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: jsoninfo
    });
    const json = await response.json();
    if (!response.ok) {
        console.log("NOT OK")
        throw new Error(json.message);
      }
      console.log("OK")
    // console.log(this.state)
  }

  componentDidMount() {
    const db = getDatabase(firebaseApp);
    const dbRef_pixels = ref(db, 'pixels');
    const dbRef_owners = ref(db, 'owners');
    onValue(dbRef_pixels, (snapshot) => {
      let newPixels = Object.values(snapshot.val())
      this.setState({ ...this.state, pixelArray: newPixels });
    });
    onValue(dbRef_owners, (snapshot) => {
      let newOwners = Object(snapshot.val())
      let newOwnersArr = Array(this.props.gridSize * this.props.gridSize).fill("")
      Object.entries(newOwners).forEach(entry => {
        const [key, value] = entry;
        // console.log(key)
        newOwnersArr[key] = value;
      });
      this.state.owners = newOwnersArr
    });
  }

  render() {
    let owners = this.state.owners
    return (
      <div className="grid" style={{
        'gridTemplateColumns': `repeat(${this.state.gridSize}, 1fr)`,
        'gridTemplateRows': `repeat(${this.state.gridSize}, 1fr)`
      }}>
        {this.state.pixelArray.map((pixel, index) => {
          const x = index  % this.state.gridSize
          const y = Math.floor(index / this.state.gridSize)
          const tooltip_text = this.state.owners[index] === ""? null : "Owner: " + this.state.owners[index]
          return <div
            className={`box color${pixel}`}
            title={tooltip_text}
            onClick={(event) => {
              let now_t = Date.now()
              if ( now_t - this.state.lastClickTime > 1000) {
                this.setState({ lastClickTime: now_t })
                this.handleClick(x, y, this.props.user.uid == null ? "NA" : this.props.user.displayName)
              }
              else {
                // console.log("You're clicking too fast!")
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
