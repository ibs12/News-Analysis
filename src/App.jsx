// src/App.js
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import 'bootstrap/dist/css/bootstrap.min.css';
import { ArticleProvider } from './ArticlesContext';
import SearchBar from './search';
import SearchResult from './searchResult';


function App() {
  return (
    

    <ArticleProvider>
      <Router>
        <div className="App">
          <Routes>
            <Route path="/" element={<SearchBar />} />
            <Route path="/searchResult" element={<SearchResult />} />
          </Routes>
        </div>
      </Router>
    </ArticleProvider>


  );
}

export default App;

