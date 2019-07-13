import re
import urllib.request
import os
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import scipy as sp
from scipy.misc import imread
from scipy.signal.signaltools import correlate2d as c2d

def resource_path(relative):
    return os.path.join(
        os.environ.get(
            "_MEIPASS2",
            os.path.abspath(".")
        ),
        relative
    )
def get(path):
        # get JPG image as Scipy array, RGB (3 layer)
        data = imread(path)
        # convert to grey-scale using W3C luminance calc
        data = sp.inner(data, [299, 587, 114]) / 1000.0
        # normalize per http://en.wikipedia.org/wiki/Cross-correlation
        return (data - data.mean()) / data.std()
def captcha_solver(pid):
    captcha=Image.open(resource_path('Captcha\\captcha%s.png'%pid))
    captcha.convert('RGBA')
    for letter in range (0,4):
        #Slice captcha image into four 40*40 pieces
        box=[letter*38,0,(letter+1)*38+1,40]
        temp=captcha.crop(box).resize((19,20),Image.ANTIALIAS)
        pixdata=temp.load()
        #Map RGBA colour codes so reduces noises
        for y in range(temp.size[1]):
            for x in range(temp.size[0]):
                if pixdata[x, y][0] < 95:
                    pixdata[x, y] = (0, 0, 0, 255)
                if pixdata[x, y][1] < 95:
                    pixdata[x, y] = (0, 0, 0, 255)
                if pixdata[x, y][2] > 150:
                    pixdata[x, y] = (255, 255, 255, 255)
        temp.save(resource_path('Captcha\\captcha%s_%s.png'%(pid,letter)))

    folders_list=['0','1','2','3','4','5','6','7','8','9']
    answer_list=[]
    for letter in range (0,4):
        corr_list=[]
        img1=get(resource_path('Captcha\\captcha%s_%s.png'%(pid,letter)))
        baseline=c2d(img1,img1,mode='same').max()
        for folder in folders_list:
            sum_corr=0
            counter=0
            for img in os.listdir(resource_path('Iconset\\%s'%folder)):
                img2=get(resource_path('Iconset\\%s\\%s'%(folder,img)))
                corr=c2d(img1,img2,mode='same').max()
                sum_corr+=corr
                counter+=1
            ave_corr=sum_corr/counter
            corr_list.append(abs(ave_corr-baseline))
        answer_list.append(folders_list[corr_list.index(min(corr_list))])
    answer = "".join(str(x) for x in answer_list)
    return answer
def grab_captcha(browser,pid):
    src = "/Telerik.Web.UI.WebResource.axd?type=rca&isc=true&"
    out_path = resource_path('Captcha\\captcha%s.png'%pid)
    raw = browser.page_source
    guid = re.findall(r'(guid=\w*-\w*-\w*-\w*-\w*)',raw)[0]
    ImgLink = "http://services6.tehran.ir"+src+guid
    urllib.request.urlretrieve(ImgLink,out_path)

if __name__ == '__main__':

    pid = os.getpid()
    url = "http://services6.tehran.ir/urbanmodule/%D8%A7%D8%B3%D8%AA%D8%B9%D9%84%D8%A7%D9%85-%D8%B7%D8%B1%D8%AD-%D8%AA%D9%81%D8%B5%DB%8C%D9%84%DB%8C-%D8%AC%D8%AF%DB%8C%D8%AF"
    browser = webdriver.Firefox()
    
    captcha_error = True
    while captcha_error:
        try:
            browser.get(url)
            captchabox = WebDriverWait(browser, 30).until(EC.presence_of_element_located((By.NAME,"dnn$ctr747$ViewTMNewDetailedPlan$ctlCaptcha$CaptchaTextBox")))
            grab_captcha(browser,pid)
            captcha = captcha_solver(pid)
            captchabox.send_keys(captcha)
            option = WebDriverWait(browser, 30).until(EC.presence_of_element_located((By.ID,"dnn_ctr747_ViewTMNewDetailedPlan_rbFileNo")))
            option.click()
            option.send_keys(Keys.RETURN)
            #filenumber_box appears after successful captcha entry. We use it as sanity check here.
            filenumber_box = WebDriverWait(browser, 30).until(EC.presence_of_element_located((By.ID, "dnn_ctr747_ViewTMNewDetailedPlan_txtFileNo")))
            captcha_error = False
        except:
            continue
    folder = '.\\Captcha'
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        #elif os.path.isdir(file_path): shutil.rmtree(file_path)
        except Exception as e:
            print(e)