import psycopg2
from psycopg2 import OperationalError
import os

class DBManager:
    """
    Класс для управления подключением к базе данных PostgreSQL и выполнения запросов.
    """
    def __init__(self, dbname="repair_tracker_db", user="postgres", password="your_secure_password", host="localhost", port="5432"):
        self.conn = None
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        
        try:
            self.conn = psycopg2.connect(
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            )
            self.conn.autocommit = True
            print("Успешное подключение к базе данных PostgreSQL.")
        except OperationalError as e:
            print(f"Ошибка подключения к базе данных: {e}")
            print("Убедитесь, что сервер PostgreSQL запущен и параметры подключения верны.")
            self.conn = None

    def execute_query(self, query, params=None, fetch_one=False, fetch_all=False):
        """Выполняет SQL-запрос."""
        if not self.conn:
            return None

        try:
            with self.conn.cursor() as cursor:
                if params is not None:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                if fetch_one:
                    return cursor.fetchone()
                if fetch_all:
                    return cursor.fetchall()
                return True
        except Exception as e:
            print(f"Ошибка при выполнении запроса: {e}")
            print(f"Запрос: {query[:200]}...")
            return None

    def create_schema(self, schema_file_path):
        """Создает схему базы данных, выполняя SQL-скрипт из файла."""
        if not self.conn:
            print("Невозможно создать схему: нет подключения к БД.")
            return False

        try:
            with open(schema_file_path, 'r', encoding='utf-8') as f:
                sql_script = f.read()
            
            with self.conn.cursor() as cursor:
                lines = []
                for line in sql_script.split('\n'):
                    if '--' in line:
                        line = line[:line.index('--')]
                    if line.strip():
                        lines.append(line)
                
                full_script = '\n'.join(lines)
                queries = [q.strip() for q in full_script.split(';') if q.strip()]
                
                for query in queries:
                    if query:
                        try:
                            cursor.execute(query)
                        except Exception as e:
                            error_msg = str(e).lower()
                            if 'already exists' in error_msg or 'существует' in error_msg or 'duplicate' in error_msg:
                                continue
                            print(f"Предупреждение при выполнении части скрипта: {e}")
                            print(f"Запрос: {query[:200]}...")
            
            print(f"Схема базы данных успешно создана из файла: {schema_file_path}")
            return True
        except FileNotFoundError:
            print(f"Ошибка: Файл схемы не найден по пути: {schema_file_path}")
            return False
        except Exception as e:
            print(f"Ошибка при создании схемы: {e}")
            return False

    def close(self):
        """Закрывает соединение с базой данных."""
        if self.conn:
            self.conn.close()
            print("Соединение с базой данных закрыто.")

    def backup_database(self, output_file="backup.sql"):
        """Выполняет резервное копирование базы данных с помощью pg_dump."""
        try:
            os.environ['PGPASSWORD'] = self.password
            
            command = (
                f"pg_dump -U {self.user} -h {self.host} -p {self.port} -d {self.dbname} "
                f"-F p -v -f {output_file}"
            )
            
            import subprocess
            process = subprocess.run(command, shell=True, capture_output=True, text=True)
            
            del os.environ['PGPASSWORD']
            
            if process.returncode == 0:
                print(f"Резервное копирование успешно завершено. Файл: {output_file}")
                return True
            else:
                print(f"Ошибка резервного копирования: {process.stderr}")
                return False
        except Exception as e:
            print(f"Критическая ошибка при выполнении pg_dump: {e}")
            return False

if __name__ == "__main__":
    db_manager = DBManager(
        dbname="repair_tracker_db", 
        user="postgres", 
        password="p4v17102006", 
        host="localhost"
    )
    
    if db_manager.conn:
        schema_path = os.path.join(os.path.dirname(__file__), "table.sql")
        db_manager.create_schema(schema_path)
    
    db_manager.close()
