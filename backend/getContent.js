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

            return article.textContent.trim();
        })
        .catch(error => {
            console.error('Error fetching article:', error);
            return null;
        });
}

// Function to scrape Washington Post articles using cheerio
function scrapeWashingtonPost(articleUrl) {
    return axios.get(articleUrl)
        .then(response => {
            const html = response.data;
            const $ = cheerio.load(html);

            // Select the main article content based on the structure of the Washington Post's HTML
            const articleContent = $('article').text().trim(); // Adjust the selector based on the specific HTML structure

            return articleContent;
        })
        .catch(error => {
            console.error('Error fetching Washington Post article:', error);
            return null;
        });
}

// Connect to the database
client.connect(err => {
    if (err) {
        console.error('Database connection error:', err.stack);
        process.exit(1);
    }

    // Query to fetch all URLs from the top_US_headlines table
    const query = 'SELECT id, url FROM top_headlines_us';

    client.query(query, (err, res) => {
        if (err) {
            console.error('Error executing query:', err.stack);
            client.end();
            return;
        }

        // Array to hold promises for each article processing
        const promises = [];

        // Process each URL
        res.rows.forEach(row => {
            const { id, url } = row;

            // Scrape article content and update database
            const promise = scrapeArticle(url)
                .then(articleContent => {
                    if (articleContent) {
                        // Update the database with the article content
                        const updateQuery = 'UPDATE top_headlines_us SET content = $1 WHERE id = $2';
                        const values = [articleContent, id];

                        return client.query(updateQuery, values);
                    } else {
                        console.error('No article content retrieved for URL:', url);
                    }
                })
                .catch(error => {
                    console.error('Error scraping article for URL', url, ':', error);
                });

            promises.push(promise);
        });

        // Wait for all promises to resolve before closing the database connection
        Promise.all(promises)
            .then(() => {
                console.log('All articles processed successfully.');
                client.end(); // Close the database connection
            })
            .catch(err => {
                console.error('Error processing articles:', err);
                client.end(); // Close the database connection on error too
            });
    });
});
