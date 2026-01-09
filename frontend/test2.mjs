import { chromium } from 'playwright';

const URL = 'https://w6ti4txqsipy.space.minimax.io';

async function test() {
  console.log('🧪 Тестування ШІ-Агента Контактного Центру...\n');
  
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  try {
    console.log('📱 Відкриваємо сторінку...');
    await page.goto(URL, { waitUntil: 'networkidle', timeout: 30000 });
    
    const title = await page.title();
    console.log(`✅ Заголовок: ${title}`);
    
    // Перевірка що немає згадок про Запоріжжя та 1580
    const pageContent = await page.content();
    const has1580 = pageContent.includes('1580');
    const hasZaporizhzhia = pageContent.toLowerCase().includes('запоріж');
    
    console.log(`✅ Згадки про 1580: ${has1580 ? '❌ ЗНАЙДЕНО' : '✓ немає'}`);
    console.log(`✅ Згадки про Запоріжжя: ${hasZaporizhzhia ? '❌ ЗНАЙДЕНО' : '✓ немає'}`);
    
    // Перевірка основних елементів
    const header = await page.locator('h1:has-text("ШІ-Агент Контактного Центру")').isVisible();
    console.log(`✅ Заголовок "ШІ-Агент Контактного Центру": ${header ? 'знайдено' : 'не знайдено'}`);
    
    // Перевірка кнопки симуляції
    const callButton = await page.locator('button:has-text("Симулювати")').isVisible();
    console.log(`✅ Кнопка симуляції: ${callButton ? 'є' : 'немає'}`);
    
    // Перевірка інструкції про звук
    const soundInstruction = await page.locator('text=Увімкніть звук').isVisible();
    console.log(`✅ Інструкція про звук: ${soundInstruction ? 'є' : 'немає'}`);
    
    // Скріншот
    await page.screenshot({ path: '/workspace/zaporizhzhia-1580-agent/screenshot-updated.png', fullPage: true });
    console.log('\n📸 Скріншот збережено');
    
    console.log('\n✅ Тестування завершено!');
    
  } catch (error) {
    console.error('❌ Помилка:', error.message);
  } finally {
    await browser.close();
  }
}

test();
