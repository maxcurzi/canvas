import './App.css';
import Grid from './components/Grid';
import { firebaseApp, resetGrid } from './Firebase';

function App() {

  return (
    <div className="App">
      <Grid />
      <button onClick={function(){resetGrid(32)}}>Reset</button>
    </div>
  );
}

export default App;
