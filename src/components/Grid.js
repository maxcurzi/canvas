import React, { useState, useEffect } from 'react';
import './styles/grid.css';
import { firebaseApp, resetGrid } from '../Firebase';
import { getDatabase, ref, push, set, onValue , get, child, update} from 'firebase/database';


class Grid extends React.Component{
  constructor(props) {
    console.log(props.user)
    super(props);
    this.state = {
      pixelArray: Array(32 * 32).fill(0),
      user: props.user,
    };
    const db = getDatabase(firebaseApp);
    const dbRef = ref(db);
    get(child(dbRef, 'pixels')).then((snapshot) => {
      // update the state with the data from the Firebase database
      // or set it to a default value if it's null
      this.state = { pixelArray: snapshot.val() || Array(32*32).fill(0) };
      if (snapshot.val() === null) {
        console.log("database empty, reinitialize state");
        resetGrid();
      }
      set(ref(db,'/'), {
        pixels: this.state.pixelArray
      })
    });
  }

  handleClick(event, index) {
    if (this.props.isAuthenticated()) {
      // process the click event and update Firebase database
      const db = getDatabase(firebaseApp);
      const dbRef = ref(db);
      const pixels = {};
      pixels['/pixels/' + index] = 1;
      update(dbRef, pixels);
    } else {
        console.log("User is not authenticated.");
    }
  }

  componentDidMount() {
    const db = getDatabase(firebaseApp);
    const dbRef = ref(db, 'pixels');

    onValue(dbRef, (snapshot) => {
      let newPixels = Object.values(snapshot.val())
      this.setState({ pixelArray: newPixels, user: this.state.user });

    });
  }

  render() {
    return (
      <div className="grid">
        {this.state.pixelArray.map((pixel, index) => {
          return <div
            className={`box color${pixel}`}
            onClick={(event) => { this.handleClick(event, index)} }
            key={index}
          />
        })}
      </div>
        )
  }
};

export default Grid;
