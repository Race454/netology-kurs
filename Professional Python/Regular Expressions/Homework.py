import csv
import re
from pprint import pprint

with open("phonebook_raw.csv", encoding="utf-8") as f:
    rows = csv.reader(f, delimiter=",")
    contacts_list = list(rows)

def format_fio(contact):
    fio_parts = " ".join(contact[:3]).split()
    if len(fio_parts) == 2:  # Если только Ф и И
        lastname, firstname = fio_parts
        surname = ""
    elif len(fio_parts) == 3:  # Если Ф, И и О
        lastname, firstname, surname = fio_parts
    else:
        lastname, firstname, surname = contact[0], "", ""
    
    return [lastname, firstname, surname] + contact[3:]


def format_phone(phone):
    phone = re.sub(r'\D', '', phone)
    if len(phone) == 11 and phone.startswith('7'):
        return f"+7({phone[1:4]}){phone[4:7]}-{phone[7:9]}-{phone[9:]}"
    elif len(phone) == 10 and phone.startswith('9'):
        return f"+7({phone[:3]}){phone[3:6]}-{phone[6:8]}-{phone[8:]}"
    elif len(phone) == 11 and phone.startswith('8'):
        return f"+7({phone[1:4]}){phone[4:7]}-{phone[7:9]}-{phone[9:]}"
    return phone

contacts_dict = {}

for contact in contacts_list:
    formatted_contact = format_fio(contact)
    formatted_contact[5] = format_phone(contact[5]) if len(contact) > 5 else ""
    
    key = (formatted_contact[0], formatted_contact[1])
    
    if key not in contacts_dict:
        contacts_dict[key] = formatted_contact
    else:
        for i in range(3, len(formatted_contact)):
            if formatted_contact[i] and not contacts_dict[key][i]:
                contacts_dict[key][i] = formatted_contact[i]


contacts_list = list(contacts_dict.values())

with open("phonebook.csv", "w", encoding="utf-8") as f:
    datawriter = csv.writer(f, delimiter=',')
    datawriter.writerows(contacts_list)

pprint(contacts_list)