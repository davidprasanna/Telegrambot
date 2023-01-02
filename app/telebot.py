from flask import Flask
from flask import request
from flask import Response
import requests
from requests.structures import CaseInsensitiveDict
import database as database
import pandas as pd
from config import get_config
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from database import Restaurent, close_session, commit_session, insert_row, db

config_data = get_config()

TOKEN = "5823544860:AAEKfEG4zhGUjOD5q_6rGRnH2fqTqdeR9lU"
app = Flask(__name__)

db_uri = "postgresql://{0}:{1}@{2}/{3}".format(config_data['Database_credentials']['Database_username'],config_data['Database_credentials']['Database_password'],config_data['Database_credentials']['host'],config_data['Database_credentials']['Database_name'])
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    database.create_all_db()

def parse_message(message):
    chat_id = message['message']['chat']['id']
    txt = message['message']['text']
    return chat_id,txt
 
def tel_send_message(chat_id, text, mode):
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    payload = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode' : mode
                }
   
    r = requests.post(url,json=payload)
    return r

def tel_send_image(chat_id,photo):
    url = f'https://api.telegram.org/bot{TOKEN}/sendPhoto'
    payload = {
                'chat_id': chat_id,
                'photo': photo,
                }
    r = requests.post(url,json=payload)
    return r

def tel_send_location(chat_id,latitude,longitude):
    url = f'https://api.telegram.org/bot{TOKEN}/sendLocation'
    payload = {
                'chat_id': chat_id,
                'latitude': latitude,
                'longitude': longitude
                }
   
    r = requests.post(url,json=payload)
    return r

def getLocation(res_name):
    url = "https://api.geoapify.com/v1/geocode/search?text={}&apiKey=17f4a280f17049bcaf71f12f45b0bfc8".format(res_name)
    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"

    resp = requests.get(url, headers=headers)
    return resp

def getaddress(res_name):
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome("/usr/lib/chromium-browser/chromedriver",options=options)
    url = 'https://google.com/search?q=' + res_name
    driver.get(url)
    content = driver.page_source
    soup = BeautifulSoup(content)
    address=soup.find('span', attrs={'class':'LrzXr'})
    return address.text

def getrating(res_name):
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome("/usr/lib/chromium-browser/chromedriver",options=options)
    url = 'https://google.com/search?q=' + res_name
    driver.get(url)
    content = driver.page_source
    soup = BeautifulSoup(content)
    rating=soup.find('span', attrs={'class':'Aq14fc'})
    return rating.text

def getlatlng(res_name):
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome("/usr/lib/chromium-browser/chromedriver",options=options)
    url = 'https://google.com/search?q=' + res_name
    driver.get(url)
    ele=driver.find_element("link text",'Maps')
    ele.click()
    current_url = driver.current_url
    WebDriverWait(driver, 10).until(EC.url_changes(current_url))
    content=driver.current_url
    lat, long = content.split("!3d")[1].split("!4d")
    return lat , long

def getmenu(res_name):
    # options = Options()
    # options.add_argument("--headless")
    driver = webdriver.Chrome("/usr/lib/chromium-browser/chromedriver")
    url = 'https://google.com/search?q=' + res_name
    driver.get(url)
    ele=driver.find_element("link text",'Images')
    ele.click()
    ele1=driver.find_element("link text",'menu')
    ele1.click()
    ele2=driver.find_element('class name','bRMDJf').click()
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'v4dQwb')))
    ele3=driver.find_element('class name','v4dQwb').find_element('tag name','img').get_attribute('src')
    print("ele3:",ele3)
    # return img
 
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        msg = request.get_json()
        chat_id,txt = parse_message(msg)
        if txt.lower() == "hi":
            username = msg['message']['from']['first_name']
            description = "Hello {} I am wanderlust bot and some of the feature i have are:\n-To add your fav restaurent typein--> *add res: <restaurant_name>*\n-To list all the fav restaurent--> *list res*\n-To get location of the restaurent--> *get location: <restaurent name>*\n-To get Restaurent in particular location--> *get res:<location>*".format(username)
            tel_send_message(chat_id,description,'Markdown')
        elif "add res" in txt.lower():
            res_name=txt.split(':')[1]
            loc = getaddress(res_name)
            obj = Restaurent(
                RestaurentName=res_name.split(',')[0],
                location=loc,
                Area='',
                AddedBy=msg['message']['from']['first_name']
            )
            insert_row(obj)
            commit_session()
            close_session()
            tel_send_message(chat_id,"Restaurent successfully added to the list",'Markdown')
        elif "get location" in txt.lower():
            res_name=txt.split(':')[1]
            address = getaddress(res_name)
            tel_send_message(chat_id,"Restaurent address:\n-{}".format(address),'Markdown')
            latitude,longitude = getlatlng(res_name)
            tel_send_location(chat_id,latitude,longitude)
        elif "get res" in txt.lower():
            area=txt.split(':')[1].strip()
            res_list=Restaurent.query.filter(Restaurent.location.contains(area)).all()
            rest = pd.DataFrame([(d.id, d.RestaurentName, d.location)for d in res_list],
                                columns=["id", "RestaurentName", "location"])
            text="Restaurent list in {} location:".format(area)
            for index, row in rest.iterrows():
                text = text + "\n-{}".format(row['RestaurentName'])
            tel_send_message(chat_id,text,'Markdown')
        elif "grd" in txt.lower():
            res_name=txt.split(':')[1].strip()
            rating=getrating(res_name)
            text='*{}\nRated: {} out of 5*'.format(res_name,rating)
            tel_send_message(chat_id,text,'Markdown')
        elif "get menu" in txt.lower():
            res_name=txt.split(':')[1]
            img=getmenu(res_name)
            # tel_send_image(chat_id,img)
        elif "list res" in txt.lower():
            obj=Restaurent.query.all()
            rest = pd.DataFrame([(d.id, d.RestaurentName, d.location)for d in obj],
                                columns=["id", "RestaurentName", "location"])
            if rest.empty == False:
                restaurent = "The list of fav restaurent are:"
                for index, row in rest.iterrows():  
                    restaurent = restaurent + '\n-{0}'.format(row['RestaurentName'])
                tel_send_message(chat_id,restaurent,'Markdown')
            else:
                tel_send_message(chat_id,'No restaurent added.','Markdown')
        else:
            username = msg['message']['from']['first_name']
            description = "Hello {} I am wanderlust bot and some of the feature i have are:\n-To add your fav restaurent type--> *add res: <restaurant_name>*\n-To list all the fav restaurent--> *list res*\n-To get location of the restaurent--> *get location: <restaurent name>*\n-To get Restaurent in particular location--> *get res:<location>*".format(username)
            tel_send_message(chat_id,description,'Markdown')
       
        return Response('ok', status=200)
    else:
        return "<h1>Welcome!</h1>"
 
if __name__ == '__main__':
   app.run(host='127.0.0.1', port=5002,threaded=True)