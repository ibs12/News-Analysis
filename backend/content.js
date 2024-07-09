const axios = require('axios');
const { JSDOM } = require('jsdom');
const { Readability } = require('@mozilla/readability');
const cheerio = require('cheerio');

function scrapeArticle(articleUrl) {
    // Check if the article is from the Washington Post
    if (articleUrl.includes('washingtonpost.com')) {
        return scrapeWashingtonPost(articleUrl);
    } else {
        return scrapeStandardArticle(articleUrl);
    }
}

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

// Example usage:
let articleUrl = 'https://fortune.com/2014/10/07/race-gender-sexual-orientation-job-applications/';
scrapeArticle(articleUrl)
    .then(articleContent => {
        console.log('Article Content:');
        console.log(articleContent);
    })
    .catch(error => {
        console.error('Error scraping article:', error);
    });
