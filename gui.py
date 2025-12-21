import sys
import os
import qrcode
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QLabel, QLineEdit, QPushButton, QTableWidget, 
    QTableWidgetItem, QHeaderView, QMessageBox, QDialog, QFormLayout,
    QComboBox, QTextEdit, QInputDialog, QSpinBox, QDoubleSpinBox,
    QGridLayout, QFileDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap
from database_module import DBManager
from main_app import RepairTracker

class RegistrationDialog(QDialog):
    def __init__(self, tracker, parent=None):
        super().__init__(parent)
        self.tracker = tracker
        self.setWindowTitle("Регистрация Клиента")
        self.setGeometry(300, 300, 350, 250)
        
        layout = QFormLayout(self)
        
        self.fio_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.login_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        layout.addRow("ФИО:", self.fio_input)
        layout.addRow("Телефон:", self.phone_input)
        layout.addRow("Логин:", self.login_input)
        layout.addRow("Пароль:", self.password_input)
        
        self.register_button = QPushButton("Зарегистрироваться")
        self.register_button.clicked.connect(self.register_user)
        layout.addRow(self.register_button)

    def register_user(self):
        fio = self.fio_input.text().strip()
        phone = self.phone_input.text().strip()
        login = self.login_input.text().strip()
        password = self.password_input.text()
        
        if not all([fio, phone, login, password]):
            QMessageBox.warning(
                self, 
                "Ошибка ввода данных", 
                "Все поля должны быть заполнены. Пожалуйста, заполните все обязательные поля и попробуйте снова."
            )
            return
        
        if len(login) < 3 or len(password) < 3:
            QMessageBox.warning(
                self, 
                "Ошибка валидации", 
                "Логин и пароль должны содержать не менее 3 символов. Пожалуйста, введите более длинные значения."
            )
            return

        try:
            success = self.tracker.register_client(fio, phone, login, password)
            
            if success:
                QMessageBox.information(
                    self, 
                    "Регистрация успешна", 
                    "Регистрация прошла успешно! Теперь вы можете войти в систему, используя свой логин и пароль."
                )
                self.accept()
            else:
                QMessageBox.critical(
                    self, 
                    "Ошибка регистрации", 
                    "Не удалось зарегистрировать пользователя. Возможные причины:\n"
                    "- Логин уже занят другим пользователем\n"
                    "- Ошибка подключения к базе данных\n"
                    "Пожалуйста, попробуйте использовать другой логин или обратитесь к администратору."
                )
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Критическая ошибка", 
                f"Произошла непредвиденная ошибка при регистрации:\n{str(e)}\n\n"
                "Пожалуйста, проверьте подключение к базе данных и попробуйте снова. "
                "Если проблема сохраняется, обратитесь к системному администратору."
            )


class LoginDialog(QDialog):
    def __init__(self, tracker, parent=None):
        super().__init__(parent)
        self.tracker = tracker
        self.setWindowTitle("Вход в Систему")
        self.setGeometry(300, 300, 350, 200)
        
        self.user_info = None

        layout = QFormLayout(self)
        
        self.login_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.toggle_password_btn = QPushButton(QIcon.fromTheme("view-reveal-symbolic"), "")
        self.toggle_password_btn.setFixedWidth(30)
        self.toggle_password_btn.setCheckable(True)
        self.toggle_password_btn.clicked.connect(self.toggle_password_visibility)
        
        password_layout = QHBoxLayout()
        password_layout.addWidget(self.password_input)
        password_layout.addWidget(self.toggle_password_btn)
        
        layout.addRow("Логин:", self.login_input)
        layout.addRow("Пароль:", password_layout)
        
        button_layout = QHBoxLayout()
        self.login_button = QPushButton("Войти")
        self.login_button.clicked.connect(self.check_login)
        
        self.register_button = QPushButton("Регистрация")
        self.register_button.clicked.connect(self.show_registration_dialog)
        
        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.register_button)
        
        layout.addRow(button_layout)

    def toggle_password_visibility(self, checked):
        if checked:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

    def show_registration_dialog(self):
        reg_dialog = RegistrationDialog(self.tracker, self)
        reg_dialog.exec()

    def check_login(self):
        login = self.login_input.text().strip()
        password = self.password_input.text()
        
        if not login or not password:
            QMessageBox.warning(
                self, 
                "Ошибка ввода", 
                "Пожалуйста, введите логин и пароль для входа в систему."
            )
            return
        
        if len(login) < 3 or len(password) < 3:
            QMessageBox.warning(
                self, 
                "Ошибка валидации", 
                "Логин и пароль должны содержать не менее 3 символов. Пожалуйста, проверьте правильность ввода."
            )
            return

        try:
            user = self.tracker.authenticate_user(login, password)
            
            if user:
                self.user_info = user
                QMessageBox.information(
                    self, 
                    "Вход выполнен", 
                    f"Добро пожаловать, {user['fio']} ({user['role']})!"
                )
                self.accept()
            else:
                QMessageBox.critical(
                    self, 
                    "Ошибка аутентификации", 
                    "Неверный логин или пароль. Пожалуйста, проверьте правильность введенных данных и попробуйте снова.\n\n"
                    "Если вы забыли пароль, обратитесь к администратору системы."
                )
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Критическая ошибка", 
                f"Произошла ошибка при попытке входа в систему:\n{str(e)}\n\n"
                "Пожалуйста, проверьте подключение к базе данных и попробуйте снова. "
                "Если проблема сохраняется, обратитесь к системному администратору."
            )


