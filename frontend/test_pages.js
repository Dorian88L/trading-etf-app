#!/usr/bin/env node

const puppeteer = require('puppeteer');

async function testPages() {
  const browser = await puppeteer.launch({ 
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  
  // Capturer les erreurs de console
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      console.log(`❌ ERREUR CONSOLE: ${msg.text()}`);
    }
  });
  
  page.on('pageerror', (error) => {
    console.log(`💥 ERREUR PAGE: ${error.message}`);
  });
  
  const testResults = {};
  
  // Pages à tester
  const pages = [
    { name: 'Homepage', url: 'http://localhost:3000/' },
    { name: 'Login', url: 'http://localhost:3000/login' },
    { name: 'ETFs', url: 'http://localhost:3000/etfs' },
    { name: 'Dashboard', url: 'http://localhost:3000/dashboard' },
    { name: 'Signals', url: 'http://localhost:3000/signals' },
    { name: 'Portfolio', url: 'http://localhost:3000/portfolio' },
    { name: 'Settings', url: 'http://localhost:3000/settings' }
  ];
  
  console.log('🔍 TEST DES PAGES FRONTEND');
  console.log('='.repeat(50));
  
  for (const pageTest of pages) {
    try {
      console.log(`\n📄 Test de la page: ${pageTest.name}`);
      await page.goto(pageTest.url, { waitUntil: 'networkidle0', timeout: 10000 });
      
      // Vérifier si la page contient des erreurs
      const hasReactError = await page.evaluate(() => {
        return document.body.innerText.includes('error') || 
               document.body.innerText.includes('Error') ||
               document.body.innerText.includes('Cannot read') ||
               document.body.innerText.includes('TypeError');
      });
      
      const title = await page.title();
      const url = await page.url();
      
      testResults[pageTest.name] = {
        success: !hasReactError,
        title,
        url,
        hasError: hasReactError
      };
      
      if (hasReactError) {
        console.log(`   ❌ Erreur détectée sur la page`);
        // Capturer le texte de l'erreur
        const errorText = await page.evaluate(() => {
          const errorElements = document.querySelectorAll('*');
          for (let el of errorElements) {
            if (el.textContent && (el.textContent.includes('Error') || el.textContent.includes('TypeError'))) {
              return el.textContent.substring(0, 200);
            }
          }
          return null;
        });
        if (errorText) {
          console.log(`   💬 Erreur: ${errorText}`);
        }
      } else {
        console.log(`   ✅ Page chargée avec succès`);
        console.log(`   📍 URL: ${url}`);
        console.log(`   📄 Titre: ${title}`);
      }
      
    } catch (error) {
      console.log(`   ❌ Erreur lors du test: ${error.message}`);
      testResults[pageTest.name] = {
        success: false,
        error: error.message
      };
    }
  }
  
  await browser.close();
  
  // Résumé
  console.log('\n📊 RÉSUMÉ DES TESTS');
  console.log('='.repeat(50));
  const successful = Object.values(testResults).filter(r => r.success).length;
  const total = Object.keys(testResults).length;
  console.log(`✅ Pages réussies: ${successful}/${total}`);
  
  const failed = Object.entries(testResults).filter(([_, r]) => !r.success);
  if (failed.length > 0) {
    console.log(`❌ Pages en erreur:`);
    failed.forEach(([name, result]) => {
      console.log(`   - ${name}: ${result.error || 'Erreur React détectée'}`);
    });
  }
  
  return testResults;
}

// Vérifier si puppeteer est disponible
try {
  testPages().catch(console.error);
} catch (error) {
  console.log('❌ Puppeteer non disponible, test manuel nécessaire');
  console.log('Pour installer: npm install puppeteer');
  process.exit(1);
}