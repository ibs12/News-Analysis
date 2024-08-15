// src/ArticlesContext.js
import { createContext, useState } from 'react';

export const ArticleContext = createContext();

export const ArticleProvider = ({ children }) => {
  const [article, setArticle] = useState([]);

  return (
    <ArticleContext.Provider value={{ article, setArticle }}>
      {children}
    </ArticleContext.Provider>
  );
};

