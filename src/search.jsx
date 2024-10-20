import React, {useState, useContext} from 'react';
import axios from 'axios';
import "./search.css";
import { useNavigate } from 'react-router-dom';
import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap/dist/js/bootstrap.bundle.min";
import { Container, Form, Button, Row, Col } from 'react-bootstrap';
import { ArticleContext } from './ArticlesContext';




const SearchBar = () => {
  const [searchTerm, setSearchTerm] = useState('');
  
  const { article, setArticle } = useContext(ArticleContext);
  const navigate = useNavigate();
  const handleChange = (event) => {
    setSearchTerm(event.target.value);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
  
    try {
      const response = await axios.get('http://127.0.0.1:5000/fetch-articles', {
        params: {
          search_term: searchTerm, // Assuming searchTerm is a state variable holding the search term
        },
      });
      if (response.status === 200) {
        console.log('API response:', response.data);
        console.log('Articles:', response.data.articles);
        setArticle(response.data.articles); // This should be an array of articles
        navigate('/searchResult');
      } else {
        console.error('Unexpected response status:', response.status);
      }
    } catch (error) {
      console.error('Error fetching articles:', error);
    }
  };
  

  return (
    <Container fluid>
      <div className="Logo">New Analysis</div>
      <div className="section">
        <div className="container">
          <div className="title">Analyze News For...</div>
            <Form onSubmit={handleSubmit}>
                <Row>
                    <Col>
                        <Form.Group className="mb-3">
                            <Form.Control 
                                type="text" 
                                placeholder="Search here" 
                                value={searchTerm} 
                                onChange={handleChange} 
                            />
                        </Form.Group>
                    </Col>
                    <Col>
                        <Button variant="primary" type="submit">
                            Search
                        </Button>
                    </Col>
                </Row>
            </Form>

        </div>
      </div>
    </Container>
  );
};


export default SearchBar; 



{/* <><div className="Logo">New Analysis</div>
<div className="section">
        <div className="container">
            <div className="title">Analyze News For...</div>
            <form onSubmit={handleSubmit}>
                <div className="input">
                    <input className="textfield" placeholder="Search here" type="text" value={searchTerm} onChange={handleChange} />
                </div>
                <button className="button">
                    <div className="primary">
                        <div className="text-wrapper">Search</div>
                    </div>
                </button>
            </form>
        </div>
        <img className="vector" alt="Vector" src="vector-200.svg" />
    </div>
    <div className="contents">
      <div className="container">
          <div className="image-container">
              <div className="image" />
          </div>
          <div className="div">
              <div className="title">Insights</div>
              <div className="text-wrapper">Explore the data</div>
          </div>
      </div>
      <div className="list">
          <div className="row">
              <div className="article">
                  <div className="image-wrapper">
                      <div className="image" />
                  </div>
                  <div className="frame">
                      <div className="title-2">Data Analysis</div>
                      <p className="text-wrapper">Analyzing trends to discover insights.</p>
                  </div>
              </div>
              <div className="article">
                  <div className="image-wrapper">
                      <div className="image" />
                  </div>
                  <div className="frame">
                      <div className="title-2">Visualization</div>
                      <div className="text-wrapper">Creating visually appealing charts.</div>
                  </div>
              </div>
          </div>
      </div>
      <img className="vector" alt="Vector" src="vector-200.svg" />
  </div>
    </> */}




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