import os, sqlite3

base = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))
img_dir = os.path.join(base, 'images')
db_path = os.path.join(base, 'database.db')

conn = sqlite3.connect(db_path)
cur = conn.cursor()

for filename in os.listdir(img_dir):
    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
        cur.execute('SELECT 1 FROM teachers WHERE image_filename = ?', (filename,))
        if not cur.fetchone():
            name = os.path.splitext(filename)[0]
            cur.execute(
                'INSERT INTO teachers (name, specialization, image_filename) VALUES (?, ?, ?)',
                (name, 'غير محدد', filename)
            )

conn.commit()
conn.close()
