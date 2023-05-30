from bs4 import BeautifulSoup
import requests
import urllib.request
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
# Для работы с данными в таблицах
import pandas as pd

# Для занесения всех новых данных в эксель
import openpyxl
from openpyxl import Workbook
import os


# Указываем данные с сайта для того, чтобы не дублировать их в коде + чтобы можно было занести их в эксель легко
region = 'Республика Удмуртия'  # Название региона
name_zak_sobr = 'Государственный совет Удмуртской Республики'  # Название зак собрания
# Ссылка на главную страницу зак собрания, лучше в конце иметь 
ssil_zak_sobr = 'http://www.udmgossovet.ru'
# Ссылка на страницу зак собрания где публикуются законы
zakoni = 'http://www.udmurt.ru/regulatory/?typeid=352435&year=2015&doccnt='
# Ссылка на страницу зак собрания, где публикуются новости
novosti = 'http://www.udmgossovet.ru/press/news/'

# В какой главной папке будет сохранена папка региона
path = '...'

# Создаем папку. Если она уже существует, программа пропускает этот шаг
try:
    os.mkdir(path+f'{region}')
except FileExistsError:
    pass
try:
    os.mkdir(path + f'{region}'+"//Photo")
except FileExistsError:
    pass

df = pd.DataFrame()  # создаем датафрейм, в который будем заносить потом данные

# в случае, когда депутаты расположены на разных страницах под номерами, мы создаем цикл
# Где проходимся по каждому номеру страницы, и оттуда забираем их данные
dep_link_list = []
# Ищем тег, который показывает начало данных каждого депутата в коде страницы
i = 0
while i < 3:
    i += 1
    # Ссылка страницы депутатов. f{i} позволяет добавлять в строку переменную
    ssil_stran_dep = f'http://www.udmgossovet.ru/consist/structure/deputies/?PAGEN_1={i}'

    # Получаем данные со страницы с депутатами
    source = requests.get(ssil_stran_dep)
    soup = BeautifulSoup(source.text, 'lxml')

    # Ищем тег, который показывает начало данных каждого депутата в коде страницы
    for article in soup.find('div', class_="news-list").find_all('div', class_="news-item deputat_list_item"):
        dep_link_list.append(ssil_zak_sobr+article.find('a')['href'])


    # Для каждого депутата получаем ссылку на его профиль, чтобы потом оттуда получить данные
    #     обычно ссылки находятся под тегом а[href]
    #
    #     Обычно ссылки на сайте на стран деп. короткие, поэтому дополняем, если будут полными - удаляем
    #
    # После того как получили все ссылки на депутатов, проходимся по каждому из них и собираем данные
for dep_link in dep_link_list:
    deputat_full_data = {}
    source_dep_link = requests.get(dep_link)
    soup_dep_link = BeautifulSoup(source_dep_link.text, 'lxml')


    # Эта часть нужна для генерации строчки экселя для каждого депутата
    deputat_full_data['Регион'] = region
    deputat_full_data['Оф название зак собрания'] = name_zak_sobr
    deputat_full_data['Ссылка на страницу Зак собрания'] = ssil_zak_sobr
    deputat_full_data['Ссылка на страницу принятых законов'] = zakoni
    deputat_full_data['Ссылка на страницу новостей зак собрания'] = novosti


    # уменьшаем поле поиска до меньшего блока - карточки депутата
    article_dep = soup_dep_link.find('div', class_="news-detail")

    # Далее внутри этой "карточки" поиском вычленяем по тегам и ключевым словам нужную нам информацию
    deputat_full_data['Имя'] = article_dep.find('div', class_="deputie_wrap").find('h3').text.strip()
    print(deputat_full_data['Имя'])

    # ищем партию на сайте
    try:
        deputat_full_data['Партия']=article_dep.find(lambda tag: 'парти' in tag.text.lower() or 'впп' in tag.text.lower() or 'фракци' in tag.text.lower()).text
    except:
        deputat_full_data['Партия']='0'

    #приводим название к общему стандарту
    if 'единая россия' in deputat_full_data['Партия'].lower():
        deputat_full_data['Партия'] = 'ЕДИНАЯ РОССИЯ'
    elif 'лдпр' in deputat_full_data['Партия'].lower():
        deputat_full_data['Партия'] = 'ЛДПР'
    elif 'коммунистическая партия российской федерации' in deputat_full_data['Партия'].lower() or 'кпрф' in deputat_full_data['Партия'].lower():
        deputat_full_data['Партия'] = 'КПРФ'
    elif 'справедливая россия' in deputat_full_data['Партия'].lower():
        deputat_full_data['Партия'] = 'Справедливая Россия'
    elif 'новые люди' in deputat_full_data['Партия'].lower():
        deputat_full_data['Партия'] = 'Новые люди'
    elif 'партия пенсионеров' in deputat_full_data['Партия'].lower():
        deputat_full_data['Партия'] = 'Партия пенсионеров'
    else:
        deputat_full_data['Партия'] = 0

    # ищем год рождения депутата
    try:
        god=[]
        predls = article_dep.text.split('Родил')[1].split('\n')[0].split()
        for j in predls:
            if len(j)>=4 and '19' in j:
                deputat_full_data['Год Рождения']=j
    except:
        deputat_full_data['Год Рождения'] = 0

    # ищем округ на сайте
    try:
        predls = article_dep.find(lambda tag: 'округ' in tag.text.lower()).text.split('.')
        deputat_full_data['Округ'] = 0
        for p in predls:
            if '№' in p:
                deputat_full_data['Округ']="№"+p.split('№')[1].split()[0]
            if 'единый' in p or 'единому' in p or 'единого' in p:
                deputat_full_data['Округ'] = 'Единый избирательный округ'
    except:
        deputat_full_data['Округ'] = 0

    # берем со страницы депутата информацию о его биографии
    try:
        deputat_full_data['Биография'] = 'Образование' + article_dep.text.split('Образование')[1].split('Государственные награды')[0]
    except:
        deputat_full_data['Биография'] = 0
        
    # поиск почты депутата
    try:
        predls = article_dep.find(lambda tag: '@' in tag.text.lower()).text.split()
        for h in predls:
            if '@' in h:
                 deputat_full_data['Рабочая почта'] = h.strip()
    except:
        deputat_full_data['Рабочая почта'] = 0

    # данный сайт не содержит ссылки на страницы новостей депутатов, поэтому ставим 0
    deputat_full_data['Ссылка на страницу новостей депутата'] = 0

    # по обозначенному пути сохраняем фотографии депутатов, которые скачиваем по ссылке
    try:
        urllib.request.urlretrieve(ssil_zak_sobr + article_dep.find('div', class_= "deput_img").find('img')['src'], path+f'{region}'+"//Photo//"+f'{deputat_full_data["Имя"]}.jpg')
    except:
        try:
            urllib.request.urlretrieve(article_dep.find('div', class_= "deput_img").find('img')['src'], path+f'{region}'+"//Photo//"+f'{deputat_full_data["Имя"]}.jpg')
        except:
            pass

    # заполняем основной датафрейм словарем, который собрали в ходе данной итерации
    df = df.append(deputat_full_data, ignore_index=True, sort=False)

# эта часть заносит полученные данные в экселевский файл
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
