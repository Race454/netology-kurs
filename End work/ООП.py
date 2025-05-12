import requests
import json
import os

VK_API_URL = 'https://api.vk.com/method/photos.get'
YANDEX_DISK_API_URL = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
TOKEN_VK = 'YOUR_VK_TOKEN'
TOKEN_YANDEX = 'YOUR_YANDEX_TOKEN'
USER_ID = 'USER_ID'
PHOTOS_COUNT = 5

def get_photos(user_id):
    params = {
        'owner_id': user_id,
        'album_id': 'profile',
        'access_token': TOKEN_VK,
        'v': '5.131'
    }
    response = requests.get(VK_API_URL, params=params)
    return response.json()['response']['items']

def upload_to_yandex_disk(file_name, file_path):
    headers = {
        'Authorization': f'OAuth {TOKEN_YANDEX}'
    }
    upload_url_response = requests.get(YANDEX_DISK_API_URL, headers=headers, params={'path': file_name, 'overwrite': 'true'})
    upload_url = upload_url_response.json().get('href')
    
    with open(file_path, 'rb') as file:
        requests.put(upload_url, files={'file': file})

def main():
    photos = get_photos(USER_ID)
    
    sorted_photos = sorted(photos, key=lambda x: (-x['likes']['count'], x['date']))
    
    uploaded_photos_info = []
    
    for photo in sorted_photos[:PHOTOS_COUNT]:
        max_size_photo = max(photo['sizes'], key=lambda x: x['width'] * x['height'])
        file_name = f"{max_size_photo['likes']['count']}.jpg"
        
        photo_url = max_size_photo['url']
        photo_response = requests.get(photo_url)
 
        temp_file_path = os.path.join('/tmp', file_name)
        with open(temp_file_path, 'wb') as temp_file:
            temp_file.write(photo_response.content)
        
        upload_to_yandex_disk(file_name, temp_file_path)
        
        uploaded_photos_info.append({
            "file_name": file_name,
            "size": max_size_photo['type']
        })
        
        os.remove(temp_file_path)

    with open('uploaded_photos.json', 'w') as json_file:
        json.dump(uploaded_photos_info, json_file)

if __name__ == '__main__':
    main()