import psycopg2
import xlwt

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import *
from config import *


class Main_Window(QMainWindow):
    def __init__(self):
        super(Main_Window, self).__init__()
        self.resize(1000, 750)
        self.centralwidget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.centralwidget)
        self.setWindowTitle('DocPlusDB')
        self.setWindowIcon(QtGui.QIcon('logo.png'))
        self.centralwidget.setFont(QtGui.QFont("Times", 10))
        self.search_groupe = QtWidgets.QGroupBox('Поиск', self.centralwidget)

        self.btn_clear = QtWidgets.QPushButton(self.search_groupe)
        self.btn_clear.setText("Очистить")
        self.btn_clear.clicked.connect(self.start_clear)
        self.btn_clear.setFixedWidth(100)

        self.btn_search = QtWidgets.QPushButton(self.search_groupe)
        self.btn_search.setText("Поиск")
        self.btn_search.setFixedWidth(100)

        self.btn_save = QtWidgets.QPushButton(self.search_groupe)
        self.btn_save.setText("Сохранить")
        self.btn_save.setEnabled(False)
        self.btn_save.setFixedWidth(100)
        self.btn_save.clicked.connect(self.save_table)
        self.btn_search.clicked.connect(self.start_search)

        self.table = QtWidgets.QTableWidget(self.search_groupe)
        self.table.setMinimumHeight(150)
        self.table.sortByColumn(2, QtCore.Qt.AscendingOrder)
        self.table.itemDoubleClicked.connect(self.equipment_show)

        self.search = QtWidgets.QLineEdit(self.search_groupe)

        self.search_for_what = QtWidgets.QComboBox(self.search_groupe)
        self.search_for_what.setMinimumWidth(110)
        self.search_for_what.addItems(['Всё', 'По Адресу', 'По Оборудованию', 'По Имени'])
        self.search_for_what.currentTextChanged.connect(self.sfw2)

        self.search_for_what2 = QtWidgets.QComboBox(self.search_groupe)
        self.search_for_what2.setMinimumWidth(110)
        self.search_for_what2.currentTextChanged.connect(self.sfw3)

        self.search_for_what3 = QtWidgets.QComboBox(self.search_groupe)
        self.search_for_what3.setMaximumWidth(50)

        self.layout = QGridLayout(self.centralwidget)
        self.layout.addWidget(self.search_groupe, 0, 0)
        self.layout_search = QGridLayout(self.search_groupe)
        self.layout_search.addWidget(self.search_for_what, 0, 0)
        self.layout_search.addWidget(self.search_for_what2, 0, 1)
        self.layout_search.addWidget(self.search_for_what3, 0, 2)
        self.layout_search.addWidget(self.search, 0, 3)
        self.layout_search.addWidget(self.btn_search, 0, 4)
        self.layout_search.addWidget(self.table, 1, 0, 1, 5)
        self.layout_search.addWidget(self.btn_save, 3, 0)
        self.layout_search.addWidget(self.btn_clear, 3, 4)


        #Добавление
        self.add_groupe = QtWidgets.QGroupBox('Добавление', self.centralwidget)
        self.add_groupe.setGeometry(10, 630, 880, 160)

        self.add_lable_address = QtWidgets.QLabel(self.add_groupe)
        self.add_lable_address.setText('Адрес:')

        self.add_CB_address = QtWidgets.QComboBox(self.add_groupe)
        self.add_CB_address.setFixedWidth(300)
        self.add_CB_address.currentTextChanged.connect(self.add_room)

        self.add_lable_room = QtWidgets.QLabel(self.add_groupe)
        self.add_lable_room.setText('Кабинет:')

        self.add_CB_room = QtWidgets.QComboBox(self.add_groupe)
        self.add_CB_room.setFixedWidth(300)

        self.add_lable_type = QtWidgets.QLabel(self.add_groupe)
        self.add_lable_type.setText('Оборудование:')

        self.add_CB_type = QtWidgets.QComboBox(self.add_groupe)
        self.add_CB_type.setFixedWidth(300)
        self.add_CB_type.currentTextChanged.connect(self.sfw2)

        self.add_lable_name = QtWidgets.QLabel(self.add_groupe)
        self.add_lable_name.setText('Наименование:')

        self.add_name = QtWidgets.QLineEdit(self.add_groupe)
        self.add_name.setFixedWidth(300)

        self.add_lable_sn = QtWidgets.QLabel(self.add_groupe)
        self.add_lable_sn.setText('Серийный номер:')

        self.add_sn = QtWidgets.QLineEdit(self.add_groupe)
        self.add_sn.setFixedWidth(300)

        self.add_lable_date = QtWidgets.QLabel(self.add_groupe)
        self.add_lable_date.setText('Год выпуска:')

        self.add_date = QtWidgets.QLineEdit(self.add_groupe)
        self.add_date.setFixedWidth(300)

        self.btn_add = QtWidgets.QPushButton(self.add_groupe)
        self.btn_add.setFixedWidth(100)
        self.btn_add.setText("Добавить")
        self.btn_add.clicked.connect(self.start_add)

        self.btn_add_clear = QtWidgets.QPushButton(self.add_groupe)
        self.btn_add_clear.setFixedWidth(100)
        self.btn_add_clear.setText("Очистить")
        self.btn_add_clear.clicked.connect(self.start_add_clear)

        self.add_groupe.setEnabled(True)
        self.add_groupe.setCheckable(True)

        self.layout.addWidget(self.add_groupe, 1, 0)
        self.layout_add = QGridLayout(self.add_groupe)
        self.layout_add.addWidget(self.add_lable_address, 0, 0, alignment = QtCore.Qt.AlignLeft)
        self.layout_add.addWidget(self.add_CB_address, 1, 0, alignment = QtCore.Qt.AlignLeft)
        self.layout_add.addWidget(self.add_lable_room, 2, 0, alignment = QtCore.Qt.AlignLeft)
        self.layout_add.addWidget(self.add_CB_room, 3, 0, alignment = QtCore.Qt.AlignLeft)
        self.layout_add.addWidget(self.add_lable_type, 4, 0, alignment = QtCore.Qt.AlignLeft)
        self.layout_add.addWidget(self.add_CB_type, 5, 0, alignment = QtCore.Qt.AlignLeft)
        self.layout_add.addWidget(self.add_lable_name, 0, 1, alignment = QtCore.Qt.AlignLeft)
        self.layout_add.addWidget(self.add_name, 1, 1, alignment = QtCore.Qt.AlignLeft)
        self.layout_add.addWidget(self.add_lable_sn, 2, 1, alignment = QtCore.Qt.AlignLeft)
        self.layout_add.addWidget(self.add_sn, 3, 1, alignment = QtCore.Qt.AlignLeft)
        self.layout_add.addWidget(self.add_lable_date, 4, 1, alignment = QtCore.Qt.AlignLeft)
        self.layout_add.addWidget(self.add_date, 5, 1, alignment = QtCore.Qt.AlignLeft)
        self.layout_add.addWidget(self.btn_add, 1, 200, alignment = QtCore.Qt.AlignRight)
        self.layout_add.addWidget(self.btn_add_clear, 5, 200, alignment = QtCore.Qt.AlignRight)

        self.add_all()

    #"""Настройка добавления оборудования"""

    def add_all(self):
            try:
                con = psycopg2.connect(
                    host=host,
                    user=user,
                    password=password,
                    database=db_name
                )
                with con.cursor() as cur:

                    #"""Выбор Улицы"""
                    cur.execute("SELECT street FROM streets")
                    x = cur.fetchall()
                    x = ','.join(map(str, x))
                    for r in (('(', ''), (',)', ''), ("'", '')):
                        x = x.replace(*r)
                    #print(x.split(','))
                    self.add_CB_address.addItems(x.split(','))

                    #"""Выбор Типа"""
                    cur.execute("SELECT type FROM types "
                                "ORDER BY type ASC ")
                    x = cur.fetchall()
                    x = ','.join(map(str, x))
                    for r in (('(', ''), (',)', ''), ("'", '')):
                        x = x.replace(*r)
                    #print(x.split(','))
                    self.add_CB_type.addItems(x.split(','))

                    cur.execute("SELECT DISTINCT name FROM names")
                    x = cur.fetchall()
                    #print(x)
                    x = ','.join(map(str, x))
                    #print(x)
                    for r in (('(', ''), (',)', ''), ("'", '')):
                        x = x.replace(*r)
                    #print(x.split(','))
                    completer = QCompleter(x.split(','))
                    self.add_name.setCompleter(completer)
                    completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)

            except Exception as e:
                error = QMessageBox()
                error.setWindowTitle("Ошибка")
                error.setText("Что-то пошло не так")
                error.setIcon(QMessageBox.Warning)
                error.setStandardButtons(QMessageBox.Ok)
                error.setDetailedText(f'Error {e}')
                print(f'Error {e}')
                error.exec_()
            finally:
                if con:
                    con.close()

    #"""Добавление комнаты, относительно улицы"""
    def add_room(self):
        try:
            con = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            with con.cursor() as cur:
                cur.execute(f"SELECT "
                            f"address.room "
                            f"FROM address "
                            f"INNER JOIN streets ON street_id = streets.id "
                            f"WHERE streets.street = '{str(self.add_CB_address.currentText())}'")
                x = cur.fetchall()
                x = ','.join(map(str, x))
                for r in (('(', ''), (',)', ''), ("'", '')):
                    x = x.replace(*r)
                # print(x.split(','))
                self.add_CB_room.clear()
                self.add_CB_room.addItems(x.split(','))
        except Exception as e:
            error = QMessageBox()
            error.setWindowTitle("Ошибка")
            error.setText("Что-то пошло не так")
            error.setIcon(QMessageBox.Warning)
            error.setStandardButtons(QMessageBox.Ok)
            error.setDetailedText(f'Error {e}')
            print(f'Error {e}')
            error.exec_()
        finally:
            if con:
                con.close()

    #"""Настройки поиска"""
    def sfw2(self):
        try:
            con = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            with con.cursor() as cur:

                #"""Поиск без фильтров"""
                if self.search_for_what.currentText() == 'Всё':
                    self.search.setEnabled(False)
                    self.search_for_what2.setEnabled(False)
                    self.search_for_what3.setEnabled(False)
                    self.search_for_what2.clear()

                #"""Поиск по адресу"""

                elif self.search_for_what.currentText() == 'По Адресу':
                    self.search.setEnabled(False)
                    self.search_for_what2.setEnabled(True)
                    self.search_for_what3.setEnabled(True)
                    self.search_for_what2.clear()
                    cur.execute("SELECT street FROM streets")
                    x = cur.fetchall()
                    #print(x)
                    x = ','.join(map(str, x))
                    #print(x)
                    for r in (('(', ''), (',)', ''), ("'", '')):
                        x = x.replace(*r)
                    #print(x.split(','))
                    self.search_for_what2.addItems(x.split(','))
                    #self.sfw3()

                #"""Поиск по типу"""
                elif self.search_for_what.currentText() == 'По Оборудованию':
                    self.search.setEnabled(False)
                    self.search_for_what2.setEnabled(True)
                    self.search_for_what3.setEnabled(False)
                    self.search_for_what2.clear()
                    cur.execute("SELECT type FROM types")
                    x = cur.fetchall()
                    #print(x)
                    x = ','.join(map(str, x))
                    #print(x)
                    for r in (('(', ''), (',)', ''), ("'", '')):
                        x = x.replace(*r)
                    self.search_for_what2.addItems(x.split(','))

                #"""Поиск по имени"""
                elif self.search_for_what.currentText() == 'По Имени':
                    self.search.setEnabled(True)
                    self.search_for_what2.setEnabled(False)
                    self.search_for_what3.setEnabled(False)
                    cur.execute("SELECT DISTINCT name FROM names")
                    x = cur.fetchall()
                    #print(x)
                    x = ','.join(map(str, x))
                    #print(x)
                    for r in (('(', ''), (',)', ''), ("'", '')):
                        x = x.replace(*r)
                    #print(x.split(','))
                    completer = QCompleter(x.split(','))
                    self.search.setCompleter(completer)
                    completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
                    self.search_for_what2.clear()
        except Exception as e:
            error = QMessageBox()
            error.setWindowTitle("Ошибка")
            error.setText("Что-то пошло не так")
            error.setIcon(QMessageBox.Warning)
            error.setStandardButtons(QMessageBox.Ok)
            error.setDetailedText(f'Error {e}')
            print(f'Error {e}')
            error.exec_()
        finally:
            if con:
                con.close()

    def sfw3(self):
        try:
            con = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            with con.cursor() as cur:
                self.search_for_what3.clear()
                cur.execute(f"SELECT "
                            f"address.room "
                            f"FROM address "
                            f"INNER JOIN streets ON street_id = streets.id "
                            f"WHERE streets.street = '{str(self.search_for_what2.currentText())}'")
                x = cur.fetchall()
                #print(x)
                x = ','.join(map(str, x))
                #print(x)
                for r in (('(', ''), (',)', ''), ("'", '')):
                    x = x.replace(*r)
                #print(x.split(','))
                self.search_for_what3.addItems(x.split(','))
        except Exception as e:
            error = QMessageBox()
            error.setWindowTitle("Ошибка")
            error.setText("Что-то пошло не так")
            error.setIcon(QMessageBox.Warning)
            error.setStandardButtons(QMessageBox.Ok)
            error.setDetailedText(f'Error {e}')
            print(f'Error {e}')
            error.exec_()
        finally:
            if con:
                con.close()

    #"""Очистка таблицы"""
    def start_clear(self):
        self.table.clearContents()

    #"""Кнопка Поиска"""
    def start_search(self):
        try:
            con = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            with con.cursor() as cur:

                #"""Кнопка поиска без фильтров"""
                if self.search_for_what.currentText() == 'Всё':
                    cur.execute(
                        "SELECT equipments.id, streets.street, address.room, types.type, names.name, names.sn, names.date "
                        "FROM equipments "
                        "INNER JOIN address ON address.id = equipments.address_id "
                        "INNER JOIN types ON types.id = equipments.type_id "
                        "INNER JOIN names ON names.id = equipments.name_id "
                        "INNER JOIN streets ON street_id = streets.id;")

                #"""Кнопка поиска по адресу"""
                elif self.search_for_what.currentText() == 'По Адресу':
                    self.table.clearContents()
                    cur.execute(
                        f"SELECT equipments.id, streets.street, address.room, types.type, names.name, names.sn, names.date "
                        f"FROM equipments "
                        f"INNER JOIN address ON address.id = equipments.address_id "
                        f"INNER JOIN types ON types.id = equipments.type_id "
                        f"INNER JOIN names ON names.id = equipments.name_id "
                        f"INNER JOIN streets ON street_id = streets.id "
                        f"WHERE streets.street = '{str(self.search_for_what2.currentText())}' AND address.room = '{str(self.search_for_what3.currentText())}'")

                #"""Кнопка поиска по типу"""
                elif self.search_for_what.currentText() == 'По Оборудованию':
                    self.table.clearContents()
                    cur.execute(
                        f"SELECT equipments.id, streets.street, address.room, types.type, names.name, names.sn, names.date "
                        f"FROM equipments "
                        f"INNER JOIN address ON address.id = equipments.address_id "
                        f"INNER JOIN types ON types.id = equipments.type_id "
                        f"INNER JOIN names ON names.id = equipments.name_id "
                        f"INNER JOIN streets ON street_id = streets.id "
                        f"WHERE types.type = '{str(self.search_for_what2.currentText())}'")

                #"""Кнопка поиска по имени"""
                elif self.search_for_what.currentText() == 'По Имени':
                    cur.execute(
                        f"SELECT equipments.id, streets.street, address.room, types.type, names.name, names.sn, names.date "
                        f"FROM equipments "
                        f"INNER JOIN address ON address.id = equipments.address_id "
                        f"INNER JOIN types ON types.id = equipments.type_id "
                        f"INNER JOIN names ON names.id = equipments.name_id "
                        f"INNER JOIN streets ON street_id = streets.id "
                        f"WHERE to_tsvector(name) @@ plainto_tsquery('{str(self.search.text())}')"
                    )
                data = cur.fetchall()
                a = len(data)  # rows
                b = len(data[0])  # columns
                #print(data, data[0])
                self.table.setColumnCount(b)
                self.table.setRowCount(a)
                self.table.setSortingEnabled(False)
                for j in range(a):
                    for i in range(b):
                        item = QtWidgets.QTableWidgetItem(str(data[j][i]))
                        self.table.setItem(j, i, item)
                self.table.setHorizontalHeaderLabels(
                        ['id', 'Адрес', 'Кабинет', 'Оборудование', 'Наименование', 'С/Н', 'Год выпуска'])
                self.table.setSortingEnabled(True)
                self.table.sortByColumn(2, QtCore.Qt.AscendingOrder)

                self.table.resizeColumnsToContents()
                self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
                self.btn_save.setEnabled(True)

        except Exception as e:
            error = QMessageBox()
            error.setWindowTitle("Ошибка")
            error.setText("Что-то пошло не так")
            error.setIcon(QMessageBox.Warning)
            error.setStandardButtons(QMessageBox.Ok)
            error.setDetailedText(f'Error {e}')
            print(f'Error {e}')
            error.exec_()
        finally:
            if con:
                con.close()

    #"""Кнопка добавления"""
    def start_add(self):
        try:
            con = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            with con.cursor() as cur:


                #"""ID Улицы"""
                cur.execute(
                    f"SELECT id "
                    f"FROM streets "
                    f"WHERE street = '{str(self.add_CB_address.currentText())}'"
                )
                id_street = cur.fetchall()
                id_street = ','.join(map(str, id_street))
                for r in (('(', ''), (',)', '')):
                    id_street = id_street.replace(*r)
                #print(f"Улица_id: {id_street}")


                #"""ID Адресса"""
                cur.execute(
                    f"SELECT id "
                    f"FROM address "
                    f"WHERE room = '{str(self.add_CB_room.currentText())}' AND street_id = '{id_street}'"
                )
                id_address = cur.fetchall()
                id_address = ','.join(map(str, id_address))
                for r in (('(', ''), (',)', '')):
                    id_address = id_address.replace(*r)
                print(f"Комната_id: {id_address}")



                #"""ID Типа оборудования"""
                cur.execute(
                    f"SELECT id "
                    f"FROM types "
                    f"WHERE type = '{str(self.add_CB_type.currentText())}'"
                )
                id_type = cur.fetchall()
                id_type = ','.join(map(str, id_type))
                for r in (('(', ''), (',)', '')):
                    id_type = id_type.replace(*r)
                print(f"Тип_id: {id_type}")

                cur.execute(
                    f"INSERT INTO names ( "
                    f"id, name, sn, date) "
                    f"VALUES (DEFAULT, '{str(self.add_name.text())}', '{str(self.add_sn.text())}', '{str(self.add_date.text())}')"
                )

                con.commit()
                print('Данные добавленны в names')

                cur.execute(
                    "SELECT DISTINCT ON (id) id "
                    "FROM names "
                    "ORDER BY id DESC"
                )
                id_name = cur.fetchall()
                id_name = str(id_name[0])
                #print(str(x[0]))
                for r in (('(', ''), (',)', '')):
                    id_name = id_name.replace(*r)
                print(f"Имя_id: {id_name}")

                add_message = QMessageBox()
                add_message.setWindowTitle("Добавление в базу")
                add_message.setText("Добавить в базу данных?")
                add_message.setIcon(QMessageBox.Question)
                add_message.setStandardButtons(QMessageBox.Cancel|QMessageBox.Ok)
                add_message.exec_()
                if add_message.Ok:
                    """Добавление в базу"""
                    cur.execute(
                        f"INSERT INTO equipments ( "
                        f"id, address_id, type_id, name_id) "
                        f"VALUES (DEFAULT, '{id_address}', '{id_type}', '{id_name}')"
                    )
                    con.commit()
                    print('УСПЕШНО ДОБАВЛЕННО В БАЗУ!')
                    add_message = QMessageBox()
                    add_message.setWindowTitle("Успешно")
                    add_message.setText("Оборудование добавленно в базу")
                    add_message.setIcon(QMessageBox.Information)
                    add_message.setStandardButtons(QMessageBox.Ok)
                    add_message.exec_()

        except Exception as e:
            error = QMessageBox()
            error.setWindowTitle("Ошибка")
            error.setText("Что-то пошло не так")
            error.setIcon(QMessageBox.Warning)
            error.setStandardButtons(QMessageBox.Ok)
            error.setDetailedText(f'Error {e}')
            print(f'Error {e}')
            error.exec_()
        finally:
            if con:
                con.close()

    def start_add_clear(self):
        self.add_name.clear()
        self.add_sn.clear()
        self.add_date.clear()

    #"""Кнопка сохранения"""
    def save_table(self):
        rows = self.table.rowCount()
        cols = self.table.columnCount()
        heads = ['id', 'Адрес', 'Кабинет', 'Оборудование', 'Наименование', 'С/Н', 'Год выпуска']
        name, _ = QFileDialog.getSaveFileName(self, 'Сохранить', '.', 'Excel(*.xls)')
        if not name:
            error = QMessageBox.information(self, 'Внимание!', 'Укажите имя файла')
            return
        wb = xlwt.Workbook()
        ws = wb.add_sheet('Список оборудования')
        for colx in range(cols):
            width = 3000 + colx * 500
            ws.col(colx).width = width
        data = []
        for row in range(rows):
            items = []
            for col in range(cols):
                    items.append(self.table.item(row, col).text())
            data.append(items)
        j = 0
        for n in heads:
            ws.write(0, j, n)
            j += 1
        i = 1
        for n in data:
            ws.write(i, 0, n[0])
            ws.write(i, 1, n[1])
            ws.write(i, 2, n[2])
            ws.write(i, 3, n[3])
            ws.write(i, 4, n[4])
            ws.write(i, 5, n[5])
            ws.write(i, 6, n[6])
            i += 1
        wb.save(name)

    #"""Показать Данные оборудовани"""
    def equipment_show(self):

        row = self.table.currentIndex().row()
        global index
        index = self.table.model().index(row, 0).data()
        print(index)
        self.equipment_window = Equipment_Window()
        self.equipment_window.show()



