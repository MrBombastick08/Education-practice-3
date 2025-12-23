from database_module import DBManager
from datetime import datetime, timedelta

class RepairTracker:
    """
    Класс, реализующий основную бизнес-логику системы учета заявок.
    """
    def __init__(self, db_manager):
        self.db = db_manager

    def add_new_request(self, client_id, type_id, model, description, serial_number=None):
        """Добавляет новую заявку в базу данных."""
        query = """
        INSERT INTO requests (client_id, type_id, model, description, serial_number, status_id)
        VALUES (%s, %s, %s, %s, %s, (SELECT status_id FROM statuses WHERE status_name = 'Новая'))
        RETURNING request_id;
        """
        params = (client_id, type_id, model, description, serial_number)
        result = self.db.execute_query(query, params, fetch_one=True)
        
        # Если возникла ошибка из-за конфликта последовательности, обновляем её и повторяем запрос
        if not result:
            # Обновляем последовательность до максимального значения + 1
            fix_sequence_query = """
            SELECT setval('requests_request_id_seq', COALESCE((SELECT MAX(request_id) FROM requests), 0) + 1, false);
            """
            self.db.execute_query(fix_sequence_query)
            # Повторяем запрос
            result = self.db.execute_query(query, params, fetch_one=True)
        
        if result:
            print(f"Заявка №{result[0]} успешно создана.")
            return result[0]
        return None

    def assign_master(self, request_id, master_id):
        """Назначает мастера на заявку и меняет статус на 'В работе'."""
        query = """
        UPDATE requests
        SET master_id = %s, 
            status_id = (SELECT status_id FROM statuses WHERE status_name = 'В работе'),
            date_start_work = CURRENT_TIMESTAMP
        WHERE request_id = %s
        RETURNING request_id;
        """
        params = (master_id, request_id)
        result = self.db.execute_query(query, params, fetch_one=True)
        if result:
            print(f"Мастер {master_id} назначен на заявку №{request_id}.")
            return True
        return False

    def authenticate_user(self, login, password):
        """Проверяет логин и пароль пользователя и возвращает его роль и ID."""
        # ВНИМАНИЕ: Пароль передается открытым текстом, что небезопасно. 
        # В реальном приложении пароль должен быть хэширован.
        query = """
        SELECT user_id, role, fio
        FROM users
        WHERE login = %s AND password_hash = %s;
        """
        result = self.db.execute_query(query, (login, password), fetch_one=True)
        if result:
            user_id, role, fio = result
            return {'user_id': user_id, 'role': role, 'fio': fio}
        return None

    def complete_request(self, request_id, cost):
        """Завершает заявку, устанавливает стоимость и меняет статус на 'Выполнена'."""
        query = """
        UPDATE requests
        SET status_id = (SELECT status_id FROM statuses WHERE status_name = 'Выполнена'),
            date_completed = CURRENT_TIMESTAMP,
            cost = %s
        WHERE request_id = %s
        RETURNING request_id;
        """
        params = (cost, request_id)
        result = self.db.execute_query(query, params, fetch_one=True)
        if result:
            print(f"Заявка №{request_id} успешно завершена.")
            return True
        return False

    def register_client(self, fio, phone, login, password):
        """Регистрирует нового клиента и системного пользователя."""
        if self.authenticate_user(login, password):
            return False
            
        max_id_query = "SELECT MAX(user_id) FROM users;"
        max_id = self.db.execute_query(max_id_query, fetch_one=True)[0]
        new_id = (max_id if max_id else 0) + 1
        
        user_query = "INSERT INTO users (user_id, login, password_hash, role, fio, phone_number) VALUES (%s, %s, %s, %s, %s, %s);"
        self.db.execute_query(user_query, (new_id, login, password, 'Клиент', fio, phone))
        
        client_query = "INSERT INTO clients (client_id, full_name, phone_number) VALUES (%s, %s, %s);"
        self.db.execute_query(client_query, (new_id, fio, phone))
        
        print(f"Клиент {fio} успешно зарегистрирован с ID {new_id}.")
        return True

    def get_request_details(self, request_id):
        """Возвращает детальную информацию о заявке для QR-кода."""
        query = """
        SELECT 
            r.request_id, 
            c.full_name AS client_name, 
            et.type_name || ' (' || r.model || ')' AS equipment,
            r.description,
            COALESCE(m.full_name, 'Не назначен') AS master_name,
            s.status_name,
            r.date_created
        FROM requests r
        JOIN clients c ON r.client_id = c.client_id
        JOIN equipment_types et ON r.type_id = et.type_id
        JOIN statuses s ON r.status_id = s.status_id
        LEFT JOIN masters m ON r.master_id = m.master_id
        WHERE r.request_id = %s;
        """
        result = self.db.execute_query(query, (request_id,), fetch_one=True)
        if result:
            return {
                'request_id': result[0],
                'client_name': result[1],
                'equipment': result[2],
                'description': result[3],
                'master_name': result[4],
                'status_name': result[5],
                'date_created': result[6]
            }
        return None

    def get_request_status_info(self, request_id):
        """Возвращает статус и информацию о мастере заявки для валидации действий."""
        query = """
        SELECT 
            r.status_id,
            s.status_name,
            r.master_id
        FROM requests r
        JOIN statuses s ON r.status_id = s.status_id
        WHERE r.request_id = %s;
        """
        result = self.db.execute_query(query, (request_id,), fetch_one=True)
        if result:
            return {
                'status_id': result[0],
                'status_name': result[1],
                'master_id': result[2]
            }
        return None

    def complete_request(self, request_id, status_id, cost, repair_parts):
        """Завершает заявку, устанавливает статус, стоимость и детали ремонта."""
        query = """
        UPDATE requests
        SET status_id = %s,
            date_completed = CURRENT_TIMESTAMP,
            cost = %s,
            repair_parts = %s
        WHERE request_id = %s
        RETURNING request_id;
        """
        params = (status_id, cost, repair_parts, request_id)
        result = self.db.execute_query(query, params, fetch_one=True)
        if result:
            print(f"Заявка №{request_id} успешно завершена.")
            return True
        return False

    def calculate_average_repair_time(self, start_date=None, end_date=None):
        """
        Реализация алгоритма "Расчет среднего времени ремонта" (Задача 1).
        Рассчитывает среднее время между date_start_work и date_completed 
        для завершенных заявок в заданном периоде.
        """
        query = """
        SELECT date_start_work, date_completed
        FROM requests
        WHERE status_id = (SELECT status_id FROM statuses WHERE status_name = 'Выполнена')
        """
        
        params = []
        
        if start_date:
            query += " AND date_completed >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND date_completed <= %s"
            params.append(end_date)
            
        completed_requests = self.db.execute_query(query, tuple(params), fetch_all=True)
        
        if not completed_requests:
            return 0.0, 0

        total_time_seconds = 0
        completed_count = 0

        for start_time, end_time in completed_requests:
            if start_time and end_time:
                time_delta = end_time - start_time
                total_time_seconds += time_delta.total_seconds()
                completed_count += 1

        if completed_count == 0:
            return 0.0, 0

        average_time_seconds = total_time_seconds / completed_count
        average_time_hours = average_time_seconds / 3600

        return average_time_hours, completed_count

    def get_status_report(self):
        """Возвращает отчет по количеству заявок в каждом статусе."""
        query = """
        SELECT s.status_name, COUNT(r.request_id)
        FROM statuses s
        LEFT JOIN requests r ON s.status_id = r.status_id
        GROUP BY s.status_name
        ORDER BY COUNT(r.request_id) DESC;
        """
        return self.db.execute_query(query, fetch_all=True)

    def get_master_load_report(self):
        """Возвращает отчет по загрузке мастеров (количество назначенных заявок)."""
        query = """
        SELECT 
            m.full_name, 
            COUNT(r.request_id) AS assigned_requests
        FROM masters m
        LEFT JOIN requests r ON m.master_id = r.master_id
        GROUP BY m.full_name
        ORDER BY assigned_requests DESC;
        """
        return self.db.execute_query(query, fetch_all=True)

    def update_request_description(self, request_id, description):
        """Обновляет описание заявки."""
        query = """
        UPDATE requests
        SET description = %s
        WHERE request_id = %s
        RETURNING request_id;
        """
        result = self.db.execute_query(query, (description, request_id), fetch_one=True)
        if result:
            print(f"Описание заявки №{request_id} успешно обновлено.")
            return True
        return False

    def update_request_status(self, request_id, status_id):
        """Обновляет статус заявки."""
        query = """
        UPDATE requests
        SET status_id = %s
        WHERE request_id = %s
        RETURNING request_id;
        """
        result = self.db.execute_query(query, (status_id, request_id), fetch_one=True)
        if result:
            print(f"Статус заявки №{request_id} успешно обновлен.")
            return True
        return False

    def master_respond_to_request(self, request_id, master_id):
        """Позволяет мастеру откликнуться на нераспределенную заявку."""
        check_query = "SELECT master_id FROM requests WHERE request_id = %s;"
        result = self.db.execute_query(check_query, (request_id,), fetch_one=True)
        if not result:
            return False
        
        if result[0] is not None:
            return False
        
        return self.assign_master(request_id, master_id)

    def get_master_performance_report(self):
        """Возвращает отчет для менеджера: кто выполнял какие заявки."""
        query = """
        SELECT 
            m.full_name AS master_name,
            r.request_id,
            c.full_name AS client_name,
            et.type_name || ' (' || r.model || ')' AS equipment,
            s.status_name,
            r.date_created,
            r.date_start_work,
            r.date_completed,
            r.cost
        FROM requests r
        JOIN clients c ON r.client_id = c.client_id
        JOIN equipment_types et ON r.type_id = et.type_id
        JOIN statuses s ON r.status_id = s.status_id
        LEFT JOIN masters m ON r.master_id = m.master_id
        WHERE r.master_id IS NOT NULL
        ORDER BY m.full_name, r.date_created DESC;
        """
        return self.db.execute_query(query, fetch_all=True)

    def get_all_users(self):
        """Возвращает список всех пользователей системы для администратора."""
        query = """
        SELECT user_id, login, role, fio, phone_number
        FROM users
        ORDER BY role, fio;
        """
        return self.db.execute_query(query, fetch_all=True)

    def update_user_role(self, user_id, new_role):
        """Обновляет роль пользователя (только для администратора)."""
        allowed_roles = ['Администратор', 'Менеджер', 'Оператор', 'Мастер', 'Клиент']
        if new_role not in allowed_roles:
            return False
        
        query = """
        UPDATE users
        SET role = %s
        WHERE user_id = %s
        RETURNING user_id;
        """
        result = self.db.execute_query(query, (new_role, user_id), fetch_one=True)
        if result:
            print(f"Роль пользователя {user_id} успешно изменена на {new_role}.")
            return True
        return False

if __name__ == "__main__":
    print("RepairTracker class is ready.")
