// src/App.js
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const App = () => {
  const [articles, setArticles] = useState([]);

  useEffect(() => {
    axios.get('http://127.0.0.1:5000/api/articles')
      .then(response => {
        setArticles(response.data);
      })
      .catch(error => {
        console.error('Error fetching articles:', error);
      });
  }, []);

  return (
    <div>
      <h1>News Articles</h1>
      <ul>
        {articles.map(article => (
          <li key={article.url}>
            <h2>{article.title}</h2>
            <p>{article.description}</p>
            <a href={article.url} target="_blank" rel="noopener noreferrer">Read more</a>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default App;
