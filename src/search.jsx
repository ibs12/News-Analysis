import React, { useState } from 'react';
import axios from 'axios';

const SearchBar = () => {
  const [searchTerm, setSearchTerm] = useState('');

  const handleChange = (event) => {
    setSearchTerm(event.target.value);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    try {
      const response = await axios.post('http://127.0.0.1:5000/api/fetch-articles', { searchTerm });
      console.log('Fetch articles response:', response.data);
    } catch (error) {
      console.error('Error fetching articles:', error);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        placeholder="Search..."
        value={searchTerm}
        onChange={handleChange}
      />
      <button type="submit">Search</button>
    </form>
  );
};

export default SearchBar;


// import React, { useState, useEffect } from 'react';
// import axios from 'axios';

// const App = () => {
//   const [articles, setArticles] = useState([]);

//   useEffect(() => {
//     axios.get('http://127.0.0.1:5000/api/articles')
//       .then(response => {
//         setArticles(response.data);
//       })
//       .catch(error => {
//         console.error('Error fetching articles:', error);
//       });
//   }, []);

//   return (
//     <div>
//       <h1>News Articles</h1>
//       <ul>
//         {articles.map(article => (
//           <li key={article.url}>
//             <h2>{article.title}</h2>
//             <p>{article.description}</p>
//             <a href={article.url} target="_blank" rel="noopener noreferrer">Read more</a>
//             <p>Content: {article.content}</p>
//           </li>
//         ))}
//       </ul>
//     </div>
//   );
// };