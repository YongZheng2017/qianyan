"""一次性迁移：为 data_sources 表添加 credentials_encrypted 列"""
import pymysql

conn = pymysql.connect(host='localhost', port=3306, user='root', password='123456',
                       database='qianyan', charset='utf8mb4')
cur = conn.cursor()
cur.execute("SHOW COLUMNS FROM data_sources LIKE 'credentials_encrypted'")
if cur.fetchone():
    print("[OK] credentials_encrypted 列已存在，无需迁移")
else:
    cur.execute("ALTER TABLE data_sources ADD COLUMN credentials_encrypted TEXT "
                "COMMENT '加密后的凭证JSON' AFTER api_url")
    conn.commit()
    print("[OK] 已添加 credentials_encrypted 列")
cur.close()
conn.close()