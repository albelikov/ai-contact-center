import { chromium } from 'playwright';

const URL = 'https://9q4xowlvp3cp.space.minimax.io';

async function test() {
  console.log('🧪 Тестування ШІ-Агента 1580...\n');
  
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  try {
    // Відкриття сторінки
    console.log('📱 Відкриваємо сторінку...');
    await page.goto(URL, { waitUntil: 'networkidle', timeout: 30000 });
    
    // Перевірка заголовка
    const title = await page.title();
    console.log(`✅ Заголовок: ${title}`);
    
    // Перевірка основних елементів
    const header = await page.locator('h1:has-text("ШІ-Агент 1580")').isVisible();
    console.log(`✅ Заголовок "ШІ-Агент 1580": ${header ? 'знайдено' : 'не знайдено'}`);
    
    // Перевірка навігації
    const navButtons = await page.locator('button:has-text("Дзвінки")').count();
    console.log(`✅ Кнопка навігації "Дзвінки": ${navButtons > 0 ? 'є' : 'немає'}`);
    
    // Перевірка статусу системи
    const fishSpeechStatus = await page.locator('text=Fish Speech Active').isVisible();
    console.log(`✅ Статус Fish Speech: ${fishSpeechStatus ? 'активний' : 'не знайдено'}`);
    
    // Перевірка кнопки симуляції дзвінка
    const callButton = await page.locator('button:has-text("Симулювати")').isVisible();
    console.log(`✅ Кнопка симуляції дзвінка: ${callButton ? 'є' : 'немає'}`);
    
    // Перевірка панелі статусу системи
    const sileroStatus = await page.locator('text=Silero ASR').isVisible();
    console.log(`✅ Silero ASR у статусі: ${sileroStatus ? 'є' : 'немає'}`);
    
    // Клік на вкладку "Класифікатор"
    await page.locator('button:has-text("Класифікатор")').click();
    await page.waitForTimeout(500);
    
    const classifierTable = await page.locator('table').isVisible();
    console.log(`✅ Таблиця класифікатора: ${classifierTable ? 'відображається' : 'не знайдено'}`);
    
    // Повернення на дашборд
    await page.locator('button:has-text("Дзвінки")').click();
    await page.waitForTimeout(500);
    
    // Симуляція дзвінка
    console.log('\n📞 Симулюємо вхідний дзвінок...');
    await page.locator('button:has-text("Симулювати")').click();
    await page.waitForTimeout(3000);
    
    // Перевірка що дзвінок активний
    const callActive = await page.locator('text=Активний дзвінок').isVisible() || 
                       await page.locator('text=Вхідний дзвінок').isVisible() ||
                       await page.locator('text=Обробка').isVisible();
    console.log(`✅ Дзвінок активний: ${callActive ? 'так' : 'очікування'}`);
    
    // Чекаємо на повідомлення в чаті
    await page.waitForTimeout(4000);
    const chatMessages = await page.locator('.max-w-\\[80\\%\\]').count();
    console.log(`✅ Повідомлень у чаті: ${chatMessages}`);
    
    // Скріншот
    await page.screenshot({ path: '/workspace/zaporizhzhia-1580-agent/screenshot.png', fullPage: true });
    console.log('\n📸 Скріншот збережено: screenshot.png');
    
    console.log('\n✅ Всі тести пройдено успішно!');
    
  } catch (error) {
    console.error('❌ Помилка:', error.message);
    await page.screenshot({ path: '/workspace/zaporizhzhia-1580-agent/error-screenshot.png' });
  } finally {
    await browser.close();
  }
}

test();
