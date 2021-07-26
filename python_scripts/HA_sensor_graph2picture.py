'''
Обращение к НА с помощью rest api Home Assistant для запроса истории датчика
за указанное количество часов, построение графика и сохранение его в файл картинки PNG

ToDo:
1. перенести number_of_hours и entity_id в НА и передавать в виде аргументов в скрипт
2. добавить сглаживание графика?
3. разобраться почему ошибка на первом элементе
4.

'''




# подключаем библиотеки/модули 
import json                                 # Модуль JSON
from requests import get                    # get requesrs
from datetime import datetime, timedelta
import numpy as np                          # библиотека NumPy это open-source модуль для python, который предоставляет общие математические и числовые операции в виде пре-скомпилированных, быстрых функций
import matplotlib                           # Библиотека на языке программирования Python для визуализации данных двумерной (2D) графикой.
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker          # модуль управления тиками
from matplotlib.ticker import FormatStrFormatter
from matplotlib.dates import DateFormatter
from pytz import timezone
import os

# переменные
temp = None                         # строка для временного хранения данных
url = None                          # url ссылка
filter_date_time = None             # время до которого будем запрашивать данные
kol_all = 0                         # количество обработанных значений
skip_flag = 0                       # флаг пропуска элемента массива

number_of_hours = 24                                # количество часов которые будем запрашивать
entity_id = "sensor.th2_temperature"                # сенсор

# API ключ (Long-Lived Access Token) НА и адрес сервера
api_key = "ABCDEFGH"
address_hass = "192.168.0.2"





##########################################################

#print ("\nStart program\n")

# сменим рабочую папку на ту в которую нужно сохранять картинку
#path="/home/homeassistant/.homeassistant/www"
path="/home/d/py"
os.chdir(path)

# узнаем tz. 
# Для этого заберем конфиг НА с помощью REST API и вычленим там time_zone
url = 'http://' + address_hass + ':8123/api/config'

headers = {
    "Authorization": "Bearer " + api_key,
    "content-type": "application/json",
}

response = get(url, headers=headers)

temp = response.text
readable_json = json.loads(temp)
time_zone = readable_json['time_zone']
tz = timezone(time_zone)
#print (tz)
matplotlib.rcParams['timezone'] = time_zone # чтобы в осях графика время было правильное (учет tz)

##########################################################
# ДЛЯ ТЕСТА
# читаем массив данных с НА - температура процессора

# массив заведенный ручками
#temp_data="""[[{"entity_id": "sensor.processor_temperature", "state": "46.2", "attributes": {"unit_of_measurement": "\u00b0C", "friendly_name": "Processor temperature", "device_class": "temperature"}, "last_changed": "2021-07-19T21:00:00+00:00", "last_updated": "2021-07-19T21:00:00+00:00"}, {"entity_id": "sensor.processor_temperature", "state": "47.2", "attributes": {"unit_of_measurement": "\u00b0C", "friendly_name": "Processor temperature", "device_class": "temperature"}, "last_changed": "2021-07-19T21:00:03.838474+00:00", "last_updated": "2021-07-19T21:00:03.838474+00:00"}, {"entity_id": "sensor.processor_temperature", "state": "46.2", "attributes": {"unit_of_measurement": "\u00b0C", "friendly_name": "Processor temperature", "device_class": "temperature"}, "last_changed": "2021-07-19T21:00:18.840096+00:00", "last_updated": "2021-07-19T21:00:18.840096+00:00"}, {"entity_id": "sensor.processor_temperature", "state": "47.2", "attributes": {"unit_of_measurement": "\u00b0C", "friendly_name": "Processor temperature", "device_class": "temperature"}, "last_changed": "2021-07-19T21:01:03.850947+00:00", "last_updated": "2021-07-19T21:01:03.850947+00:00"}, {"entity_id": "sensor.processor_temperature", "state": "46.2", "attributes": {"unit_of_measurement": "\u00b0C", "friendly_name": "Processor temperature", "device_class": "temperature"}, "last_changed": "2021-07-19T21:01:18.843539+00:00", "last_updated": "2021-07-19T21:01:18.843539+00:00"}, {"entity_id": "sensor.processor_temperature", "state": "46.7", "attributes": {"unit_of_measurement": "\u00b0C", "friendly_name": "Processor temperature", "device_class": "temperature"}, "last_changed": "2021-07-19T21:01:48.844643+00:00", "last_updated": "2021-07-19T21:01:48.844643+00:00"}, {"entity_id": "sensor.processor_temperature", "state": "47.2", "attributes": {"unit_of_measurement": "\u00b0C", "friendly_name": "Processor temperature", "device_class": "temperature"}, "last_changed": "2021-07-19T21:02:03.846437+00:00", "last_updated": "2021-07-19T21:02:03.846437+00:00"}, {"entity_id": "sensor.processor_temperature", "state": "46.7", "attributes": {"unit_of_measurement": "\u00b0C", "friendly_name": "Processor temperature", "device_class": "temperature"}, "last_changed": "2021-07-19T21:02:18.845491+00:00", "last_updated": "2021-07-19T21:02:18.845491+00:00"}, {"entity_id": "sensor.processor_temperature", "state": "46.2", "attributes": {"unit_of_measurement": "\u00b0C", "friendly_name": "Processor temperature", "device_class": "temperature"}, "last_changed": "2021-07-19T21:02:48.847300+00:00", "last_updated": "2021-07-19T21:02:48.847300+00:00"}, {"entity_id": "sensor.processor_temperature", "state": "46.7", "attributes": {"unit_of_measurement": "\u00b0C", "friendly_name": "Processor temperature", "device_class": "temperature"}, "last_changed": "2021-07-19T21:03:03.854238+00:00", "last_updated": "2021-07-19T21:03:03.854238+00:00"}]]"""