class AddRequestDialog(QDialog):
    def __init__(self, tracker, parent=None):
        super().__init__(parent)
        self.tracker = tracker
        self.setWindowTitle("Добавить Новую Заявку")
        self.setGeometry(200, 200, 400, 300)
        
        self.layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()
        
        self.clients = self._load_data("SELECT client_id, full_name FROM clients ORDER BY full_name")
        self.equipment_types = self._load_data("SELECT type_id, type_name FROM equipment_types ORDER BY type_name")
        
        self.client_combo = QComboBox()
        self.client_combo.setEditable(False)
        for client_id, name in self.clients:
            self.client_combo.addItem(f"{name} (ID: {client_id})", userData=client_id)
        
        self.type_combo = QComboBox()
        self.type_combo.setEditable(False)
        for type_id, name in self.equipment_types:
            self.type_combo.addItem(name, userData=type_id)
        
        self.model_input = QLineEdit()
        self.serial_input = QLineEdit()
        self.description_input = QTextEdit()
        
        self.form_layout.addRow("Клиент:", self.client_combo)
        self.form_layout.addRow("Тип Техники:", self.type_combo)
        self.form_layout.addRow("Модель:", self.model_input)
        self.form_layout.addRow("Серийный номер:", self.serial_input)
        self.form_layout.addRow("Описание проблемы:", self.description_input)
        
        self.layout.addLayout(self.form_layout)
        
        self.save_button = QPushButton("Сохранить")
        self.cancel_button = QPushButton("Отмена")
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        self.layout.addLayout(button_layout)
        
        self.save_button.clicked.connect(self.save_request)
        self.cancel_button.clicked.connect(self.reject)

    def _load_data(self, query):
        """Загружает данные из БД для ComboBox'ов."""
        data = self.tracker.db.execute_query(query, fetch_all=True)
        return [(row[0], row[1]) for row in data] if data else []

    def save_request(self):
        """Сохраняет новую заявку в БД."""
        try:
            client_id = self.client_combo.currentData()
            if client_id is None:
                QMessageBox.warning(
                    self, 
                    "Ошибка ввода данных", 
                    "Пожалуйста, выберите клиента из списка."
                )
                return
            
            type_id = self.type_combo.currentData()
            if type_id is None:
                QMessageBox.warning(
                    self, 
                    "Ошибка ввода данных", 
                    "Пожалуйста, выберите тип техники из списка."
                )
                return
            
            model = self.model_input.text().strip()
            serial_number = self.serial_input.text().strip()
            description = self.description_input.toPlainText().strip()
            
            if not all([model, description]):
                QMessageBox.warning(
                    self, 
                    "Ошибка ввода данных", 
                    "Поля 'Модель' и 'Описание проблемы' являются обязательными и не могут быть пустыми.\n"
                    "Пожалуйста, заполните эти поля и попробуйте снова."
                )
                return

            request_id = self.tracker.add_new_request(
                client_id, 
                type_id, 
                model, 
                description, 
                serial_number if serial_number else None
            )
            
            if request_id:
                QMessageBox.information(
                    self, 
                    "Заявка создана", 
                    f"Заявка №{request_id} успешно добавлена в систему."
                )
                self.accept()
            else:
                QMessageBox.critical(
                    self, 
                    "Ошибка сохранения", 
                    "Не удалось добавить заявку в базу данных.\n\n"
                    "Возможные причины:\n"
                    "- Ошибка подключения к базе данных\n"
                    "- Нарушение ограничений целостности данных\n\n"
                    "Пожалуйста, проверьте подключение и попробуйте снова. "
                    "Если проблема сохраняется, обратитесь к администратору."
                )

        except Exception as e:
            QMessageBox.critical(
                self, 
                "Критическая ошибка", 
                f"Произошла непредвиденная ошибка при сохранении заявки:\n{str(e)}\n\n"
                "Пожалуйста, проверьте подключение к базе данных и попробуйте снова. "
                "Если проблема сохраняется, обратитесь к системному администратору."
            )


class AssignMasterDialog(QDialog):
    def __init__(self, tracker, request_id, parent=None):
        super().__init__(parent)
        self.tracker = tracker
        self.request_id = request_id
        self.setWindowTitle(f"Назначить Мастера на Заявку №{request_id}")
        self.setGeometry(200, 200, 400, 150)
        
        layout = QFormLayout(self)
        
        self.masters = self._load_masters()
        
        self.master_combo = QComboBox()
        self.master_combo.setEditable(False)
        self.master_combo.addItem("Не назначать", userData=None)
        for master_id, name in self.masters:
            self.master_combo.addItem(name, userData=master_id)
        
        layout.addRow("Выберите мастера:", self.master_combo)
        
        self.save_button = QPushButton("Назначить")
        self.cancel_button = QPushButton("Отмена")
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addRow(button_layout)
        
        self.save_button.clicked.connect(self.assign_master)
        self.cancel_button.clicked.connect(self.reject)

    def _load_masters(self):
        """Загружает список мастеров из БД."""
        data = self.tracker.db.execute_query("SELECT master_id, full_name FROM masters ORDER BY full_name", fetch_all=True)
        return [(row[0], row[1]) for row in data] if data else []

    def assign_master(self):
        """Назначает мастера на заявку."""
        try:
            master_index = self.master_combo.currentIndex()
            if master_index == 0:
                master_id = None
            else:
                master_id = self.master_combo.currentData()
            
            if self.tracker.assign_master(self.request_id, master_id):
                if master_id:
                    master_name = next(
                        (name for m_id, name in self.masters if m_id == master_id), 
                        "Неизвестный"
                    )
                    QMessageBox.information(
                        self, 
                        "Мастер назначен", 
                        f"Мастер {master_name} успешно назначен на заявку №{self.request_id}."
                    )
                else:
                    QMessageBox.information(
                        self, 
                        "Назначение отменено", 
                        f"Назначение мастера на заявку №{self.request_id} отменено."
                    )
                self.accept()
            else:
                QMessageBox.critical(
                    self, 
                    "Ошибка назначения", 
                    f"Не удалось назначить мастера на заявку №{self.request_id}.\n\n"
                    "Возможные причины:\n"
                    "- Заявка не найдена в базе данных\n"
                    "- Ошибка подключения к базе данных\n"
                    "- Нарушение ограничений целостности данных\n\n"
                    "Пожалуйста, проверьте подключение и попробуйте снова. "
                    "Если проблема сохраняется, обратитесь к администратору."
                )
        
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Критическая ошибка", 
                f"Произошла непредвиденная ошибка при назначении мастера:\n{str(e)}\n\n"
                "Пожалуйста, проверьте подключение к базе данных и попробуйте снова. "
                "Если проблема сохраняется, обратитесь к системному администратору."
            )


class CompleteRequestDialog(QDialog):
    def __init__(self, tracker, request_id, parent=None):
        super().__init__(parent)
        self.tracker = tracker
        self.request_id = request_id
        self.setWindowTitle(f"Завершить Ремонт Заявки №{request_id}")
        self.setGeometry(200, 200, 400, 250)
        
        layout = QFormLayout(self)
        
        self.statuses = self._load_statuses()
        
        self.status_combo = QComboBox()
        self.status_combo.setEditable(False)
        default_index = 0
        for i, (status_id, name) in enumerate(self.statuses):
            self.status_combo.addItem(name, userData=status_id)
            if name == "Выполнена":
                default_index = i
        self.status_combo.setCurrentIndex(default_index)
        
        self.cost_input = QDoubleSpinBox()
        self.cost_input.setMinimum(0)
        self.cost_input.setMaximum(999999.99)
        self.cost_input.setValue(0)
        
        self.repair_parts_input = QTextEdit()
        
        layout.addRow("Статус:", self.status_combo)
        layout.addRow("Стоимость ремонта:", self.cost_input)
        layout.addRow("Использованные детали:", self.repair_parts_input)
        
        self.save_button = QPushButton("Завершить")
        self.cancel_button = QPushButton("Отмена")
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addRow(button_layout)
        
        self.save_button.clicked.connect(self.complete_request)
        self.cancel_button.clicked.connect(self.reject)

    def _load_statuses(self):
        """Загружает список статусов из БД."""
        data = self.tracker.db.execute_query("SELECT status_id, status_name FROM statuses ORDER BY status_name", fetch_all=True)
        return [(row[0], row[1]) for row in data] if data else []

    def complete_request(self):
        """Завершает заявку."""
        try:
            status_id = self.status_combo.currentData()
            if status_id is None:
                QMessageBox.warning(
                    self, 
                    "Ошибка ввода данных", 
                    "Пожалуйста, выберите статус заявки из списка."
                )
                return
            cost = self.cost_input.value()
            repair_parts = self.repair_parts_input.toPlainText().strip()
            
            if cost <= 0:
                QMessageBox.warning(
                    self, 
                    "Ошибка ввода данных", 
                    "Стоимость ремонта должна быть больше нуля. Пожалуйста, введите корректное значение."
                )
                return
            
            if self.tracker.complete_request(self.request_id, status_id, cost, repair_parts):
                QMessageBox.information(
                    self, 
                    "Заявка завершена", 
                    f"Заявка №{self.request_id} успешно завершена и сохранена в базе данных."
                )
                self.accept()
            else:
                QMessageBox.critical(
                    self, 
                    "Ошибка завершения", 
                    f"Не удалось завершить заявку №{self.request_id}.\n\n"
                    "Возможные причины:\n"
                    "- Заявка не найдена в базе данных\n"
                    "- Ошибка подключения к базе данных\n"
                    "- Нарушение ограничений целостности данных\n\n"
                    "Пожалуйста, проверьте подключение и попробуйте снова. "
                    "Если проблема сохраняется, обратитесь к администратору."
                )
        
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Критическая ошибка", 
                f"Произошла непредвиденная ошибка при завершении заявки:\n{str(e)}\n\n"
                "Пожалуйста, проверьте подключение к базе данных и попробуйте снова. "
                "Если проблема сохраняется, обратитесь к системному администратору."
            )


