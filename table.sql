-- SQL-скрипт для создания таблиц в PostgreSQL
-- База данных: Учет заявок на ремонт бытовой техники

-- 1. Таблица для справочника типов техники
CREATE TABLE equipment_types (
    type_id SERIAL PRIMARY KEY,
    type_name VARCHAR(100) UNIQUE NOT NULL
);

-- 2. Таблица для справочника статусов заявки
CREATE TABLE statuses (
    status_id SERIAL PRIMARY KEY,
    status_name VARCHAR(50) UNIQUE NOT NULL
);

-- 3. Таблица для клиентов
CREATE TABLE clients (
    client_id INTEGER PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    address TEXT
);

-- 4. Таблица для мастеров
CREATE TABLE masters (
    master_id INTEGER PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    specialization VARCHAR(255)
);

-- 5. Основная таблица для заявок на ремонт
CREATE TABLE requests (
    request_id SERIAL PRIMARY KEY,
    
    -- Внешние ключи
    client_id INTEGER NOT NULL,
    master_id INTEGER, -- Может быть NULL, пока мастер не назначен
    type_id INTEGER NOT NULL,
    status_id INTEGER NOT NULL,
    
    -- Информация о технике и проблеме
    model VARCHAR(100) NOT NULL,
    serial_number VARCHAR(100),
    description TEXT NOT NULL,
    
    -- Даты и время
    date_created TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    date_start_work TIMESTAMP WITH TIME ZONE,
    date_completed TIMESTAMP WITH TIME ZONE,
    
    -- Финансовая информация
    repair_parts TEXT,
    cost NUMERIC(10, 2) DEFAULT 0.00,
    
    -- Ограничения внешних ключей
    CONSTRAINT fk_client
        FOREIGN KEY (client_id)
        REFERENCES clients (client_id)
        ON DELETE RESTRICT,
        
    CONSTRAINT fk_master
        FOREIGN KEY (master_id)
        REFERENCES masters (master_id)
        ON DELETE SET NULL, -- Если мастер уволен, заявка остается, но мастер обнуляется
        
    CONSTRAINT fk_equipment_type
        FOREIGN KEY (type_id)
        REFERENCES equipment_types (type_id)
        ON DELETE RESTRICT,
        
    CONSTRAINT fk_status
        FOREIGN KEY (status_id)
        REFERENCES statuses (status_id)
        ON DELETE RESTRICT
);

-- Создание индексов для ускорения поиска по внешним ключам и часто используемым полям
CREATE INDEX idx_requests_client_id ON requests (client_id);
CREATE INDEX idx_requests_master_id ON requests (master_id);
CREATE INDEX idx_requests_status_id ON requests (status_id);
CREATE INDEX idx_clients_phone_number ON clients (phone_number);
CREATE INDEX idx_requests_date_created ON requests (date_created);

-- Добавление начальных данных в справочники (для примера)
INSERT INTO equipment_types (type_name) VALUES 
('Холодильник'), 
('Стиральная машина'), 
('Посудомоечная машина'), 
('Пылесос'), 
('Микроволновая печь');

INSERT INTO statuses (status_name) VALUES 
('Новая'), 
('В работе'), 
('Ожидание запчастей'), 
('Выполнена'), 
('Отменена');

-- 6. Таблица для системных пользователей (для входа в систему)
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    login VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL, -- В реальном приложении нужно хранить хэш
    role VARCHAR(50) NOT NULL, -- Менеджер, Оператор, Мастер
    fio VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20)
);

-- 7. Таблица для комментариев к заявкам
CREATE TABLE comments (
    comment_id INTEGER PRIMARY KEY,
    message TEXT NOT NULL,
    master_id INTEGER NOT NULL,
    request_id INTEGER NOT NULL,
    date_posted TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_comment_master
        FOREIGN KEY (master_id)
        REFERENCES masters (master_id)
        ON DELETE RESTRICT,
        
    CONSTRAINT fk_comment_request
        FOREIGN KEY (request_id)
        REFERENCES requests (request_id)
        ON DELETE CASCADE
);
