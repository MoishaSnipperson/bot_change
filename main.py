#!/usr/bin/python3
#Тут файл с курсами
#https://cdn.cur.su/api/latest.json


import telebot
import os.path
import time
import urllib.request
import json
import sqlite3
import math

#Хэлп шаблон
help_text = """
Помощь 
    /start - Топ курсов к рублю
    
    /help - помощь
    
    /cou Страна 
    Курс страны к рублю
    (Пример /cou Малазия) 
    Курс Рубля к Ринггит
    
    /con сумма КОД_Валюты_1 Код_валюты_2
    (Пример /change 100 UAH BYN)
    Переводим 100 Гривен в Белоруский Зайчик
    
    /but - Кнопки по частям света
    (Если не знаем обозначение валюты то
    выбираем часть света и страну,
    автоматически будет 
    конвертиться в рубль)
    """

#Топ шаблон
top = """               
           
    Топ курсов Валют       
          |------------------------
          | 🇺🇸 1 USD - 🇷🇺 {:.2f} RUB 
          |------------------------
          | 🇪🇺 1 EUR - 🇷🇺 {:.2f} RUB 
          |-------------------------  
          | 🇧🇾 1 BYN - 🇷🇺 {:.2f} RUB
          |-------------------------
          | 🇺🇦 1 UAH - 🇷🇺 {:.2f} RUB   
          |-------------------------- 
          | 🇵🇱 1 PLN - 🇷🇺 {:.2f} RUB  
          |--------------------------
          | /help - Помощь
          +--------------------------
        """

#Шаблон конвертора
country_text = """
Курс страны
    Курс валюты -> {} 
    Cтрана -> {}
    Название -> {}
        1 {} -> {:.2f} RUB   
            {}
    /help - Помощь
    """

#Шаблон конвертора
convert_text = """
Конвертор
    {:.2f} {} -> {:.2f} {}
    /help - Помощь
    """

bot = telebot.TeleBot("Bot_key")
#Файл бд с курсами
DB_FILE = 'latest.json'
#12 часов в сек
TIME_CHANGE = 10800
#Url caйта где берем курсы
URL_MOMEY =  'https://cdn.cur.su/api/latest.json'
#Словарь 
super_kurs = {}

#Функция загрузки jon файла
def download_db(url, path):
    with urllib.request.urlopen(url) as url1:
        data = json.loads(url1.read().decode())
        with open(path, 'w') as outfile:
            json.dump(data, outfile)

#Функция проверки даты и времени и скачки файла
def file_change(MONEY, PATH):
    #Проверка на нахождения файла
    if os.path.exists(PATH):
        #Время файла + 3 часов (в сек)
        file_time = os.path.getmtime(PATH) + TIME_CHANGE
        #Проверка времени, если время создания файла + 3ч < текущего времени то
        if int(file_time) < int(time.time()):
            #Скачиваем по времени
            download_db(MONEY, PATH)
    else: 
        #Если файлов нет
        download_db(MONEY, PATH)
    #Проверка на существование файла
    with open(DB_FILE) as f:
        #Загружаем файл
        file_content = f.read()
        templates = json.loads(file_content)
        #Глобальная переменный с курсом
        global super_kurs
        super_kurs = templates

#Кросс-Курс через доллар
def cross(val_in, val_to):
    val_in_usd = super_kurs['rates'][val_in]
    val_to_usd = super_kurs['rates'][val_to]
    return val_in_usd / val_to_usd

#Help
@bot.message_handler(commands=['help'])
def send_welcome(message):
    msg = bot.send_message(message.chat.id, help_text)

#Топ валют
@bot.message_handler(commands=['start'])
def start_message(message):
    file_change(URL_MOMEY, DB_FILE)
    #Выводим топ курсов
    bot.send_message(message.chat.id, top.format(super_kurs['rates']['RUB'], cross("RUB", "EUR"), cross("RUB", "BYN") , cross("RUB", "UAH"), cross("RUB", "PLN")))

#Кнопки по частям света
@bot.message_handler(commands=['but'])
def get_buttons(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=6)
    itembtn1 = telebot.types.KeyboardButton('Азия')
    itembtn2 = telebot.types.KeyboardButton('Африка')
    itembtn3 = telebot.types.KeyboardButton('Европа')
    itembtn4 = telebot.types.KeyboardButton('Океания')
    itembtn5 = telebot.types.KeyboardButton('Севамерика')
    itembtn6 = telebot.types.KeyboardButton('Южамерика')
    markup.add(itembtn1, itembtn2, itembtn3, itembtn4, itembtn5, itembtn6)
    bot.send_message(message.chat.id, "Выбери континент", reply_markup=markup)

#Тут краткие команды
@bot.message_handler(content_types=["text"])
def repeat_all_messages(message):
    
    #Делим команды по пробелу 
    text_command = message.text.split(' ')
    
    #Начинается с /cou поиск по стране
    if text_command[0] == "/cou":
        #Длинна больше 1
        if  1 < len(text_command):
            #В нижний регистр
            cou = text_command[1].lower();
            #Если буквы
            if cou.isalpha():
                #Конект к бд
                conn = sqlite3.connect('database.db')
                cur = conn.cursor()
                cur.execute("SELECT code, country, name, wiki FROM main where country = '" + cou + "';")
        
                rows = cur.fetchall()
                if 0 < len(rows): 
                    for i in rows:
                        bot.send_message(message.chat.id, country_text.format(i[0], i[1].capitalize() , i[2].capitalize() , i[0], cross("RUB", i[0]), i[3]))
                        conn.close()
                else:
                    bot.send_message(message.chat.id, "Страна не найдена")
                    conn.close()
            else:
                bot.send_message(message.chat.id, "Страна не задана")
                
    #Конвертер одной валюты в другую
    elif text_command[0] == "/con":
        #Проверка на число
        try:
            val = float(text_command[1])
        except ValueError:
            bot.send_message(message.chat.id, "Это не число")
        else:
            code1 = text_command[2].upper()
            code2 = text_command[3].upper()
            if code1 in super_kurs['rates'] and code2 in super_kurs['rates']:
                bot.send_message(message.chat.id, convert_text.format(val, code1, cross(code2, code1) * val, code2))
            else:
                bot.send_message(message.chat.id, "Валюта не найдена")

    #Тут по частям света идет
    elif text_command[0] in ['Азия', 'Америка', 'Африка', 'Европа', 'Океания', 'Севамерика', 'Южамерика']:
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute("SELECT country, code FROM main where world = '" + text_command[0].lower() + "';")
        rows = cur.fetchall()
        for x in rows:
            bot.send_message(message.chat.id, "/cou " + x[0].capitalize() + "; Код валюты " + x[1])
        conn.close()

    else:
        bot.send_message(message.chat.id, "Неверная команда !!!")

#При Старте проверяем сразу свежесть файла и при каждом новом клиенте
file_change(URL_MOMEY, DB_FILE)

bot.polling()