class EditDescriptionDialog(QDialog):
    def __init__(self, tracker, request_id, current_description, parent=None):
        super().__init__(parent)
        self.tracker = tracker
        self.request_id = request_id
        self.setWindowTitle(f"Изменить Описание Заявки №{request_id}")
        self.setGeometry(200, 200, 500, 300)
        
        layout = QVBoxLayout(self)
        
        self.description_input = QTextEdit()
        self.description_input.setPlainText(current_description)
        layout.addWidget(QLabel("Описание проблемы:"))
        layout.addWidget(self.description_input)
        
        # Кнопки
        self.save_button = QPushButton("Сохранить")
        self.cancel_button = QPushButton("Отмена")
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        # Подключение сигналов
        self.save_button.clicked.connect(self.save_description)
        self.cancel_button.clicked.connect(self.reject)

    def save_description(self):
        """Сохраняет новое описание заявки."""
        try:
            description = self.description_input.toPlainText().strip()
            
            if not description:
                QMessageBox.warning(
                    self, 
                    "Ошибка ввода данных", 
                    "Описание проблемы не может быть пустым. Пожалуйста, введите описание проблемы."
                )
                return
            
            if self.tracker.update_request_description(self.request_id, description):
                QMessageBox.information(
                    self, 
                    "Описание обновлено", 
                    f"Описание заявки №{self.request_id} успешно обновлено в базе данных."
                )
                self.accept()
            else:
                QMessageBox.critical(
                    self, 
                    "Ошибка обновления", 
                    f"Не удалось обновить описание заявки №{self.request_id}.\n\n"
                    "Возможные причины:\n"
                    "- Заявка не найдена в базе данных\n"
                    "- Ошибка подключения к базе данных\n"
                    "- Нарушение ограничений целостности данных\n\n"
                    "Пожалуйста, проверьте подключение и попробуйте снова. "
                    "Если проблема сохраняется, обратитесь к администратору."
                )
        
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Критическая ошибка", 
                f"Произошла непредвиденная ошибка при обновлении описания:\n{str(e)}\n\n"
                "Пожалуйста, проверьте подключение к базе данных и попробуйте снова. "
                "Если проблема сохраняется, обратитесь к системному администратору."
            )


class ChangeStatusDialog(QDialog):
    def __init__(self, tracker, request_id, current_status_id, parent=None):
        super().__init__(parent)
        self.tracker = tracker
        self.request_id = request_id
        self.setWindowTitle(f"Изменить Статус Заявки №{request_id}")
        self.setGeometry(200, 200, 400, 150)
        
        layout = QFormLayout(self)
        
        self.statuses = self._load_statuses()
        
        self.status_combo = QComboBox()
        self.status_combo.setEditable(False)
        current_index = 0
        for i, (status_id, name) in enumerate(self.statuses):
            self.status_combo.addItem(name, userData=status_id)
            if status_id == current_status_id:
                current_index = i
        self.status_combo.setCurrentIndex(current_index)
        
        layout.addRow("Статус:", self.status_combo)
        
        self.save_button = QPushButton("Сохранить")
        self.cancel_button = QPushButton("Отмена")
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addRow(button_layout)
        
        self.save_button.clicked.connect(self.save_status)
        self.cancel_button.clicked.connect(self.reject)

    def _load_statuses(self):
        """Загружает список статусов из БД."""
        data = self.tracker.db.execute_query("SELECT status_id, status_name FROM statuses ORDER BY status_name", fetch_all=True)
        return [(row[0], row[1]) for row in data] if data else []

    def save_status(self):
        """Сохраняет новый статус заявки."""
        try:
            status_id = self.status_combo.currentData()
            if status_id is None:
                QMessageBox.warning(
                    self, 
                    "Ошибка ввода данных", 
                    "Пожалуйста, выберите статус заявки из списка."
                )
                return
            
            if self.tracker.update_request_status(self.request_id, status_id):
                status_name = next(
                    (name for s_id, name in self.statuses if s_id == status_id), 
                    "Неизвестный"
                )
                QMessageBox.information(
                    self, 
                    "Статус обновлен", 
                    f"Статус заявки №{self.request_id} успешно изменен на '{status_name}'."
                )
                self.accept()
            else:
                QMessageBox.critical(
                    self, 
                    "Ошибка обновления", 
                    f"Не удалось обновить статус заявки №{self.request_id}.\n\n"
                    "Возможные причины:\n"
                    "- Заявка не найдена в базе данных\n"
                    "- Ошибка подключения к базе данных\n"
                    "- Нарушение ограничений целостности данных\n\n"
                    "Пожалуйста, проверьте подключение и попробуйте снова. "
                    "Если проблема сохраняется, обратитесь к администратору."
                )
        
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Критическая ошибка", 
                f"Произошла непредвиденная ошибка при обновлении статуса:\n{str(e)}\n\n"
                "Пожалуйста, проверьте подключение к базе данных и попробуйте снова. "
                "Если проблема сохраняется, обратитесь к системному администратору."
            )


