const express = require('express');
const puppeteer = require('puppeteer');

const app = express();
let cachedModels = [];
let isScraped = false;

const CATEGORIES = [
  { name: 'WOMEN', url: 'https://www.ilmodel.com/models' }
];

async function scrapeModels() {
  if (isScraped && cachedModels.length > 0) {
    return cachedModels;
  }

  try {
    console.log('Starting scrape with Puppeteer...');
    
    const browser = await puppeteer.launch({
      headless: 'new',
      args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
    });

    const page = await browser.newPage();
    const models = [];

    for (const category of CATEGORIES) {
      console.log(`Scraping: ${category.name}`);
      
      await page.goto(category.url, { waitUntil: 'networkidle2', timeout: 30000 });
      
      // Wait for model links to load
      await page.waitForSelector('a[href^="#/"]', { timeout: 10000 }).catch(() => {});
      
      // Get all model links
      const modelLinks = await page.evaluate(() => {
        const links = [];
        document.querySelectorAll('a[href^="#/"]').forEach(link => {
          const href = link.getAttribute('href');
          const name = link.textContent.trim();
          if (href && name && name.length > 1) {
            links.push({ name, href });
          }
        });
        return links;
      });

      console.log(`Found ${modelLinks.length} models`);

      // Scrape each model
      for (let i = 0; i < Math.min(modelLinks.length, 50); i++) {
        const { name, href } = modelLinks[i];
        const modelUrl = `https://www.ilmodel.com/models${href}`;
        
        try {
          console.log(`[${i+1}/${Math.min(modelLinks.length, 50)}] ${name}`);
          
          await page.goto(modelUrl, { waitUntil: 'networkidle2', timeout: 30000 });
          
          const modelData = await page.evaluate(() => {
            const text = document.body.innerText;
            const measurements = {};
            
            // Find line with Height | Bust | Waist...
            const lines = text.split('\n');
            for (const line of lines) {
              if (line.includes('Height') && line.includes('Bust') && line.includes('Waist')) {
                const parts = line.split('|');
                for (const part of parts) {
                  const trimmed = part.trim();
                  const tokens = trimmed.split(/\s+/);
                  if (tokens.length >= 2) {
                    const key = tokens[0];
                    const value = tokens.slice(1).join(' ');
                    measurements[key] = value;
                  }
                }
                break;
              }
            }
            
            return {
              name: document.querySelector('h1')?.innerText || '',
              measurements
            };
          });

          if (modelData.measurements && Object.keys(modelData.measurements).length > 0) {
            models.push({
              Name: name,
              URL: modelUrl,
              Height: modelData.measurements.Height || '',
              Bust: modelData.measurements.Bust || '',
              Waist: modelData.measurements.Waist || '',
              Hips: modelData.measurements.Hips || '',
              Bra: modelData.measurements.Bra || '',
              Shirt: modelData.measurements.Shirt || '',
              Pants: modelData.measurements.Pants || '',
              Shoe: modelData.measurements.Shoe || '',
              'Eye Color': modelData.measurements.Eye || '',
              'Hair Color': modelData.measurements.Hair || '',
              Tattoos: modelData.measurements.Tattoos || '',
              'Ear Piercings': modelData.measurements.Piercings || ''
            });
          }
        } catch (err) {
          console.error(`Error scraping ${name}:`, err.message);
        }
      }
    }

    await browser.close();
    
    cachedModels = models;
    isScraped = true;
    console.log(`Scraping complete. Total: ${models.length}`);
    
    return models;
  } catch (err) {
    console.error('Scrape error:', err);
    return [];
  }
}

app.use(express.static('public'));

app.get('/api/models', async (req, res) => {
  if (cachedModels.length === 0) {
    return res.status(503).json({ error: 'Loading models...' });
  }
  res.json(cachedModels);
});

app.get('/', (req, res) => {
  res.sendFile(__dirname + '/index.html');
});

const PORT = process.env.PORT || 8081;

// Start scraping in background
scrapeModels();

// Re-scrape every 6 hours
setInterval(() => {
  isScraped = false;
  scrapeModels();
}, 6 * 60 * 60 * 1000);

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