# прочтем массив из файла 
#f = open('/home/d/py/1.txt', 'r')
#temp_data = f.read()
#f.close()
##########################################################


##########################################################
# запрашиваем данные в НА с помощью REST API 

# рассчитаем время для подставновки в запрос
d = datetime.today() - timedelta(hours=number_of_hours, minutes=0)
filter_date_time = d.strftime("%Y-%m-%dT%H:%M:%S") + "+03:00"
#print (filter_date_time)

url = 'http://' + address_hass + ':8123/api/history/period/' + filter_date_time + '?filter_entity_id=' + entity_id

headers = {
    "Authorization": "Bearer " + api_key,
    "content-type": "application/json",
}

response = get(url, headers=headers)
#print(response.text+"\n\n")
temp_data = response.text


##########################################################
# разбираем ответ

# Уберем лишние ковычки []
temp_data = temp_data[1:len(temp_data)-1]
readable_json = json.loads(temp_data)

# пустые массивы
time_array = np.array([])
state_array = np.array([])

# Цикл обработки массива данных
for i in readable_json:

        #######################
        # почему-то первый элемент в ответе всегда содержит временные метки без миллисекунд
        # в результате получаем ошибку. чтобы исключить эту ошибку приходится выкидывать его из обработки
        if skip_flag == 0:
            skip_flag = "1"
            continue
        ####################### 

        try:
            float(i['state'])       # если значение датчика число, то выполняем всю секцию try: до except:
            
            # формируем массивы для построения графика
            state_array = np.append(state_array, float(i['state']))
            time_update = datetime.strptime(i['last_updated'], '%Y-%m-%dT%H:%M:%S.%f%z')
            time_array = np.append(time_array, time_update.astimezone(tz))
            kol_all += 1

        except:
            # ошибка
            print("uknown state")

#print ("\nВсего обработанно значений = " + str(kol_all))


##########################################################
# строим график

if 1 == 0:

    plt.grid()

    plt.title('Temperature', fontsize=14)     # заголовок графика
    plt.ylabel("\u00b0C", fontsize=10)           # метка Y оси 
    plt.xticks(fontsize=6)                       # шрифт X оси
    plt.yticks(fontsize=10)                      # шрифт Y оси

    plt.plot(time_array, state_array)
    plt.show()



if 1 == 1:

    fig = plt.figure(num=None, facecolor='w', edgecolor='k')

    plt.plot(time_array, state_array)
    plt.title('Temperature', fontsize=16)
    plt.yticks(fontsize=10)
    plt.ylabel("\u00b0C", fontsize=18, labelpad=12, rotation=0, color='steelblue')
    plt.xticks(fontsize=10)         # rotation = 45 - поворот Х меток на 45градусов

    ax = plt.gca()
    ax.yaxis.set_major_formatter(FormatStrFormatter('%.0f'))
    ax.legend(['print: ' + time_array[-1].strftime('%d/%m %H:%M')])
    ax.grid(which='major', color = 'gray', linestyle=':')       # Добавляем линии основной сетки
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(1))       # Задаем шаг дополнительный делений (тиков)
    ax.minorticks_on()                                          # Включаем видимость вспомогательных делений

    xformatter = DateFormatter('%H:%M')
    plt.gcf().axes[0].xaxis.set_major_formatter(xformatter)
    
    plt.show()                  # покажем график
    fig.savefig('plot.png')     # сохраним график