class AssignRoleDialog(QDialog):
    def __init__(self, tracker, user_id, current_role, user_fio, parent=None):
        super().__init__(parent)
        self.tracker = tracker
        self.user_id = user_id
        self.setWindowTitle(f"Назначить Роль Пользователю: {user_fio}")
        self.setGeometry(200, 200, 400, 150)
        
        layout = QFormLayout(self)
        
        self.roles = [
            ('Администратор', 'Администратор'),
            ('Менеджер', 'Менеджер'),
            ('Оператор', 'Оператор'),
            ('Мастер', 'Мастер'),
            ('Клиент', 'Клиент')
        ]
        
        self.role_combo = QComboBox()
        self.role_combo.setEditable(False)
        current_index = 0
        for i, (role_id, role_name) in enumerate(self.roles):
            self.role_combo.addItem(role_name, userData=role_id)
            if role_id == current_role:
                current_index = i
        self.role_combo.setCurrentIndex(current_index)
        
        layout.addRow("Роль:", self.role_combo)
        
        self.save_button = QPushButton("Сохранить")
        self.cancel_button = QPushButton("Отмена")
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addRow(button_layout)
        
        self.save_button.clicked.connect(self.save_role)
        self.cancel_button.clicked.connect(self.reject)

    def save_role(self):
        """Сохраняет новую роль пользователя."""
        try:
            new_role = self.role_combo.currentData()
            if new_role is None:
                QMessageBox.warning(
                    self, 
                    "Ошибка ввода данных", 
                    "Пожалуйста, выберите роль из списка."
                )
                return
            
            if self.tracker.update_user_role(self.user_id, new_role):
                QMessageBox.information(
                    self, 
                    "Роль обновлена", 
                    f"Роль пользователя успешно изменена на '{new_role}'."
                )
                self.accept()
            else:
                QMessageBox.critical(
                    self, 
                    "Ошибка обновления", 
                    f"Не удалось обновить роль пользователя.\n\n"
                    "Возможные причины:\n"
                    "- Пользователь не найден в базе данных\n"
                    "- Ошибка подключения к базе данных\n"
                    "- Нарушение ограничений целостности данных\n\n"
                    "Пожалуйста, проверьте подключение и попробуйте снова. "
                    "Если проблема сохраняется, обратитесь к администратору."
                )
        
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Критическая ошибка", 
                f"Произошла непредвиденная ошибка при обновлении роли:\n{str(e)}\n\n"
                "Пожалуйста, проверьте подключение к базе данных и попробуйте снова. "
                "Если проблема сохраняется, обратитесь к системному администратору."
            )


class QRCodeDialog(QDialog):
    def __init__(self, tracker, request_id, parent=None):
        super().__init__(parent)
        self.tracker = tracker
        self.request_id = request_id
        self.setWindowTitle(f"QR-код для Заявки №{request_id}")
        self.setGeometry(200, 200, 350, 400)
        
        layout = QVBoxLayout(self)
        
        self.qr_label = QLabel("Генерация QR-кода...")
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.qr_label)
        
        self.save_button = QPushButton("Сохранить QR-код")
        self.save_button.clicked.connect(self.save_qr_code)
        layout.addWidget(self.save_button)
        
        self.generate_qr_code()

    def generate_qr_code(self):
        # Получаем данные заявки для QR-кода
        request_data = self.tracker.get_request_details(self.request_id)
        if not request_data:
            self.qr_label.setText("Ошибка: Заявка не найдена.")
            return

        # Формируем текст для QR-кода
        qr_text = f"Заявка №{self.request_id}\n"
        qr_text += f"Клиент: {request_data['client_name']}\n"
        qr_text += f"Техника: {request_data['equipment']}\n"
        qr_text += f"Статус: {request_data['status_name']}\n"
        qr_text += f"Описание: {request_data['description'][:50]}..."
        
        # Генерируем QR-код
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_text)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        
        # Сохраняем во временный файл для отображения
        import tempfile
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"qr_code_{self.request_id}.png")
        img.save(temp_path)
        
        # Отображаем в QLabel
        pixmap = QPixmap(temp_path)
        self.qr_label.setPixmap(pixmap.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.qr_label.setText("") # Очищаем текст "Генерация..."
        self.temp_path = temp_path

    def save_qr_code(self):
        if not hasattr(self, 'temp_path'):
            QMessageBox.warning(self, "Ошибка", "QR-код не сгенерирован.")
            return
            
        # Диалог сохранения файла
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "Сохранить QR-код", 
            f"qr_code_request_{self.request_id}.png", 
            "PNG Files (*.png)"
        )
        
        if filename:
            try:
                # Копируем временный файл в выбранное пользователем место
                os.rename(self.temp_path, filename)
                QMessageBox.information(self, "Успех", f"QR-код успешно сохранен в {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл: {e}")


# --- Главное Окно ---

