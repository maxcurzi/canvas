import React, { useState, useEffect } from 'react';
import './styles/grid.css';
import { firebaseApp } from '../Firebase';
import { getDatabase, ref, push, set, onValue , get, child, update} from 'firebase/database';

const generateInitialState = (size) => Array(size * size).fill(false);

class Grid extends React.Component{
  constructor(props) {
    super(props);
    this.state = {
        clickedPixels: Array(100).fill(false),
    };
    const db = getDatabase(firebaseApp);
    const dbRef = ref(db);
    get(child(dbRef, 'pixels')).then((snapshot) => {
      // update the state with the data from the Firebase database
      // or set it to a default value if it's null
      this.state = { clickedPixels: snapshot.val() || Array(100).fill(false) };
      if (snapshot.val() === null) {
        console.log("database empty, reinitialize state");
        const pixels = {};
        for (let i = 0; i < 100; i++) {
            pixels[i] = { clicked: false };
        }
        set(ref(db, 'pixels'), pixels);
      }
      set(ref(db,'/'), {
        pixels: this.state.clickedPixels
      })
    });
  }

  handleClick(event, index) {
    // send the click event to the Firebase server
    const db = getDatabase(firebaseApp);
    const dbRef = ref(db);
    const pixels = {};
    pixels['/pixels/' + index] = true;
    update(dbRef, pixels);
  }

  componentDidMount() {
    const db = getDatabase(firebaseApp);
    const dbRef = ref(db, 'pixels');

    onValue(dbRef, (snapshot) => {
        let newPixels = Object.values(snapshot.val())
        this.setState({clickedPixels: newPixels});
    });
  }

  render() {
    return (
        <div className="grid">
            {this.state.clickedPixels.map((pixel, index) => (
                <div
                    className={`box ${pixel ? 'clicked' : ''}`}
                    onClick={(event) => this.handleClick(event, index)}
                    key={index}
                />
            ))}
        </div>
    );
  }
};

export default Grid;