class Equipment_Window(QtWidgets.QWidget):
    def __init__(self):
        super(Equipment_Window, self).__init__()
        self.resize(700, 450)
        self.centralwidget = QtWidgets.QWidget(self)
        self.setWindowTitle('Данные')
        self.setWindowIcon(QtGui.QIcon('logo.png'))
        self.centralwidget.setFont(QtGui.QFont("Times", 10))
        self.layout = QGridLayout(self.centralwidget)
        self.lable_address = QtWidgets.QLabel(self.centralwidget)
        self.lable_room = QtWidgets.QLabel(self.centralwidget)
        self.lable_type = QtWidgets.QLabel(self.centralwidget)
        self.lable_name = QtWidgets.QLabel(self.centralwidget)
        self.lable_sn = QtWidgets.QLabel(self.centralwidget)
        self.lable_date = QtWidgets.QLabel(self.centralwidget)
        self.table = QtWidgets.QTableWidget(self.centralwidget)

        self.btn_change = QtWidgets.QPushButton(self.centralwidget)
        self.btn_change.setText("Изменить")
        self.btn_change.setEnabled(False)
        self.btn_add = QtWidgets.QPushButton(self.centralwidget)
        self.btn_add.setText("Добавить запись")
        self.btn_add.setEnabled(False)
        self.layout.addWidget(self.btn_change, 0, 3)
        self.layout.addWidget(self.btn_add, 2, 3)
        self.layout.addWidget(self.table, 3, 0, 3, 4)
        self.table.setMinimumHeight(50)
        try:
            con = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name
            )
            with con.cursor() as cur:

                #"""Кнопка поиска без фильтров"""
                cur.execute(
                    "SELECT streets.street "
                    "FROM equipments "
                    "INNER JOIN address ON address.id = equipments.address_id "
                    "INNER JOIN streets ON street_id = streets.id "
                    f"WHERE equipments.id = '{str(index)}'"
                )
                address = cur.fetchall()
                address = ','.join(map(str, address))
                for r in (('(', ''), (',)', ''), ("'", '')):
                    address = str(address.replace(*r))
                #print(address)
                self.lable_address.setText(f"Адрес: {str(address)}")
                self.layout.addWidget(self.lable_address, 0, 0)

                cur.execute(
                    "SELECT address.room "
                    "FROM equipments "
                    "INNER JOIN address ON address.id = equipments.address_id "
                    f"WHERE equipments.id = '{str(index)}'"
                )
                room = cur.fetchall()
                room = ','.join(map(str, room))
                for r in (('(', ''), (',)', ''), ("'", '')):
                    room = str(room.replace(*r))
                #print(room)

                self.lable_room.setText(f"Кабинет: {str(room)}")
                self.layout.addWidget(self.lable_room, 1, 0)

                cur.execute(
                    "SELECT types.type "
                    "FROM equipments "
                    "INNER JOIN types ON types.id = equipments.type_id "
                    f"WHERE equipments.id = '{str(index)}'"
                )
                type = cur.fetchall()
                type = ','.join(map(str, type))
                for r in (('(', ''), (',)', ''), ("'", '')):
                    type = str(type.replace(*r))
                #print(type)
                self.lable_type.setText(f"Оборудование: {str(type)}")
                self.layout.addWidget(self.lable_type, 2, 0)

                cur.execute(
                    "SELECT names.name "
                    "FROM equipments "
                    "INNER JOIN names ON names.id = equipments.type_id "
                    f"WHERE equipments.id = '{str(index)}'"
                )
                name = cur.fetchall()
                name = ','.join(map(str, name))
                for r in (('(', ''), (',)', ''), ("'", '')):
                    name = str(name.replace(*r))
                #print(name)
                self.lable_name.setText(f"Наименование: {str(name)}")
                self.layout.addWidget(self.lable_name, 0, 1)

                cur.execute(
                    "SELECT names.sn "
                    "FROM equipments "
                    "INNER JOIN names ON names.id = equipments.type_id "
                    f"WHERE equipments.id = '{str(index)}'"
                )
                sn = cur.fetchall()
                sn = ','.join(map(str, sn))
                for r in (('(', ''), (',)', ''), ("'", '')):
                    sn = str(sn.replace(*r))
                #print(sn)
                self.lable_sn.setText(f"Серийный номер: {str(sn)}")
                self.layout.addWidget(self.lable_sn, 1, 1)

                cur.execute(
                    "SELECT names.date "
                    "FROM equipments "
                    "INNER JOIN names ON names.id = equipments.type_id "
                    f"WHERE equipments.id = '{str(index)}'"
                )
                date = cur.fetchall()
                #print(date)
                date = ','.join(map(str, date))
                for r in (("(Decimal('", ''), ("'),)", '')):
                    date = str(date.replace(*r))
                print(date)
                self.lable_date.setText(f"Год выпуска: {str(date)}")
                self.layout.addWidget(self.lable_date, 2, 1)

        except Exception as e:
            error = QMessageBox()
            error.setWindowTitle("Ошибка")
            error.setText("Что-то пошло не так")
            error.setIcon(QMessageBox.Warning)
            error.setStandardButtons(QMessageBox.Ok)
            error.setDetailedText(f'Error {e}')
            print(f'Error {e}')
            error.exec_()
        finally:
            pass


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    main_window = Main_Window()
    main_window.show()
    sys.exit(app.exec_())