class MainWindow(QMainWindow):
    def __init__(self, tracker, user_info):
        super().__init__()
        self.tracker = tracker
        self.user_info = user_info
        self.setWindowTitle(f"Система Учета Заявок на Ремонт (PyQt6) - Пользователь: {user_info['fio']} ({user_info['role']})")
        self.setGeometry(100, 100, 1200, 700)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.layout = QVBoxLayout(self.central_widget)
        
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)
        
        # Создание вкладок
        self.create_requests_tab()
        self.create_clients_tab()
        self.create_masters_tab()
        self.create_reports_tab()
        
        if self.user_info['role'] == 'Администратор':
            self.create_users_tab()
        
        # Кнопка выхода
        exit_button = QPushButton("Выйти")
        exit_button.clicked.connect(self.logout)
        self.layout.addWidget(exit_button)
        
        # Инициализация данных при запуске
        self.load_requests()

    def create_requests_tab(self):
        """Создает вкладку для управления заявками."""
        self.requests_tab = QWidget()
        self.tabs.addTab(self.requests_tab, "Заявки")
        
        layout = QVBoxLayout(self.requests_tab)
        
        # Таблица для отображения заявок
        self.requests_table = QTableWidget()
        self.requests_table.setColumnCount(7)
        self.requests_table.setHorizontalHeaderLabels([
            "ID", "Клиент", "Техника", "Описание", "Мастер", "Статус", "Дата создания"
        ])
        self.requests_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.requests_table)
        
        # Кнопки управления
        button_layout = QHBoxLayout()
        self.add_request_btn = QPushButton("Добавить Заявку")
        self.assign_master_btn = QPushButton("Назначить Мастера")
        self.complete_request_btn = QPushButton("Завершить Ремонт")
        self.edit_description_btn = QPushButton("Изменить Описание")
        self.change_status_btn = QPushButton("Изменить Статус")
        self.respond_to_request_btn = QPushButton("Откликнуться на Заявку")
        self.qr_code_btn = QPushButton("QR-код Заявки")
        self.refresh_btn = QPushButton("Обновить")
        
        button_layout.addWidget(self.add_request_btn)
        button_layout.addWidget(self.assign_master_btn)
        button_layout.addWidget(self.complete_request_btn)
        button_layout.addWidget(self.edit_description_btn)
        button_layout.addWidget(self.change_status_btn)
        button_layout.addWidget(self.respond_to_request_btn)
        button_layout.addWidget(self.qr_code_btn)
        button_layout.addWidget(self.refresh_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # Подключение сигналов
        self.add_request_btn.clicked.connect(self.show_add_request_dialog)
        self.assign_master_btn.clicked.connect(self.show_assign_master_dialog)
        self.complete_request_btn.clicked.connect(self.show_complete_request_dialog)
        self.edit_description_btn.clicked.connect(self.show_edit_description_dialog)
        self.change_status_btn.clicked.connect(self.show_change_status_dialog)
        self.respond_to_request_btn.clicked.connect(self.show_respond_to_request_dialog)
        self.qr_code_btn.clicked.connect(self.show_qr_code_dialog)
        self.refresh_btn.clicked.connect(self.load_requests)
        
        # Применение RBAC к кнопкам
        self.apply_rbac_to_requests_tab()

    def apply_rbac_to_requests_tab(self):
        role = self.user_info['role']
        
        # Скрываем все кнопки по умолчанию, кроме "Обновить"
        self.add_request_btn.setVisible(False)
        self.assign_master_btn.setVisible(False)
        self.complete_request_btn.setVisible(False)
        self.edit_description_btn.setVisible(False)
        self.change_status_btn.setVisible(False)
        self.respond_to_request_btn.setVisible(False)
        self.qr_code_btn.setVisible(False)
        
        # Администратор: полный функционал
        if role == 'Администратор':
            self.add_request_btn.setVisible(True)
            self.assign_master_btn.setVisible(True)
            self.complete_request_btn.setVisible(True)
            self.edit_description_btn.setVisible(True)
            self.change_status_btn.setVisible(True)
            self.qr_code_btn.setVisible(True)
        
        # Менеджер: статистика, заявки, кто выполнял какие заявки
        elif role == 'Менеджер':
            self.add_request_btn.setVisible(True)
            self.assign_master_btn.setVisible(True)
            self.complete_request_btn.setVisible(True)
            self.qr_code_btn.setVisible(True)
        
        # Оператор: назначение мастера, изменение статуса, изменение описания
        elif role == 'Оператор':
            self.add_request_btn.setVisible(True)
            self.assign_master_btn.setVisible(True)
            self.edit_description_btn.setVisible(True)
            self.change_status_btn.setVisible(True)
            self.qr_code_btn.setVisible(True)
        
        # Мастер (Сотрудник): просмотр своих заявок, отклик на нераспределенные заявки
        elif role == 'Мастер':
            self.complete_request_btn.setVisible(True)
            self.respond_to_request_btn.setVisible(True)
            self.qr_code_btn.setVisible(True)
            
        # Клиент: может добавить заявку и посмотреть свои заявки
        elif role == 'Клиент':
            self.add_request_btn.setVisible(True)
            self.qr_code_btn.setVisible(True)

    def create_clients_tab(self):
        """Создает вкладку для управления клиентами."""
        self.clients_tab = QWidget()
        self.tabs.addTab(self.clients_tab, "Клиенты")
        
        layout = QVBoxLayout(self.clients_tab)
        
        # Таблица для отображения клиентов
        self.clients_table = QTableWidget()
        self.clients_table.setColumnCount(3)
        self.clients_table.setHorizontalHeaderLabels(["ID", "ФИО", "Телефон"])
        self.clients_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.clients_table)
        
        # Кнопка обновления
        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self.load_clients)
        layout.addWidget(refresh_btn)
        
        # Загрузить данные при инициализации
        self.load_clients()
        
        # Применение RBAC к вкладке
        if self.user_info['role'] not in ['Администратор', 'Менеджер', 'Оператор']:
            self.tabs.setTabVisible(self.tabs.indexOf(self.clients_tab), False)

    def create_masters_tab(self):
        """Создает вкладку для управления мастерами."""
        self.masters_tab = QWidget()
        self.tabs.addTab(self.masters_tab, "Мастера")
        
        layout = QVBoxLayout(self.masters_tab)
        
        # Таблица для отображения мастеров
        self.masters_table = QTableWidget()
        self.masters_table.setColumnCount(2)
        self.masters_table.setHorizontalHeaderLabels(["ID", "ФИО"])
        self.masters_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.masters_table)
        
        # Кнопка обновления
        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self.load_masters)
        layout.addWidget(refresh_btn)
        
        # Загрузить данные при инициализации
        self.load_masters()
        
        # Применение RBAC к вкладке
        if self.user_info['role'] not in ['Администратор', 'Менеджер', 'Оператор']:
            self.tabs.setTabVisible(self.tabs.indexOf(self.masters_tab), False)

    def create_reports_tab(self):
        """Создает вкладку для отчетов, включая расчет среднего времени."""
        self.reports_tab = QWidget()
        self.tabs.addTab(self.reports_tab, "Отчеты")
        
        layout = QVBoxLayout(self.reports_tab)
        
        # Секция для расчета среднего времени ремонта
        avg_time_group = QWidget()
        avg_time_layout = QHBoxLayout(avg_time_group)
        
        self.calc_avg_time_btn = QPushButton("Рассчитать Среднее Время Ремонта")
        self.avg_time_result_label = QLabel("Среднее время: -")
        
        avg_time_layout.addWidget(self.calc_avg_time_btn)
        avg_time_layout.addWidget(self.avg_time_result_label)
        avg_time_layout.addStretch(1)
        
        layout.addWidget(avg_time_group)
        
        # Подключение сигнала
        self.calc_avg_time_btn.clicked.connect(self.calculate_avg_time)
        
        # Добавление новых отчетов и кнопки резервного копирования
        self.status_report_btn = QPushButton("Отчет по Статусам")
        self.master_load_btn = QPushButton("Отчет по Загрузке Мастеров")
        self.master_performance_btn = QPushButton("Отчет: Кто Выполнял Какие Заявки")
        self.backup_btn = QPushButton("Резервное Копирование БД")
        
        report_buttons_layout = QHBoxLayout()
        report_buttons_layout.addWidget(self.status_report_btn)
        report_buttons_layout.addWidget(self.master_load_btn)
        report_buttons_layout.addWidget(self.master_performance_btn)
        report_buttons_layout.addWidget(self.backup_btn)
        report_buttons_layout.addStretch(1)
        
        layout.addLayout(report_buttons_layout)
        
        self.report_output = QTextEdit()
        self.report_output.setReadOnly(True)
        layout.addWidget(self.report_output)
        
        self.status_report_btn.clicked.connect(self.show_status_report)
        self.master_load_btn.clicked.connect(self.show_master_load_report)
        self.master_performance_btn.clicked.connect(self.show_master_performance_report)
        self.backup_btn.clicked.connect(self.perform_backup)
        
        # Применение RBAC к вкладке
        if self.user_info['role'] not in ['Администратор', 'Менеджер']:
            self.tabs.setTabVisible(self.tabs.indexOf(self.reports_tab), False)

    def create_users_tab(self):
        """Создает вкладку для управления пользователями (только для администратора)."""
        self.users_tab = QWidget()
        self.tabs.addTab(self.users_tab, "Пользователи")
        
        layout = QVBoxLayout(self.users_tab)
        
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(5)
        self.users_table.setHorizontalHeaderLabels(["ID", "Логин", "Роль", "ФИО", "Телефон"])
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.users_table)
        
        button_layout = QHBoxLayout()
        self.assign_role_btn = QPushButton("Назначить Роль")
        refresh_users_btn = QPushButton("Обновить")
        
        button_layout.addWidget(self.assign_role_btn)
        button_layout.addWidget(refresh_users_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        self.assign_role_btn.clicked.connect(self.show_assign_role_dialog)
        refresh_users_btn.clicked.connect(self.load_users)
        
        self.load_users()

    def load_users(self):
        """Загружает данные о пользователях из БД и отображает в таблице."""
        users_data = self.tracker.get_all_users()
        
        if users_data is None:
            QMessageBox.critical(
                self, 
                "Ошибка", 
                "Не удалось загрузить данные о пользователях."
            )
            return
        
        self.users_table.setRowCount(len(users_data))
        for row_idx, row_data in enumerate(users_data):
            for col_idx, item in enumerate(row_data):
                self.users_table.setItem(row_idx, col_idx, QTableWidgetItem(str(item)))

    def show_assign_role_dialog(self):
        """Показывает диалог для назначения роли пользователю."""
        selected_row = self.users_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(
                self, 
                "Ошибка выбора", 
                "Пожалуйста, выберите пользователя из таблицы перед назначением роли."
            )
            return
        
        user_id = int(self.users_table.item(selected_row, 0).text())
        current_role = self.users_table.item(selected_row, 2).text()
        user_fio = self.users_table.item(selected_row, 3).text()
        
        if user_id == self.user_info['user_id']:
            QMessageBox.warning(
                self,
                "Невозможно изменить роль",
                "Вы не можете изменить свою собственную роль.\n\n"
                "Обратитесь к другому администратору для изменения вашей роли."
            )
            return
        
        dialog = AssignRoleDialog(self.tracker, user_id, current_role, user_fio, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_users()

    def logout(self):
        """Выход из системы и возврат к диалогу входа."""
        reply = QMessageBox.question(
            self,
            "Выход из системы",
            "Вы уверены, что хотите выйти из системы?\n\nВы сможете войти под другим аккаунтом.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.hide()
            login_dialog = LoginDialog(self.tracker, self)
            if login_dialog.exec() == QDialog.DialogCode.Accepted:
                self.user_info = login_dialog.user_info
                self.setWindowTitle(
                    f"Система Учета Заявок на Ремонт (PyQt6) - "
                    f"Пользователь: {self.user_info['fio']} ({self.user_info['role']})"
                )
                
                if self.user_info['role'] == 'Администратор':
                    if not hasattr(self, 'users_tab'):
                        self.create_users_tab()
                else:
                    if hasattr(self, 'users_tab'):
                        tab_index = self.tabs.indexOf(self.users_tab)
                        if tab_index >= 0:
                            self.tabs.removeTab(tab_index)
                        delattr(self, 'users_tab')
                
                self.apply_rbac_to_requests_tab()
                self.load_requests()
                self.show()
            else:
                QApplication.instance().quit()

    def load_requests(self):
        """Загружает данные о заявках из БД и отображает в таблице, с учетом роли."""
        role = self.user_info['role']
        user_id = self.user_info['user_id']
        
        base_query = """
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
        """
        
        where_clause = ""
        if role == 'Клиент':
            # Клиент видит только свои заявки
            where_clause = f"WHERE r.client_id = {user_id}"
        elif role == 'Мастер':
            # Мастер видит свои заявки и неназначенные заявки
            where_clause = f"WHERE r.master_id = {user_id} OR r.master_id IS NULL"
        
        query = f"{base_query} {where_clause} ORDER BY r.date_created DESC;"
        
        data = self.tracker.db.execute_query(query, fetch_all=True)
        
        if data is None:
            QMessageBox.critical(self, "Ошибка", "Не удалось загрузить данные о заявках.")
            return

        self.requests_table.setRowCount(len(data))
        for row_idx, row_data in enumerate(data):
            for col_idx, item in enumerate(row_data):
                # Форматирование даты
                if col_idx == 6:
                    item = item.strftime("%Y-%m-%d %H:%M") if item else ""
                
                self.requests_table.setItem(row_idx, col_idx, QTableWidgetItem(str(item)))

    def load_clients(self):
        """Загружает данные о клиентах из БД и отображает в таблице."""
        query = "SELECT client_id, full_name, phone_number FROM clients ORDER BY full_name;"
        data = self.tracker.db.execute_query(query, fetch_all=True)
        
        if data is None:
            QMessageBox.critical(self, "Ошибка", "Не удалось загрузить данные о клиентах.")
            return

        self.clients_table.setRowCount(len(data))
        for row_idx, row_data in enumerate(data):
            for col_idx, item in enumerate(row_data):
                self.clients_table.setItem(row_idx, col_idx, QTableWidgetItem(str(item)))

    def load_masters(self):
        """Загружает данные о мастерах из БД и отображает в таблице."""
        query = "SELECT master_id, full_name FROM masters ORDER BY full_name;"
        data = self.tracker.db.execute_query(query, fetch_all=True)
        
        if data is None:
            QMessageBox.critical(self, "Ошибка", "Не удалось загрузить данные о мастерах.")
            return

        self.masters_table.setRowCount(len(data))
        for row_idx, row_data in enumerate(data):
            for col_idx, item in enumerate(row_data):
                self.masters_table.setItem(row_idx, col_idx, QTableWidgetItem(str(item)))

    def show_add_request_dialog(self):
        """Показывает диалог для добавления новой заявки."""
        role = self.user_info['role']
        if role not in ['Администратор', 'Менеджер', 'Оператор', 'Клиент']:
            QMessageBox.warning(self, "Доступ Запрещен", "У вас нет прав для добавления заявок.")
            return
            
        dialog = AddRequestDialog(self.tracker, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_requests() # Обновить таблицу после успешного добавления

    def show_assign_master_dialog(self):
        """Показывает диалог для назначения мастера на заявку."""
        role = self.user_info['role']
        if role not in ['Администратор', 'Менеджер', 'Оператор']:
            QMessageBox.warning(
                self, 
                "Доступ запрещен", 
                "Только Администратор, Менеджеры и Операторы могут назначать мастеров."
            )
            return
        
        selected_row = self.requests_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(
                self, 
                "Ошибка выбора", 
                "Пожалуйста, выберите заявку из таблицы перед назначением мастера."
            )
            return
        
        request_id = int(self.requests_table.item(selected_row, 0).text())
        
        request_info = self.tracker.get_request_status_info(request_id)
        if not request_info:
            QMessageBox.critical(
                self, 
                "Ошибка", 
                f"Не удалось загрузить информацию о заявке №{request_id}.\n"
                "Заявка может быть удалена или недоступна."
            )
            return
        
        status_name = request_info['status_name']
        master_id = request_info['master_id']
        
        if master_id is not None and status_name == 'В работе':
            master_name_query = "SELECT full_name FROM masters WHERE master_id = %s;"
            master_result = self.tracker.db.execute_query(master_name_query, (master_id,), fetch_one=True)
            master_name = master_result[0] if master_result else "Неизвестный"
            
            reply = QMessageBox.question(
                self,
                "Мастер уже назначен",
                f"На заявку №{request_id} уже назначен мастер: {master_name}.\n\n"
                "Вы хотите изменить назначение мастера?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        if status_name in ['Выполнена', 'Отменена']:
            QMessageBox.warning(
                self, 
                "Невозможно назначить мастера", 
                f"Ошибка: Нельзя назначить мастера на заявку со статусом '{status_name}'.\n\n"
                f"Заявка №{request_id} уже завершена или отменена.\n\n"
                "Для назначения мастера заявка должна иметь статус:\n"
                "- 'Новая'\n"
                "- 'В работе'\n\n"
                "Если вы хотите изменить статус заявки, используйте кнопку 'Изменить Статус'."
            )
            return
        
        if status_name not in ['Новая', 'В работе']:
            QMessageBox.warning(
                self, 
                "Невозможно назначить мастера", 
                f"Ошибка: Нельзя назначить мастера на заявку со статусом '{status_name}'.\n\n"
                f"Текущий статус заявки №{request_id}: '{status_name}'.\n\n"
                "Для назначения мастера заявка должна иметь статус 'Новая' или 'В работе'.\n"
                "Если вы хотите изменить статус заявки, используйте кнопку 'Изменить Статус'."
            )
            return
        
        dialog = AssignMasterDialog(self.tracker, request_id, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_requests()

    def show_complete_request_dialog(self):
        """Показывает диалог для завершения заявки."""
        role = self.user_info['role']
        if role not in ['Администратор', 'Менеджер', 'Мастер']:
            QMessageBox.warning(
                self, 
                "Доступ запрещен", 
                "Только Администратор, Менеджеры и Мастера могут завершать заявки."
            )
            return
        
        selected_row = self.requests_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(
                self, 
                "Ошибка выбора", 
                "Пожалуйста, выберите заявку из таблицы перед завершением."
            )
            return
        
        request_id = int(self.requests_table.item(selected_row, 0).text())
        
        request_info = self.tracker.get_request_status_info(request_id)
        if not request_info:
            QMessageBox.critical(
                self, 
                "Ошибка", 
                f"Не удалось загрузить информацию о заявке №{request_id}.\n"
                "Заявка может быть удалена или недоступна."
            )
            return
        
        status_name = request_info['status_name']
        master_id = request_info['master_id']
        
        if status_name == 'Выполнена':
            QMessageBox.warning(
                self, 
                "Заявка уже завершена", 
                f"Заявка №{request_id} уже имеет статус 'Выполнена'.\n\n"
                "Нельзя повторно завершить уже завершенную заявку."
            )
            return
        
        if role == 'Мастер' and master_id != self.user_info['user_id']:
            QMessageBox.warning(
                self, 
                "Доступ запрещен", 
                f"Вы можете завершать только свои заявки.\n\n"
                f"Заявка №{request_id} назначена другому мастеру."
            )
            return
        
        if master_id is None:
            QMessageBox.warning(
                self, 
                "Невозможно завершить заявку", 
                f"Нельзя завершить заявку №{request_id}, так как на неё не назначен мастер.\n\n"
                "Сначала назначьте мастера на заявку, затем завершите её."
            )
            return
        
        dialog = CompleteRequestDialog(self.tracker, request_id, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_requests()

    def show_qr_code_dialog(self):
        """Показывает диалог с QR-кодом для выбранной заявки."""
        selected_row = self.requests_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите заявку из таблицы.")
            return
        
        request_id = int(self.requests_table.item(selected_row, 0).text())
        
        dialog = QRCodeDialog(self.tracker, request_id, self)
        dialog.exec()

    def show_edit_description_dialog(self):
        """Показывает диалог для изменения описания заявки."""
        role = self.user_info['role']
        if role not in ['Администратор', 'Оператор']:
            QMessageBox.warning(
                self, 
                "Доступ запрещен", 
                "Только Администратор и Оператор могут изменять описание заявки."
            )
            return
        
        selected_row = self.requests_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(
                self, 
                "Ошибка выбора", 
                "Пожалуйста, выберите заявку из таблицы перед изменением описания."
            )
            return
        
        request_id = int(self.requests_table.item(selected_row, 0).text())
        
        request_info = self.tracker.get_request_status_info(request_id)
        if not request_info:
            QMessageBox.critical(
                self, 
                "Ошибка", 
                f"Не удалось загрузить информацию о заявке №{request_id}.\n"
                "Заявка может быть удалена или недоступна."
            )
            return
        
        status_name = request_info['status_name']
        
        if status_name in ['Выполнена', 'Отменена']:
            QMessageBox.warning(
                self,
                "Невозможно изменить описание",
                f"Ошибка: Нельзя изменить описание заявки со статусом '{status_name}'.\n\n"
                f"Заявка №{request_id} уже завершена или отменена.\n\n"
                "Описание можно изменять только для заявок в статусах:\n"
                "- 'Новая'\n"
                "- 'В работе'"
            )
            return
        
        current_description = self.requests_table.item(selected_row, 3).text()
        
        dialog = EditDescriptionDialog(self.tracker, request_id, current_description, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_requests()

    def show_change_status_dialog(self):
        """Показывает диалог для изменения статуса заявки."""
        role = self.user_info['role']
        if role not in ['Администратор', 'Оператор']:
            QMessageBox.warning(
                self, 
                "Доступ запрещен", 
                "Только Администратор и Оператор могут изменять статус заявки."
            )
            return
        
        selected_row = self.requests_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(
                self, 
                "Ошибка выбора", 
                "Пожалуйста, выберите заявку из таблицы перед изменением статуса."
            )
            return
        
        request_id = int(self.requests_table.item(selected_row, 0).text())
        
        request_info = self.tracker.get_request_status_info(request_id)
        if not request_info:
            QMessageBox.critical(
                self, 
                "Ошибка", 
                f"Не удалось загрузить информацию о заявке №{request_id}.\n"
                "Заявка может быть удалена или недоступна."
            )
            return
        
        current_status_id = request_info['status_id']
        current_status_name = request_info['status_name']
        
        if current_status_name == 'Выполнена':
            QMessageBox.warning(
                self,
                "Невозможно изменить статус",
                f"Ошибка: Заявка №{request_id} уже имеет статус 'Выполнена'.\n\n"
                "Нельзя изменять статус выполненной заявки.\n\n"
                "Если заявка была завершена по ошибке, обратитесь к администратору."
            )
            return
        
        if current_status_name == 'Отменена':
            QMessageBox.warning(
                self,
                "Невозможно изменить статус",
                f"Ошибка: Заявка №{request_id} имеет статус 'Отменена'.\n\n"
                "Нельзя изменять статус отмененной заявки.\n\n"
                "Если заявка была отменена по ошибке, обратитесь к администратору."
            )
            return
        
        dialog = ChangeStatusDialog(self.tracker, request_id, current_status_id, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_requests()

    def show_respond_to_request_dialog(self):
        """Показывает диалог для мастера, чтобы откликнуться на нераспределенную заявку."""
        role = self.user_info['role']
        if role != 'Мастер':
            QMessageBox.warning(self, "Доступ Запрещен", "Только Мастер может откликаться на заявки.")
            return
        
        selected_row = self.requests_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите заявку из таблицы.")
            return
        
        request_id = int(self.requests_table.item(selected_row, 0).text())
        
        # Проверяем, что заявка не назначена
        query = "SELECT master_id FROM requests WHERE request_id = %s;"
        result = self.tracker.db.execute_query(query, (request_id,), fetch_one=True)
        if not result:
            QMessageBox.critical(self, "Ошибка", "Не удалось загрузить данные заявки.")
            return
        
        if result[0] is not None:
            QMessageBox.warning(self, "Ошибка", "Эта заявка уже назначена мастеру.")
            return
        
        # Получаем ID мастера из user_id
        master_id = self.user_info['user_id']
        
        # Подтверждение
        reply = QMessageBox.question(
            self, 
            "Подтверждение", 
            f"Вы хотите откликнуться на заявку №{request_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.tracker.master_respond_to_request(request_id, master_id):
                QMessageBox.information(self, "Успех", f"Вы успешно откликнулись на заявку №{request_id}.")
                self.load_requests()
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось откликнуться на заявку.")

    def calculate_avg_time(self):
        """Вызывает метод расчета среднего времени и отображает результат."""
        if self.user_info['role'] not in ['Администратор', 'Менеджер']:
            QMessageBox.warning(self, "Доступ Запрещен", "Только Администратор и Менеджер могут просматривать отчеты.")
            return
            
        try:
            avg_time, count = self.tracker.calculate_average_repair_time()
            
            if count == 0:
                result_text = "Нет завершенных заявок для расчета."
            else:
                result_text = f"Среднее время: {avg_time:.2f} часов (по {count} заявкам)"
            
            self.avg_time_result_label.setText(result_text)
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка Расчета", f"Произошла ошибка при расчете: {e}")

    def show_status_report(self):
        """Отображает отчет по статусам заявок."""
        if self.user_info['role'] not in ['Администратор', 'Менеджер']:
            QMessageBox.warning(self, "Доступ Запрещен", "Только Администратор и Менеджер могут просматривать отчеты.")
            return
            
        report_data = self.tracker.get_status_report()
        output = "--- Отчет по Статусам Заявок ---\n"
        if report_data:
            for status, count in report_data:
                output += f"{status}: {count}\n"
        else:
            output += "Нет данных для отчета."
        self.report_output.setText(output)

    def show_master_load_report(self):
        """Отображает отчет по загрузке мастеров."""
        if self.user_info['role'] not in ['Администратор', 'Менеджер']:
            QMessageBox.warning(self, "Доступ Запрещен", "Только Администратор и Менеджер могут просматривать отчеты.")
            return
            
        report_data = self.tracker.get_master_load_report()
        output = "--- Отчет по Загрузке Мастеров ---\n"
        if report_data:
            for master, count in report_data:
                output += f"{master}: {count} заявок\n"
        else:
            output += "Нет данных для отчета."
        self.report_output.setText(output)
    
    def show_master_performance_report(self):
        """Отображает отчет для менеджера: кто выполнял какие заявки."""
        if self.user_info['role'] not in ['Администратор', 'Менеджер']:
            QMessageBox.warning(self, "Доступ Запрещен", "Только Администратор и Менеджер могут просматривать этот отчет.")
            return
            
        report_data = self.tracker.get_master_performance_report()
        output = "--- Отчет: Кто Выполнял Какие Заявки ---\n\n"
        if report_data:
            current_master = None
            for row in report_data:
                master_name, request_id, client_name, equipment, status_name, date_created, date_start_work, date_completed, cost = row
                
                if master_name != current_master:
                    if current_master is not None:
                        output += "\n"
                    output += f"Мастер: {master_name}\n"
                    output += "-" * 60 + "\n"
                    current_master = master_name
                
                output += f"  Заявка №{request_id}: {equipment}\n"
                output += f"    Клиент: {client_name}\n"
                output += f"    Статус: {status_name}\n"
                if date_created:
                    output += f"    Создана: {date_created.strftime('%Y-%m-%d %H:%M') if hasattr(date_created, 'strftime') else date_created}\n"
                if date_start_work:
                    output += f"    Начало работы: {date_start_work.strftime('%Y-%m-%d %H:%M') if hasattr(date_start_work, 'strftime') else date_start_work}\n"
                if date_completed:
                    output += f"    Завершена: {date_completed.strftime('%Y-%m-%d %H:%M') if hasattr(date_completed, 'strftime') else date_completed}\n"
                if cost:
                    output += f"    Стоимость: {cost} руб.\n"
                output += "\n"
        else:
            output += "Нет данных для отчета."
        self.report_output.setText(output)

    def perform_backup(self):
        """Выполняет резервное копирование базы данных."""
        if self.user_info['role'] != 'Администратор':
            QMessageBox.warning(self, "Доступ Запрещен", "Только Администратор может выполнять резервное копирование.")
            return

        # Запрос имени файла у пользователя
        filename, ok = QInputDialog.getText(
            self, 
            "Резервное Копирование", 
            "Введите имя файла для сохранения:", 
            text="backup.sql"
        )
        
        if ok and filename:
            QMessageBox.information(self, "Резервное Копирование", "Начато резервное копирование. Это может занять некоторое время.")
            
            if self.tracker.db.backup_database(filename):
                QMessageBox.information(self, "Успех", f"Резервное копирование успешно завершено. Файл: {filename}")
            else:
                QMessageBox.critical(self, "Ошибка", "Резервное копирование не удалось. Проверьте консоль на наличие ошибок pg_dump.")


def main():
    # Инициализация DBManager (используйте свои реальные параметры)
    db_manager = DBManager(
        dbname="repair_tracker_db", 
        user="postgres", 
        password="p4v17102006", 
        host="localhost"
    )
    
    app = QApplication(sys.argv)
    
    if not db_manager.conn:
        # Если подключение не удалось, показываем ошибку и выходим
        error_box = QMessageBox()
        error_box.setIcon(QMessageBox.Icon.Critical)
        error_box.setWindowTitle("Ошибка Подключения")
        error_box.setText("Не удалось подключиться к базе данных.")
        error_box.setInformativeText("Проверьте настройки и запуск PostgreSQL.")
        error_box.exec()
        sys.exit(1)

    tracker = RepairTracker(db_manager)
    
    # Показываем окно входа
    login_dialog = LoginDialog(tracker)
    if login_dialog.exec() != QDialog.DialogCode.Accepted:
        sys.exit(0) # Выход, если вход не удался или отменен
        
    user_info = login_dialog.user_info
    
    window = MainWindow(tracker, user_info)
    window.show()
    
    # Запуск приложения
    exit_code = app.exec()
    
    # Закрытие соединения при выходе
    db_manager.close()
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
