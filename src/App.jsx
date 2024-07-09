// src/App.js


import React from 'react';
import { HashRouter as Router, Route, Routes } from 'react-router-dom';

import SearchBar from './search';




function App() {
  return (
      <Router>
        <div className="App">
          <Routes>
            <Route path="/" element={<SearchBar />} />
            
          </Routes>
        </div>
      </Router>
  );
}


export default App;
