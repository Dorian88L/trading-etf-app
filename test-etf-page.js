#!/usr/bin/env node

const puppeteer = require('puppeteer');
const fs = require('fs');

async function testETFPage() {
  console.log('🔍 Test de la page ETF...');
  
  let browser;
  try {
    browser = await puppeteer.launch({
      headless: 'new',
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    const page = await browser.newPage();
    
    // Écouter les erreurs de console
    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    // Écouter les erreurs de réseau
    const networkErrors = [];
    page.on('response', response => {
      if (response.status() >= 400) {
        networkErrors.push(`${response.status()} - ${response.url()}`);
      }
    });
    
    console.log('📱 Navigation vers la page ETF...');
    await page.goto('http://localhost:3000/etfs', { 
      waitUntil: 'networkidle2',
      timeout: 30000 
    });
    
    // Attendre que le contenu se charge
    await page.waitForTimeout(5000);
    
    // Vérifier si la page contient les éléments attendus
    const title = await page.$eval('h1', el => el.textContent).catch(() => null);
    const searchInput = await page.$('input[placeholder*="Rechercher"]').catch(() => null);
    const loadingState = await page.$('[data-testid="loading"]').catch(() => null);
    const errorState = await page.$('[class*="error"]').catch(() => null);
    
    // Faire une capture d'écran
    await page.screenshot({ path: 'etf-page-test.png', fullPage: true });
    
    // Rapport de test
    const report = {
      timestamp: new Date().toISOString(),
      url: 'http://localhost:3000/etfs',
      title: title,
      elements: {
        searchInput: !!searchInput,
        loadingState: !!loadingState,
        errorState: !!errorState
      },
      errors: {
        console: consoleErrors,
        network: networkErrors
      },
      status: consoleErrors.length === 0 && networkErrors.length === 0 ? 'SUCCESS' : 'FAILED'
    };
    
    console.log('📊 Résultats du test:');
    console.log(`   Titre: ${title || 'NON TROUVÉ'}`);
    console.log(`   Champ recherche: ${searchInput ? '✅' : '❌'}`);
    console.log(`   État chargement: ${loadingState ? '⏳' : '✅'}`);
    console.log(`   État erreur: ${errorState ? '❌' : '✅'}`);
    console.log(`   Erreurs console: ${consoleErrors.length}`);
    console.log(`   Erreurs réseau: ${networkErrors.length}`);
    
    if (consoleErrors.length > 0) {
      console.log('\n🚨 Erreurs de console:');
      consoleErrors.forEach(error => console.log(`   - ${error}`));
    }
    
    if (networkErrors.length > 0) {
      console.log('\n🌐 Erreurs réseau:');
      networkErrors.forEach(error => console.log(`   - ${error}`));
    }
    
    // Sauvegarder le rapport
    fs.writeFileSync('etf-test-report.json', JSON.stringify(report, null, 2));
    console.log('\n📄 Rapport sauvegardé dans etf-test-report.json');
    console.log('🖼️  Capture d\'écran sauvegardée dans etf-page-test.png');
    
    return report.status === 'SUCCESS';
    
  } catch (error) {
    console.error('❌ Erreur lors du test:', error.message);
    return false;
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}

// Exécuter le test si le script est appelé directement
if (require.main === module) {
  testETFPage().then(success => {
    console.log(`\n${success ? '✅ Test réussi' : '❌ Test échoué'}`);
    process.exit(success ? 0 : 1);
  });
}

module.exports = testETFPage;