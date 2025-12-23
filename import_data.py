import csv
from io import StringIO
from database_module import DBManager
from datetime import datetime
import os

# Пути к файлам данных
REPO_PATH = os.path.dirname(__file__)
USERS_FILE = os.path.join(REPO_PATH, "inputDataUsers.csv")
REQUESTS_FILE = os.path.join(REPO_PATH, "inputDataRequests.csv")
COMMENTS_FILE = os.path.join(REPO_PATH, "inputDataComments.csv")

def parse_csv_data(file_path):
    """Парсит csv файл с разделителем ';'."""
    data = []
    try:
        with open(file_path, 'r', encoding='utf-8-sig', newline='') as f:
            reader = csv.reader(f, delimiter=';')
            # Пропускаем заголовок
            next(reader)
            for row in reader:
                # Убираем лишние пробелы из каждого элемента
                cleaned_row = [item.strip() for item in row]
                if cleaned_row:
                    data.append(cleaned_row)
            return None, data # Возвращаем None вместо заголовка, так как он не используется
    except FileNotFoundError:
        print(f"Ошибка: Файл не найден: {file_path}")
        return None, None
    except Exception as e:
        print(f"Ошибка при парсинге файла {file_path}: {e}")
        return None, None

def import_users(db_manager):
    """Импортирует данные пользователей."""
    print("--- Импорт пользователей ---")
    _, users_data = parse_csv_data(USERS_FILE)
    if not users_data:
        return

    # Разделяем пользователей на клиентов и мастеров/системных пользователей
    clients_to_import = []
    masters_to_import = []
    system_users_to_import = []
    
    # Добавление пользователя Администратора (логин: admin, пароль: admin)
    admin_user = (999, 'admin', 'admin', 'Администратор', 'Системный Администратор', 'N/A')
    system_users_to_import.append(admin_user)
    
    for row in users_data:
        user_id, fio, phone, login, password, user_type = row
        
        # Проверка на дублирование с Admin
        if int(user_id) == 999:
            print(f"Предупреждение: Пользователь с ID 999 уже существует в inputDataUsers.csv. Пропускаем.")
            continue
            
        if user_type == 'Заказчик':
            # Заказчик -> Таблица clients
            clients_to_import.append((int(user_id), fio, phone))
        else:
            # Мастер, Менеджер, Оператор -> Таблица masters и users
            system_users_to_import.append((int(user_id), login, password, user_type, fio, phone))
            if user_type == 'Мастер':
                masters_to_import.append((int(user_id), fio))

    # Импорт клиентов
    client_query = "INSERT INTO clients (client_id, full_name, phone_number) VALUES (%s, %s, %s) ON CONFLICT (client_id) DO NOTHING;"
    for client in clients_to_import:
        db_manager.execute_query(client_query, client)
    print(f"Импортировано {len(clients_to_import)} клиентов.")
    
    # Обновляем последовательности для таблиц с явными ID (если они используют SERIAL)
    # Примечание: clients, masters, users используют INTEGER PRIMARY KEY, не SERIAL, поэтому последовательности нет

    # Импорт мастеров
    master_query = "INSERT INTO masters (master_id, full_name) VALUES (%s, %s) ON CONFLICT (master_id) DO NOTHING;"
    for master in masters_to_import:
        db_manager.execute_query(master_query, master)
    print(f"Импортировано {len(masters_to_import)} мастеров.")
    
    # Импорт системных пользователей
    # ВНИМАНИЕ: Пароли импортируются как есть, что небезопасно. В реальном приложении их нужно хэшировать.
    user_query = "INSERT INTO users (user_id, login, password_hash, role, fio, phone_number) VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (user_id) DO NOTHING;"
    for user in system_users_to_import:
        db_manager.execute_query(user_query, user)
    print(f"Импортировано {len(system_users_to_import)} системных пользователей.")

