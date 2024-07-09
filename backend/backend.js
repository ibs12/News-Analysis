const express = require('express');
const bodyParser = require('body-parser');
const { scrapeArticle } = require('./getContent.js');

const app = express();
const PORT = 3001;

// Middleware to parse JSON bodies
app.use(bodyParser.json());

app.post('/scrape-articles', async (req, res) => {
    const { url } = req.body;
    if (!url) {
        return res.status(400).send('URL parameter is required');
    }

    try {
        const content = await scrapeArticle(url);
        res.json({ content });
    } catch (error) {
        console.error('Error scraping article:', error);
        res.status(500).send('Error scraping article');
    }
});

app.listen(PORT, () => {
    console.log(`Node.js server running on port ${PORT}`);
});
