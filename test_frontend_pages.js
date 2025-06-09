// Test script pour vérifier les pages frontend de l'application Trading ETF
// Ce script utilise Puppeteer pour tester les pages en mode headless

const puppeteer = require('puppeteer');

const FRONTEND_URL = 'http://localhost:3000';

const pages = [
  { path: '/', name: 'Dashboard/Home' },
  { path: '/etfs', name: 'ETF List' },
  { path: '/signals', name: 'Signals' },
  { path: '/portfolio', name: 'Portfolio' },
  { path: '/alerts', name: 'Alerts' },
  { path: '/settings', name: 'Settings' },
  { path: '/login', name: 'Login' }
];

async function testPage(browser, page) {
  const testPage = await browser.newPage();
  const results = {
    url: `${FRONTEND_URL}${page.path}`,
    name: page.name,
    loaded: false,
    hasErrors: false,
    errors: [],
    title: '',
    hasReactRoot: false,
    statusCode: null
  };

  try {
    // Écouter les erreurs de console
    testPage.on('console', msg => {
      if (msg.type() === 'error') {
        results.errors.push(msg.text());
        results.hasErrors = true;
      }
    });

    // Naviguer vers la page
    const response = await testPage.goto(results.url, { 
      waitUntil: 'networkidle0',
      timeout: 30000 
    });
    
    results.statusCode = response.status();
    results.loaded = response.ok();
    
    // Attendre que React se charge
    await testPage.waitForTimeout(2000);
    
    // Vérifier le titre
    results.title = await testPage.title();
    
    // Vérifier si React s'est chargé
    const hasReactRoot = await testPage.evaluate(() => {
      return document.getElementById('root') !== null;
    });
    results.hasReactRoot = hasReactRoot;

    // Vérifier si du contenu a été rendu
    const hasContent = await testPage.evaluate(() => {
      const root = document.getElementById('root');
      return root && root.innerHTML.trim().length > 0;
    });
    results.hasContent = hasContent;

  } catch (error) {
    results.hasErrors = true;
    results.errors.push(error.message);
  } finally {
    await testPage.close();
  }

  return results;
}

async function testAllPages() {
  console.log('🚀 Début des tests des pages frontend...\n');
  
  const browser = await puppeteer.launch({ 
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const results = [];

  for (const page of pages) {
    console.log(`📄 Test de ${page.name} (${page.path})...`);
    const result = await testPage(browser, page);
    results.push(result);
    
    if (result.loaded) {
      console.log(`✅ ${page.name}: Page chargée avec succès`);
    } else {
      console.log(`❌ ${page.name}: Échec du chargement`);
    }
    
    if (result.hasErrors) {
      console.log(`⚠️  ${page.name}: Erreurs détectées`);
    }
  }

  await browser.close();

  // Rapport final
  console.log('\n📊 RAPPORT FINAL:\n');
  console.log('='.repeat(60));
  
  results.forEach(result => {
    console.log(`\n📄 ${result.name} (${result.url})`);
    console.log(`   Status: ${result.statusCode}`);
    console.log(`   Chargée: ${result.loaded ? '✅' : '❌'}`);
    console.log(`   React Root: ${result.hasReactRoot ? '✅' : '❌'}`);
    console.log(`   Contenu: ${result.hasContent ? '✅' : '❌'}`);
    console.log(`   Titre: "${result.title}"`);
    
    if (result.hasErrors) {
      console.log(`   Erreurs:`);
      result.errors.forEach(error => {
        console.log(`     - ${error}`);
      });
    }
  });

  // Statistiques globales
  const successCount = results.filter(r => r.loaded && !r.hasErrors).length;
  const totalCount = results.length;
  
  console.log('\n📈 STATISTIQUES:');
  console.log(`   Pages testées: ${totalCount}`);
  console.log(`   Pages fonctionnelles: ${successCount}`);
  console.log(`   Taux de succès: ${Math.round((successCount / totalCount) * 100)}%`);
  
  return results;
}

if (require.main === module) {
  testAllPages().catch(console.error);
}

module.exports = { testAllPages };