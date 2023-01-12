import { initializeApp } from 'firebase/app';
import { getDatabase, set, ref } from 'firebase/database'

const firebaseConfig = {
    apiKey: 'AIzaSyBGp94K5gwWumKhr4CrNPf51l0vKaFAHQY',

    authDomain: 'canvas-f06e2.firebaseapp.com',

    projectId: 'canvas-f06e2',

    storageBucket: 'canvas-f06e2.appspot.com',

    messagingSenderId: '912387798246',

    appId: '1:912387798246:web:28968d7c91d729156b3727',

    measurementId: 'G-LQJNBYBD5P',

    databaseURL:
      'https://canvas-f06e2-default-rtdb.europe-west1.firebasedatabase.app',
  };

export const resetGrid = (size) => {
    const db = getDatabase(firebaseApp);
    const pixels = {};
    for (let i = 0; i < size*size; i++) {
        pixels[i] = false;
    }
    set(ref(db, 'pixels'), pixels);
}
export const firebaseApp = initializeApp(firebaseConfig);
