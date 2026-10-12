from typing import Any

from playwright.async_api import Page


async def snapshot(page: Page, limit: int = 60) -> dict[str, Any]:
    elements = await page.evaluate(
        """() => {
          const selector = 'button,input,textarea,select,[role="button"]';
          return [...document.querySelectorAll(selector)].map(element => {
            const rect = element.getBoundingClientRect();
            const style = getComputedStyle(element);
            const visible = rect.width > 0 && rect.height > 0 &&
              style.visibility !== 'hidden' && style.display !== 'none';
            return {element, tag: element.tagName.toLowerCase(),
              text: (element.innerText || element.value || '').trim().slice(0, 80),
              name: element.getAttribute('name') || '',
              type: element.getAttribute('type') || '',
              placeholder: element.getAttribute('placeholder') || '', visible};
          }).filter(item => item.visible).map((item, id) => {
            item.element.setAttribute('data-agent-id', String(id));
            return {id, tag: item.tag, text: item.text, name: item.name,
              type: item.type, placeholder: item.placeholder};
          });
        }"""
    )
    lines = [
        f"{item['id']}: <{item['tag']} name={item['name']} type={item['type']}> "
        f"{item['text'] or item['placeholder']!r}"
        for item in elements[-limit:]
    ]
    return {
        "url": page.url,
        "title": await page.title(),
        "text": (await page.locator("body").inner_text())[:1500],
        "elements": lines,
    }
