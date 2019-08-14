import os
import logging
import datetime
import calendar
import yaml
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from customCell import CustomCell
from person import Person
from pymongo import MongoClient
import messenger

logger = logging.getLogger('execution')
cfg = None

def load_keyfile_dict():
	key = {
		"type": "service_account",
		"private_key_id": os.environ['GOOGLE_PRIVATE_KEY_ID'],
		"private_key": os.environ['GOOGLE_PRIVATE_KEY'].replace("\\n", "\n"),
		"client_email": os.environ['GOOGLE_CLIENT_EMAIL'],
		"client_id": os.environ['GOOGLE_CLIENT_ID'],
		"auth_uri": "https://accounts.google.com/o/oauth2/auth",
		"token_uri": "https://oauth2.googleapis.com/token",
		"auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
		"client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/{}".format(os.environ['GOOGLE_CLIENT_EMAIL'])
	}
	print(key)
	return key


def process_delivery(sheet, item_type, day):
	logger.info("Looking for {} on weekday: {}".format(item_type, day))
	deliveries = []
	item_config = cfg['itens'][item_type]
	item_name = item_config['text']
	quantity_cell = CustomCell(item_config['quantity']['row'], item_config['quantity']['col'])
	value_cell = CustomCell(item_config['value']['row'], item_config['value']['col'])
	today = datetime.date.today()
	next_delivery_day = today + datetime.timedelta((((day-1)-today.weekday()) % 7) + 1)
	cells_found = sheet.findall(next_delivery_day.strftime("%d/%m/%Y"))
	item_col = sheet.find(item_name).col
	quantity = sheet.cell(quantity_cell.row, quantity_cell.col).value
	value = sheet.cell(value_cell.row, value_cell.col).value
	for cell in cells_found:
		person_name = sheet.cell(cell.row, item_col).value
		if person_name != "":
			delivery = {
				'person_name': person_name,
				'quantity': quantity,
				'value': value,
				'item': item_name,
				'delivery_date': next_delivery_day.strftime("%d/%m/%Y"),
				'created_at': datetime.datetime.now(),
				'sent': False
			}
			deliveries.append(delivery)
		else:
			logger.info('No person in row {} col {}'.format(cell.row, item_col))
	return deliveries

def execute():
	global cfg
	logger.info('Loading configurations')
	try:
		with open("config.yml", 'r', encoding='utf8') as ymlfile:
			cfg = yaml.safe_load(ymlfile)
	except FileNotFoundError:
		logger.critical('To execute this script it is necessary config.yml')
		exit()

	scopes = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
	credentials = ServiceAccountCredentials.from_json_keyfile_dict(load_keyfile_dict(), scopes)

	client = gspread.authorize(credentials)
	sheet = client.open(cfg['google']['sheet_name']).sheet1
	
	deliveries = []
	for item, values in cfg['itens'].items():
		deliveries += process_delivery(sheet, item, values['weekday'])
	logger.info("Found {}".format(len(deliveries)))
	if(len(deliveries) > 0):
		client = MongoClient(os.environ['MONGO_URL'])
		database = client['alerts']
		user_collection = database['users']
		for delivery in deliveries:
			user = user_collection.find_one({"spreadsheet_identifier": delivery['person_name']})
			if(user != None):
				if("alert_weekday" in user and user['alert_weekday'] != None and user['alert_weekday'] != "" and str(datetime.date.today().weekday()) == user['alert_weekday']):
					if('email' in user and user['email'] != None and user['email'] != ""):
						delivery['sent'] = messenger.send_email(user, delivery)
					if('alert_telegram' in user and user['alert_telegram']):
						delivery['sent'] = messenger.send_message(user, delivery)

					logger.info('Nome: {}, Quantidade: {}, Valor: {}'.format(delivery['person_name'] , delivery['quantity'], delivery['value']))
			
				else:
					logger.info('Do not send notification today {} to {}, configuration = {}'.format(datetime.date.today().weekday(),delivery['person_name'], user['alert_weekday']))
			else:
				logger.info('Não há usuário cadastrado')
		logs_collection = database['logs']
		log_id = logs_collection.insert_many(deliveries)
		logger.info('Insert {} log registers into database'.format(len(deliveries)))
		client.close()

if __name__ == '__main__':
	print('Esse arquivo não pode ser executado diretamente!')