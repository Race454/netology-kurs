import requests
import pytest

BASE_URL = "https://cloud-api.yandex.net/v1/disk/resources"
TOKEN = "ваш_токен" 

headers = {
    "Authorization": f"OAuth {TOKEN}"
}

def create_folder(folder_name):
    response = requests.put(f"{BASE_URL}/folders/{folder_name}", headers=headers)
    return response

def test_create_folder_success():
    folder_name = "test_folder"
    
    requests.delete(f"{BASE_URL}/folders/{folder_name}", headers=headers)
    
    response = create_folder(folder_name)
    
    assert response.status_code == 201
    
    response = requests.get(f"{BASE_URL}/?path={folder_name}", headers=headers)
    
    assert response.status_code == 200
    assert folder_name in response.json()['_embedded']['items'][0]['name']


@pytest.mark.parametrize("folder_name", [
    "",
])

def test_create_folder_failure(folder_name):
    response = create_folder(folder_name)
    
    assert response.status_code != 201