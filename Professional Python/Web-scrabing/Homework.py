import requests
from bs4 import BeautifulSoup

# Определяем список ключевых слов:
KEYWORDS = ['дизайн', 'фото', 'web', 'python']


url = "https://habr.com/ru/articles/"


response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

articles = soup.find_all('article')

matching_articles = []

def get_full_article_text(article_url):
    response = requests.get(article_url)
    article_soup = BeautifulSoup(response.text, 'html.parser')
    # Находим основной текст статьи
    content = article_soup.find('div', class_='post__text')
    return content.get_text(strip=True) if content else ''

for article in articles:
    # Извлекаем дату, заголовок и ссылку
    date = article.find('time')['datetime'] if article.find('time') else 'Нет даты'
    title_element = article.find('h2')
    title = title_element.get_text(strip=True) if title_element else 'Нет заголовка'
    link = title_element.find('a')['href'] if title_element and title_element.find('a') else 'Нет ссылки'
    
    full_text = get_full_article_text(link)

    if any(keyword.lower() in full_text.lower() for keyword in KEYWORDS):
        matching_articles.append(f"{date} – {title} – {link}")

for match in matching_articles:
    print(match)