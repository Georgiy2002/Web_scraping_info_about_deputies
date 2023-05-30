from time import sleep
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
import urllib.request
import openpyxl
from openpyxl import Workbook
import os
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)



browser = webdriver.Chrome(executable_path=r"...") #тут нужна ссылка на chromedriver
path = '...' #тут необходимо написать путь до папки где будут сохранены фотографии и эксель-файлы

#создаем датафрей, который в конце занесем в эксель файл
df = pd.DataFrame()

region = 'Республика Татарстан'  # Название региона
name_zak_sobr = 'Государственное собрание Республики Татарстан'  # Название зак собрания
# Ссылка на главную страницу зак собрания, лучше в конце иметь /
ssil_zak_sobr = 'https://gossov.tatarstan.ru'
# Ссылка на страницу зак собрания где публикуются законы
zakoni = 'https://gossov.tatarstan.ru/activity/lawmaking/zakonmesyc'
# Ссылка на страницу зак собрания, где публикуются новости
novosti = 'https://gossov.tatarstan.ru/index.htm/news/tape'

#создаем файл, в который будем сохранять фотографии и эксель файлы
try:
    os.mkdir(path+f'{region}')
except FileExistsError:
    pass
try:
    os.mkdir(path + f'{region}'+"//Photo")
except FileExistsError:
    pass

url = 'https://gossov.tatarstan.ru/structure/deputaty' # сслыка на страницу с депутатами
oroboros = 0
while oroboros == 0:
    try:
        browser.get(url)  # заходим на страницу с депутатами
        oroboros = 1
    except:
        sleep(4)
sleep(3)

#запускаем цикл длина которого соответствует кол-ву депутатов
for y in range(len(browser.find_elements(By.CLASS_NAME, 'deputy'))):
    # создаем словарь, в который будем заполянть информацию
    deputat_full_data = {}
    deputat_full_data['Регион'] = region
    deputat_full_data['Оф название зак собрания'] = name_zak_sobr
    deputat_full_data['Ссылка на страницу Зак собрания'] = ssil_zak_sobr
    deputat_full_data['Ссылка на страницу принятых законов'] = zakoni
    deputat_full_data['Ссылка на страницу новостей зак собрания'] = novosti

    # ищем имя на сайте
    name = browser.find_elements(By.CLASS_NAME, 'deputy-details')[y].find_element(By.TAG_NAME, 'a')
    deputat_full_data['Имя'] = ' '.join(name.text.split('\n'))

    # ищем партию на сайте
    party = browser.find_elements(By.CLASS_NAME, 'party')[y]
    deputat_full_data['Партия'] = party.text
    if deputat_full_data['Партия'] == '':
        deputat_full_data['Партия'] = 0

    # ищем округ на сайте
    okrug = browser.find_elements(By.CLASS_NAME, 'district')[y]
    deputat_full_data['Округ'] = okrug.text

    # после сбора общей информации, переходим к персональной
    # кликаем по ссылке на конкретного депутата
    name.click()
    sleep(4)
    try:
        browser.find_element(By.XPATH, '//*[@id="page-content"]/div/div[2]/div/div[1]/div[2]').click()
        biography = browser.find_element(By.CLASS_NAME, 'wysiwyg')
        predls =biography.text.split('одил')[1].split('\n')[0].split()

        # ищем год рождения депутата
        for i in predls:
            if '19' in i:
                deputat_full_data['Год Рождения'] = i

        #берем со страницы депутата информацию о его биографии
        deputat_full_data['Биография'] = biography.text

        #если не получилось первым способом собрать необходимую информацию, пользуемся вторым с помощью механизма try-except
    except:
        browser.find_element(By.XPATH, '//*[@id="page-content"]/div/div[2]/div/div[1]/div[1]').click()
        biography = browser.find_element(By.CLASS_NAME, 'wysiwyg')
        predls = biography.text.split('одил')[1].split('\n')[0].split()
        for i in predls:
            if '19' in i:
                deputat_full_data['Год Рождения'] = i
        deputat_full_data['Биография'] = biography.text

    # поиск почты депутата
    deputat_full_data['Рабочая почта'] = 0
    try:
        browser.find_element(By.XPATH, '//*[@id="page-content"]/div/div[2]/div/div[1]/div[3]').click()
        mails = browser.find_element(By.CLASS_NAME, 'contacts').find_elements(By.TAG_NAME, 'a')
        for d in mails:
            if '@' in d.text:
                deputat_full_data['Рабочая почта'] = d.text
    except:
        pass
    if deputat_full_data['Рабочая почта'] == 0:
        browser.find_element(By.XPATH, '//*[@id="page-content"]/div/div[2]/div/div[1]/div[2]').click()
        mails = browser.find_element(By.CLASS_NAME, 'contacts').find_elements(By.TAG_NAME, 'a')
        for d in mails:
            if '@' in d.text:
                deputat_full_data['Рабочая почта'] = d.text

    # данный сайт не содержит ссылки на страницы новостей депутатов, поэтому ставим 0
    deputat_full_data['Ссылка на страницу новостей депутата'] = 0

    #берем ссылку на фотографию депутатов
    image = browser.find_element(By.TAG_NAME, 'img').get_attribute('src')

    #по обозначенному пути сохраняем фотографии депутатов, которые скачивае по взятой ссылке
    try:
        urllib.request.urlretrieve(image, path + f'{region}' + "//Photo//" + f'{deputat_full_data["Имя"]}.jpg')
    except:
        pass

    #перезаходим на страницу со всеми депутатами для начала следующей итерации
    browser.get(url)
    sleep(3)

    # заполняем основной датафрейм словарем, который собрали в ходе данной итерации
    df = df.append(deputat_full_data, ignore_index=True, sort=False)


# по пути, обозначенному выше, создаем эксель-файл, в который сохраняем полученную информацию
wb = Workbook()
wb.save(path +
        f'{region}//'+f'{region}.xlsx')
workbook = openpyxl.load_workbook(
    path+f'{region}//'+f'{region}.xlsx')
writer = pd.ExcelWriter(
    path+f'{region}//'+f'{region}.xlsx', engine='openpyxl')
writer.book = workbook
writer.sheets = dict((ws.title, ws) for ws in workbook.worksheets)
df.to_excel(writer, 'Sheet')
writer.save()
writer.close()

print('Done')