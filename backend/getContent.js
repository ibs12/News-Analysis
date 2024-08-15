// getContent.js

const fs = require('fs');
const { Client } = require('pg');
const axios = require('axios');
const { JSDOM } = require('jsdom');
const { Readability } = require('@mozilla/readability');
const cheerio = require('cheerio');

// Load config
let config;
try {
    const data = fs.readFileSync('config.json', 'utf8');
    config = JSON.parse(data);
} catch (err) {
    console.error('Error reading config file:', err);
    process.exit(1);
}

// Establish database connection
const client = new Client(config);

// Function to scrape article content based on URL
function scrapeArticle(articleUrl) {
    // Check if the article is from the Washington Post
    if (articleUrl.includes('washingtonpost.com')) {
        return scrapeWashingtonPost(articleUrl);
    } else {
        return scrapeStandardArticle(articleUrl);
    }
}

// Function to scrape standard articles using Readability
function scrapeStandardArticle(articleUrl) {
    return axios.get(articleUrl)
        .then(response => {
            const html = response.data;
            const dom = new JSDOM(html, { url: articleUrl });
            const article = new Readability(dom.window.document).parse();
            
            if (article) {
                return article.textContent.trim();
            } else {
                console.error('Readability could not parse the article.');
                return null;
            }
        })
        .catch(error => {
            console.error('Error fetching article:', error);
            return null;
        });
}

function scrapeWashingtonPost(articleUrl) {
    return axios.get(articleUrl)
        .then(response => {
            const html = response.data;
            const $ = cheerio.load(html);
            const articleContent = $('article').text().trim();
            
            if (articleContent) {
                return articleContent;
            } else {
                console.error('Cheerio could not find the article content.');
                return null;
            }
        })
        .catch(error => {
            console.error('Error fetching Washington Post article:', error);
            return null;
        });
}


// Export functions if needed for integration
module.exports = {
    scrapeArticle
};

