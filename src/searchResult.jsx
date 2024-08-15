import React, { useContext } from 'react';
import { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import './searchResult.css';
import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap/dist/js/bootstrap.bundle.min";
import { Container, Form, Button, Row, Col, Navbar, Card } from 'react-bootstrap';
import { ArticleContext } from './ArticlesContext';


const SearchResult = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const { article, setArticle } = useContext(ArticleContext);
  const [show, setShow] = useState(false);
  // const target = useRef(null);


  const navigate = useNavigate();

  console.log('articles:', article); // Debugging line

  // if (!Array.isArray(articles) || articles.length === 0) {
  //   return <div>No articles found.</div>;
  // }



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
      <Navbar bg="light">
        <Container fluid>
          <Navbar.Brand href="/" className = "title">New Analysis</Navbar.Brand>
          <Form className="d-flex ms-auto" onSubmit={handleSubmit}>
            <Form.Control 
              type="text" 
              placeholder="Search topics" 
              className="me-2" 
              value={searchTerm} 
              onChange={handleChange} 
            />
            <Button variant="primary" type="submit">
              Search
            </Button>
          </Form>
        </Container>
      </Navbar>
      <header className="searchResult-header">Articles</header>
      <div className="row">
      {article.map((article, index) => (
        <div key={index} className="col-md-3 mb-4"> {/* Adjust col-md-4 for column width */}
          <Card>
          <a href={article.url} target="_blank" rel="noopener noreferrer">
          <Card.Img variant="top" src={article.url_to_image} alt={article.title} />
          </a>          
        <Card.Body>
              <Card.Title>
                <a href={article.url} target="_blank" rel="noopener noreferrer" style={{ textDecoration: 'none', color: 'inherit' }}>
                  {article.title}
                </a>
              </Card.Title>
              <Card.Subtitle className="mb-2 text-muted">{article.author} | {article.source_name}</Card.Subtitle>
              <Card.Text>
                {article.description}
              </Card.Text>
              <Button variant="primary" onClick={() => setShow(!show)}>
                Get Sentiment
              </Button>
            </Card.Body>
          </Card>
        </div>
      ))}
    </div>
    </Container>

  );
};

export default SearchResult;


{/* <Container fluid className="p-4">
<Row className="justify-content-center mt-5">
  <Col xs={12} md={8} lg={6}>
  <Card style={{ width: '70rem' }}>
    <Card.Body>
      <Card.Title>Card Title</Card.Title>
      <Card.Subtitle className="mb-2 text-muted">Card Subtitle</Card.Subtitle>
      <Card.Text>
        Some quick example text to build on the card title and make up the
        bulk of the card's content.
      </Card.Text>
      <Card.Link href="#">Card Link</Card.Link>
      <Card.Link href="#">Another Link</Card.Link>
    </Card.Body>
  </Card>
  </Col>
</Row>
</Container>
</Container> */}



{/* <div className="searchResult-container">
<header className="searchResult-header">
  <h1>Search Results</h1>
</header>
<main className="searchResult-main">
  <section className="searchResult-section">
    <h2>Articles</h2>
    <ul>
      {articles.map((article) => (
        <li key={article.url}>
          <h2>{article.title}</h2>
          <p>{article.description}</p>
          <a href={article.url} target="_blank" rel="noopener noreferrer">
            Read more
          </a>
          <p>Content: {article.content}</p>
        </li>
      ))}
    </ul>
  </section>
</main>
<footer className="searchResult-footer">
  <p>&copy; 2024 My Website. All rights reserved.</p>
</footer>
</div> */}