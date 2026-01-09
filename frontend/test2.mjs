import { chromium } from 'playwright';

const URL = 'https://your-deployment-url.example.com';

async function test() {
  console.log('🧪 Тестування ШІ-Агента Контактного Центру...\n');
  
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  try {
    console.log('📱 Відкриваємо сторінку...');
    await page.goto(URL, { waitUntil: 'networkidle', timeout: 30000 });
    
    const title = await page.title();
    console.log(`✅ Заголовок: ${title}`);
    
    // Перевірка що немає згадок про місто
    const pageContent = await page.content();
    const hasCityName = /запоріж|запорож/i.test(pageContent);
    
    console.log(`✅ Згадки про місто: ${hasCityName ? '❌ ЗНАЙДЕНО' : '✓ немає'}`);
    
    // Перевірка основних елементів
    const header = await page.locator('h1:has-text("ШІ-Агент")').isVisible();
    console.log(`✅ Заголовок "ШІ-Агент": ${header ? 'знайдено' : 'не знайдено'}`);
    
    // Перевірка кнопки симуляції
    const callButton = await page.locator('button:has-text("Демо")').isVisible();
    console.log(`✅ Кнопка симуляції: ${callButton ? 'є' : 'немає'}`);
    
    // Перевірка інструкції про звук
    const soundInstruction = await page.locator('text=Увімкніть звук').isVisible();
    console.log(`✅ Інструкція про звук: ${soundInstruction ? 'є' : 'немає'}`);
    
    console.log('\n✅ Тестування завершено!');
    
  } catch (error) {
    console.error('❌ Помилка:', error.message);
  } finally {
    await browser.close();
  }
}

test();
