import React, { useContext, useRef, useEffect, useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import './searchResult.css';
import "bootstrap/dist/css/bootstrap.min.css";
import { Container, Form, Button, Navbar, Card, Overlay } from 'react-bootstrap';
import { ArticleContext } from './ArticlesContext';

const SearchResult = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const { article, setArticle } = useContext(ArticleContext);
  const [showOverlay, setShowOverlay] = useState({});
  const [sentiments, setSentiments] = useState([]); // State to store sentiments
  const refs = useRef([]);
  const navigate = useNavigate();


  useEffect(() => {
    refs.current = refs.current.slice(0, article.length);
    article.forEach((_, index) => {
      if (!refs.current[index]) {
        refs.current[index] = React.createRef();
      }
    });

    // Initially set sentiments to null for all articles
    const initialSentiments = article.map(() => null);
    setSentiments(initialSentiments);
  }, [article]);

  const handleOverlayToggle = (index) => {
    setShowOverlay((prevState) => ({
      ...prevState,
      [index]: !prevState[index],
    }));
    // If sentiment is already fetched, no need to refetch
    if (sentiments[index]) return;

    // Fetch sentiment from backend using article content
    const articleContent = article[index].content; // Assuming the article has a content field
    console.log(articleContent)

    axios.post('http://127.0.0.1:5000/get-sentiment', { content: articleContent })
      .then((response) => {
        const newSentiment = response.data.label.toLowerCase(); // Expecting 'positive', 'negative', or 'neutral'
        setSentiments((prevSentiments) => {
          const updatedSentiments = [...prevSentiments];
          updatedSentiments[index] = newSentiment;



          return updatedSentiments;
        });
      })
      .catch((error) => {
        console.error('Error fetching sentiment:', error);
      });
  };

  const getButtonVariant = (sentiment) => {
    if (sentiment === 'positive') return 'success';
    if (sentiment === 'negative') return 'danger';
    if (sentiment === 'neutral') return 'secondary';
    return 'primary'; // Default button variant
  };

  const getButtonText = (sentiment) => {
    return sentiment ? sentiment.charAt(0).toUpperCase() + sentiment.slice(1) : 'Get Sentiment';
  };


  const handleChange = (event) => {
    setSearchTerm(event.target.value);
  };


  const handleSubmit = async (event) => {
    event.preventDefault();
    try {
      const response = await axios.get('http://127.0.0.1:5000/fetch-articles', {
        params: { search_term: searchTerm },
      });
      if (response.status === 200) {
        setArticle(response.data.articles); // Set fetched articles
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
          <Navbar.Brand href="/" className="title">News Analysis</Navbar.Brand>
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
          <div key={index} className="col-md-3 mb-4">
            <Card>
              <a href={article.link} target="_blank" rel="noopener noreferrer">
                <Card.Img variant="top" src={article.image_url} alt={article.title} />
              </a>
              <Card.Body>
                <Card.Title>
                  <a href={article.link} target="_blank" rel="noopener noreferrer" style={{ textDecoration: 'none', color: 'inherit' }}>
                    {article.title}
                  </a>
                </Card.Title>
                <Card.Subtitle className="mb-2 text-muted">
                  {article.creator} | {article.source_name}
                </Card.Subtitle>
                <Card.Text>
                  {article.description}
                </Card.Text>
                <Button
                  variant={getButtonVariant(sentiments[index])}
                  ref={refs.current[index] || React.createRef()}
                  onClick={() => handleOverlayToggle(index)}
                >
                  {getButtonText(sentiments[index])}
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



// Overlay idea

// import React, { useContext, useRef, useEffect } from 'react';
// import { useState } from 'react';
// import axios from 'axios';
// import { useNavigate } from 'react-router-dom';
// import './searchResult.css';
// import "bootstrap/dist/css/bootstrap.min.css";
// import "bootstrap/dist/js/bootstrap.bundle.min";
// import { Container, Form, Button, Row, Col, Navbar, Card } from 'react-bootstrap';
// import { ArticleContext } from './ArticlesContext';

// import Overlay from 'react-bootstrap/Overlay';

// const SearchResult = () => {
//   const [searchTerm, setSearchTerm] = useState('');
//   const { article, setArticle } = useContext(ArticleContext);
//   const [showOverlay, setShowOverlay] = useState({});
  
//   const refs = useRef([]);


//   const navigate = useNavigate();

//   console.log('articles:', article); // Debugging line

//   // if (!Array.isArray(articles) || articles.length === 0) {
//   //   return <div>No articles found.</div>;
//   // }


//   const handleOverlayToggle = (index) => {
//     setShowOverlay((prevState) => ({
//       ...prevState,
//       [index]: !prevState[index],
//     }));
//   };

//   useEffect(() => {
//     refs.current = refs.current.slice(0, article.length); // Ensure we only have as many refs as articles
//     article.forEach((_, index) => {
//       if (!refs.current[index]) {
//         refs.current[index] = React.createRef();
//       }
//     });
//   }, [article]);


//   const handleChange = (event) => {
//     setSearchTerm(event.target.value);
//   };

//   const handleSubmit = async (event) => {
//     event.preventDefault();
  
//     try {
//       const response = await axios.get('http://127.0.0.1:5000/fetch-articles', {
//         params: {
//           search_term: searchTerm, // Assuming searchTerm is a state variable holding the search term
//         },
//       });
  
//       if (response.status === 200) {
//         console.log('API response:', response.data);
//         console.log('Articles:', response.data.articles);
//         setArticle(response.data.articles); // This should be an array of articles
//         navigate('/searchResult');
//       } else {
//         console.error('Unexpected response status:', response.status);
//       }
//     } catch (error) {
//       console.error('Error fetching articles:', error);
//     }
//   };

//   return (
//     <Container fluid>
//       <Navbar bg="light">
//         <Container fluid>
//           <Navbar.Brand href="/" className = "title">New Analysis</Navbar.Brand>
//           <Form className="d-flex ms-auto" onSubmit={handleSubmit}>
//             <Form.Control 
//               type="text" 
//               placeholder="Search topics" 
//               className="me-2" 
//               value={searchTerm} 
//               onChange={handleChange} 
//             />
//             <Button variant="primary" type="submit">
//               Search
//             </Button>
//           </Form>
//         </Container>
//       </Navbar>
//       <header className="searchResult-header">Articles</header>
//       <div className="row">
//       {article.map((article, index) => (
        
//         <div key={index} className="col-md-3 mb-4"> {/* Adjust col-md-4 for column width */}
//           <Card>
//           <a href={article.url} target="_blank" rel="noopener noreferrer">
//           <Card.Img variant="top" src={article.url_to_image} alt={article.title} />
//           </a>          
//         <Card.Body>
//               <Card.Title>
//                 <a href={article.url} target="_blank" rel="noopener noreferrer" style={{ textDecoration: 'none', color: 'inherit' }}>
//                   {article.title}
//                 </a>
//               </Card.Title>
//               <Card.Subtitle className="mb-2 text-muted">{article.author} | {article.source_name}</Card.Subtitle>
//               <Card.Text>
//                 {article.description}
//               </Card.Text>
//               <Button 
//                   variant="primary" 
//                   ref={refs.current[index] || React.createRef()} 
//                   onClick={() => handleOverlayToggle(index)}
//                   >
//                   Get Sentiment
//                 </Button>
//                 <Overlay target={refs.current[index]?.current} show={showOverlay[index]} placement="right">
//                   {({ placement, arrowProps, ...props }) => (
//                     <div
//                       {...props}
//                       style={{
//                         position: 'absolute',
//                         backgroundColor: 'rgba(255, 100, 100, 0.85)',
//                         padding: '2px 10px',
//                         color: 'white',
//                         borderRadius: 3,
//                         ...props.style,
//                       }}
//                     >
//                       Simple tooltip
//                     </div>
//                   )}
//                 </Overlay>
//             </Card.Body>
//           </Card>
//         </div>
//       ))}
//     </div>
//     </Container>

//   );
// };

// export default SearchResult;