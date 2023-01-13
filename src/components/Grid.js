import './styles/grid.css';
import { firebaseApp, resetGrid } from '../Firebase';
import { getDatabase, ref, set, onValue , get, child, update} from 'firebase/database';
import React from 'react';

class Grid extends React.Component{
  constructor(props) {
    super(props);
    this.state = {
      pixelArray: Array(props.gridSize * props.gridSize).fill(0),
      gridSize: props.gridSize,
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

  handleClick(event, index) {
    if (this.props.isAuthenticated()) {
      // process the click event and update Firebase database
      const db = getDatabase(firebaseApp);
      const dbRef = ref(db);
      const pixels = {};
      pixels['/pixels/' + index] = (this.state.pixelArray[index]+1)%8;
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
