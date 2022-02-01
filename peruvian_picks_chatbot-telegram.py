import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd 


# use creds to create a client to interact with the Google Drive API
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
client = gspread.authorize(creds)

# Find a workbook by name and open the first sheet
# Make sure you use the right name here.
sheet = client.open("Peruvian Picks - Datos membresias (1)").sheet1

# Extract and print all of the values
nombre = sheet.col_values(1)
usuario = sheet.col_values(2)
fecha_ingreso = sheet.col_values(3)
paquete = sheet.col_values(4)
receptor_deposito = sheet.col_values(5)
tiempo_membresia = sheet.col_values(6)
duracion_plan = sheet.col_values(7)
tiempo_grupo = sheet.col_values(8)
membresia_restante = sheet.col_values(9)
estado = sheet.col_values(10)


d = {'Nombre': nombre, 'Usuario': usuario, 'Fecha de ingreso': fecha_ingreso, 'Paquete': paquete, 'Receptor de deposito': receptor_deposito, 'Tiempo de membresia': tiempo_membresia, 'Duracion del plan': duracion_plan, 'Tiempo en el grupo': tiempo_grupo, 'Membresaia restante': membresia_restante, 'Estado': estado}

df = pd.DataFrame(d)

print(df)