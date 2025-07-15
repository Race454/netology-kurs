from selenium import webdriver
from selenium.webdriver.common.by import By
import pytest

@pytest.fixture(scope="module")
def browser():
    driver = webdriver.Chrome()
    yield driver
    driver.quit()

def test_yandex_auth(browser):
    browser.get("https://passport.yandex.ru/auth/")
    
    browser.find_element(By.NAME, "login").send_keys("ваш_логин")
    browser.find_element(By.CSS_SELECTOR, ".Button").click()
    
    browser.implicitly_wait(5)  
   
   browser.find_element(By.NAME, "passwd").send_keys("ваш_пароль")
   browser.find_element(By.CSS_SELECTOR, ".Button").click()
   
   assert "Яндекс" in browser.title