def import_requests(db_manager):
    """Импортирует данные заявок."""
    print("--- Импорт заявок ---")
    _, requests_data = parse_csv_data(REQUESTS_FILE)
    if not requests_data:
        return

    # Получаем ID справочников для преобразования строковых значений
    status_rows = db_manager.execute_query("SELECT status_name, status_id FROM statuses", fetch_all=True)
    status_map = {row[0]: row[1] for row in status_rows} if status_rows else {}
    
    # В ТЗ нет таблицы для homeTechType, но мы используем equipment_types
    # Создадим недостающие типы техники
    equipment_types = set(row[2] for row in requests_data)
    for eq_type in equipment_types:
        db_manager.execute_query("INSERT INTO equipment_types (type_name) VALUES (%s) ON CONFLICT (type_name) DO NOTHING", (eq_type,))
    
    type_rows = db_manager.execute_query("SELECT type_name, type_id FROM equipment_types", fetch_all=True)
    type_map = {row[0]: row[1] for row in type_rows} if type_rows else {}

    request_query = """
    INSERT INTO requests (request_id, date_created, type_id, model, description, status_id, date_completed, repair_parts, master_id, client_id)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (request_id) DO NOTHING;
    """
    
    imported_count = 0
    for row in requests_data:
        # requestID;startDate;homeTechType;homeTechModel;problemDescryption;requestStatus;completionDate;repairParts;masterID;clientID
        request_id, start_date, tech_type, model, description, status_name, completion_date, repair_parts, master_id, client_id = row[:10] # Берем только первые 10 полей
        
        # Преобразование типов
        request_id = int(request_id)
        client_id = int(client_id)
        
        # Исправление ошибки 'null' для master_id
        # Исправление ошибки смещения полей: проверяем, является ли значение числом
        master_id = master_id.strip()
        if master_id and master_id.lower() != 'null' and master_id.isdigit():
            master_id = int(master_id)
        else:
            master_id = None
        
        type_id = type_map.get(tech_type)
        # Если статус не указан или не найден, устанавливаем 'Новая' (ID=1)
        status_id = status_map.get(status_name.strip() if status_name else None, 1)
        
        # Преобразование дат
        try:
            date_created = datetime.strptime(start_date.strip(), '%Y-%m-%d') if start_date else None
        except (ValueError, AttributeError) as e:
            print(f"Ошибка при парсинге даты создания для заявки {request_id}: {start_date}. Устанавливаем None.")
            date_created = None
        
        try:
            date_completed = datetime.strptime(completion_date.strip(), '%Y-%m-%d') if completion_date and completion_date.strip().lower() != 'null' else None
        except (ValueError, AttributeError) as e:
            print(f"Ошибка при парсинге даты завершения для заявки {request_id}: {completion_date}. Устанавливаем None.")
            date_completed = None
        
        # repair_parts в файле пустой, если нет данных, но в запросе он должен быть строкой
        repair_parts = repair_parts if repair_parts else None
        
        # Вставка данных
        params = (
            request_id, date_created, type_id, model, description, status_id, 
            date_completed, repair_parts, master_id, client_id
        )
        db_manager.execute_query(request_query, params)
        imported_count += 1
    
    # Обновляем последовательность request_id до максимального значения + 1
    # Это необходимо, чтобы избежать конфликтов при создании новых заявок
    fix_sequence_query = """
    SELECT setval('requests_request_id_seq', COALESCE((SELECT MAX(request_id) FROM requests), 0) + 1, false);
    """
    db_manager.execute_query(fix_sequence_query)
    
    print(f"Импортировано {imported_count} заявок.")

def import_comments(db_manager):
    """Импортирует данные комментариев."""
    print("--- Импорт комментариев ---")
    _, comments_data = parse_csv_data(COMMENTS_FILE)
    if not comments_data:
        return

    comment_query = """
    INSERT INTO comments (comment_id, message, master_id, request_id)
    VALUES (%s, %s, %s, %s) ON CONFLICT (comment_id) DO NOTHING;
    """
    
    imported_count = 0
    for row in comments_data:
        # commentID;message;masterID;requestID
        comment_id, message, master_id, request_id = row
        
        # Преобразование типов
        comment_id = int(comment_id)
        
        # Обработка master_id (может быть пустым или 'null')
        master_id = master_id.strip() if master_id else ''
        if master_id and master_id.lower() != 'null' and master_id.isdigit():
            master_id = int(master_id)
        else:
            master_id = None
        
        request_id = int(request_id)
        
        # Вставка данных
        params = (comment_id, message, master_id, request_id)
        db_manager.execute_query(comment_query, params)
        imported_count += 1
    
    # Обновляем последовательность comment_id до максимального значения + 1
    # (если таблица использует SERIAL, иначе это не нужно)
    # fix_comment_sequence_query = """
    # SELECT setval('comments_comment_id_seq', COALESCE((SELECT MAX(comment_id) FROM comments), 0) + 1, false);
    # """
    # db_manager.execute_query(fix_comment_sequence_query)
    
    print(f"Импортировано {imported_count} комментариев.")

def main():
    # Инициализация DBManager (используйте свои реальные параметры)
    db_manager = DBManager(
        dbname="repair_tracker_db", 
        user="postgres", 
        password="p4v17102006", 
        host="localhost"
    )
    
    if not db_manager.conn:
        print("Не удалось подключиться к базе данных. Импорт невозможен.")
        return

    # 1. Создание схемы (если еще не создана)
    schema_path = os.path.join(os.path.dirname(__file__), "table.sql")
    
    if not os.path.exists(schema_path):
        print(f"КРИТИЧЕСКАЯ ОШИБКА: Файл схемы не найден по пути: {schema_path}")
        print("Убедитесь, что файл table.sql находится в папке, расположенной на один уровень выше, чем repair_tracker")
        return
        
    db_manager.create_schema(schema_path)
    
    # 2. Импорт данных
    import_users(db_manager)
    import_requests(db_manager)
    import_comments(db_manager)
    
    db_manager.close()
    print("Импорт данных завершен.")

if __name__ == "__main__":
    main()
