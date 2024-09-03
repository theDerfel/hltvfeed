import feedparser
import requests
import time
import os
import sqlite3
from io import BytesIO
from PIL import Image
from atproto import Client, client_utils

# Configurações do feed RSS e Bluesky
feed_url = 'http://www.hltv.org/news.rss.php'
bluesky_username = 'hltvnewsfeed.bsky.social'
bluesky_password = 'xBfP%K4#hhAT6rRZ&Vzs'
database_file = 'published_posts.db'  # Nome do arquivo do banco de dados SQLite

# Inicializa cliente do Bluesky
client = Client()
client.login(bluesky_username, bluesky_password)

def initialize_db():
    """Inicializa o banco de dados e cria a tabela se não existir."""
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS published_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            link TEXT NOT NULL UNIQUE
        )
    ''')
    conn.commit()
    conn.close()

def is_post_published(link):
    """Verifica se o post já foi publicado."""
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM published_posts WHERE link = ?', (link,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def save_published_post(link):
    """Salva o link de um post recém-publicado."""
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO published_posts (link) VALUES (?)', (link,))
    conn.commit()
    conn.close()

def process_feed():
    """Processa o feed RSS e publica novos posts no Bluesky."""
    feed = feedparser.parse(feed_url)

    for entry in feed.entries:
        title = entry.title
        link = entry.link

        # Verifica se o post já foi publicado
        if is_post_published(link):
            continue

        image_url = None
        if 'media_content' in entry:
            image_url = entry.media_content[0]['url']
        elif 'enclosures' in entry:
            image_url = entry.enclosures[0]['href']

        if image_url:
            # Simula cabeçalhos de um navegador real
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': link,  # Referer pode ser a URL do post original
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            }

            # Tenta baixar a imagem com os cabeçalhos
            response = requests.get(image_url, headers=headers)

            if response.status_code == 200:
                try:
                    # Abre a imagem e salva localmente
                    image = Image.open(BytesIO(response.content))
                    image_path = 'downloaded_image.jpg'
                    image.save(image_path)

                    # Envia o post com a imagem para o Bluesky
                    with open(image_path, 'rb') as img_file:
                        text = client_utils.TextBuilder().text(f'{title}\n\n').link(f'{link}', f'{link}')
                        client.send_image(image=img_file, image_alt='', text=text)

                    # Registra o link do post como publicado
                    save_published_post(link)
                except Exception as e:
                    print(f"Erro ao processar a imagem: {e}")
            else:
                print(f"Erro ao baixar a imagem. Código de status: {response.status_code}")
        else:
            # Se não houver imagem, apenas publica o texto e o link
            text = client_utils.TextBuilder().text(f'{title}\n\n').link(f'{link}', f'{link}')
            client.send_post(text)
            # Registra o link do post como publicado
            save_published_post(link)

if __name__ == "__main__":
    initialize_db()  # Inicializa o banco de dados
    process_feed()  # Executa o processamento uma única vez