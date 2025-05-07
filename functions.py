import requests
import os
import re
import json
import shutil
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from requests.auth import HTTPBasicAuth

# Função para obter todos os IDs das máquinas
def get_computer_ids(urlIDs):
    username = get_env("API_USER")
    password = get_env("API_PWD")
    
    if not password:
        raise ValueError("A senha não foi encontrada. Certifique-se de definir a variável de ambiente 'API_PWD'.")
    
    try:
        response = requests.get(urlIDs, auth=HTTPBasicAuth(username, password))
        response.raise_for_status()
        data = response.json()
        # Supondo que a resposta seja uma lista de IDs
        # Se o ID estiver em um campo específico, por exemplo 'id', extraímos dessa forma
        return [item['ID'] for item in data] if isinstance(data, list) else []
    except requests.exceptions.RequestException as e:
        print(f"Erro ao obter IDs: {e}")
        return False


# Função para obter informações de uma máquina com base no ID
def get_computer_info(computerID, urlBase):
    username = get_env("API_USER")
    password = get_env("API_PWD")
    
    if not password:
        raise ValueError("A senha não foi encontrada. Certifique-se de definir a variável de ambiente 'API_PWD'.")
    
    try:
        # Garantir que o ID seja passado como um número simples
        response = requests.get(f"{urlBase}{computerID}", auth=HTTPBasicAuth(username, password))
        response.raise_for_status()

        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Erro ao obter informações da máquina {computerID}: {e}")
        return False
        
        
# Função para salvar os dados da máquina em um arquivo
def save_computer_info(computerID, data, outputDir):
    try:                
        # Obter data e hora atual no formato desejado
        currentDatetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        # Gerando o nome do arquivo com base no ID e data/hora
        filename = f"ID_{computerID}-{currentDatetime}.txt"
        txtPath = os.path.join(outputDir, filename)
        
        with open(txtPath, "w", encoding="utf-8") as file:
            file.write(str(data))
        
        return filename    
    except Exception as e:
        print(f"Erro ao salvar os dados da máquina {computerID}: {e}")
        return False 


# Função para verificar se uma pasta existe
def verify_folder_exist(folderName):
    # Retorna verdadeiro caso a pasta já exista
    if os.path.isdir(folderName):
        return True
    else:
        create_folder(folderName)
        return False


# Função para verificar se pastas está vazia
def verify_folder_is_empty(folder):
    return True if os.listdir(folder) else False


# Função para criar uma pasta    
def create_folder(folderName):
    os.makedirs(folderName)
    return False


# Função para buscar o arquivo antigo com o ID
def search_file_for_id(computerID, folderPath):
    # Nome do arquivo com o ID:
    # idToSearch = "ID_" + computerID
    idToSearch = f"ID_{computerID}"
    
    # Regex para capturar o ID no nome do arquivo
    pattern = rf"({idToSearch})-\d{{4}}-\d{{2}}-\d{{2}}_\d{{2}}-\d{{2}}-\d{{2}}\.txt"
       
    # armazena o nome do arquivo encontrado
    fileFound = ''
   
    # Percorre os arquivos na pasta
    for filename in os.listdir(folderPath):
        match = re.match(pattern, filename)
        if match:
            fileFound = filename
            break  # Sai do loop, já que só haverá um arquivo por ID
        
    # Retorna o nome do arquivo encontrado
    return fileFound


# Função que verifica as diferenças:
def diff_files(fileA, fileB):
    if len(set(fileA) - set(fileB)) > 0:      
        return f"Items removed: {set(fileA) - set(fileB)}"
        
    if len(set(fileB) - set(fileA)) > 0:
        return f"Items added: {set(fileB) - set(fileA)}"
        
    if set(fileA) == set(fileB):
        # print(f"They are the same")
        return False


# Função para obter todos os softwares do cliente
def get_softwares(jsonPath):
    try:        
        # Carregar o arquivo JSON e extrair NAME e OSNAME
        with open(jsonPath, 'r', encoding='utf-8') as file:
            loadedData = json.load(file)
                        
            # Extrair informações dos softwares
            idVM = next(iter(loadedData))
            softwares = loadedData[idVM].get("softwares", [])
            # softwares = loadedData.get("1", {}).get("softwares", [])
            
            softwareNames=[]
            for software in softwares:
                softwareName = software.get("NAME", "Não encontrado")
                softwareGUID = software.get("GUID", "GUID não encontrado")
                softwareVersion = software.get("VERSION", "Version não encontrado")
                
                softwareNames.append(f"Name: {softwareName} | GUID: {softwareGUID} | Version: {softwareVersion}")
            return softwareNames
    # except json.JSONDecodeError:
    #     print("Erro ao decodificar a resposta JSON.")
    #     return False
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return False


# Função para obter todos os usuários
def get_users(jsonPath):
    try:
        with open(jsonPath, 'r', encoding='utf-8') as file:
            loadedData = json.load(file)
            
            # Extrair informações dos usuários
            idVM = next(iter(loadedData))
            users = loadedData[idVM].get("winusers", [])
                        
            # users = loadedData.get("1", {}).get("winusers", [])
            userNames=[]
            for user in users:
                userName = user.get("NAME", "Não encontrado")
                userSID = user.get("SID", "Não encontrado")
                userDescription = user.get("DESCRIPTION", "Nenhuma descrição")
                
                userNames.append(f"Name: {userName} | SID: {userSID} | Descrição: {userDescription}")
            return userNames
    
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return False


# Função para mover o arquivo inventariado para dentro da subpasta:
def move_file_to_folder(folderOrigin, folderDestiny, fileName):
    try:
        limbo = verify_folder_exist(folderDestiny)        
        shutil.move(folderOrigin + "/" + fileName, folderDestiny + "/" + fileName)
        return True
    except ValueError as e:
        print(e)
        return False


# Função para pegar o nome e o IP da VM:
def get_name_and_ip_computer(jsonPath):
    try:
        # Carregar o arquivo JSON e extrair NAME e OSNAME
        with open(jsonPath, 'r', encoding='utf-8') as file:
            loadedData = json.load(file)
            
            valuesJson = next(iter(loadedData.values()))
            nameComputer = valuesJson["hardware"]["NAME"]
            ipComputer = valuesJson["hardware"]["IPADDR"]
        
        return (nameComputer + " - " + ipComputer)
    
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return False


# Função para enviar notificação via Slack
#def send_notification(message, emailDestino):
    ## pega as variáveis necessárias
#    emailAddr = get_env("EMAIL_ADDS")
#    emailPWD = get_env("EMAIL_PWD")    
#    emailSMTP = get_env("EMAIL_SMTP")
    
#    emailAddr = emailAddr.replace('"', '')
#    emailPWD = emailPWD.replace('"', '')
#    emailSMTP = emailSMTP.replace('"', '')
#    emailDestino = emailDestino.replace('"', '')
    
   # try:
     #   msg = MIMEMultipart()
     #   msg['From'] = emailAddr
     #   msg['To'] = emailDestino
     #   msg['Subject'] = "RSI - Alerta"
     #   msg.attach(MIMEText(message, 'plain', 'utf-8'))

       # servidor = smtplib.SMTP(emailSMTP, 587)
      #  servidor.starttls()  # Ativa criptografia
     #   servidor.login(emailAddr, emailPWD)
         # Envio do e-mail
                 
    #    servidor.send_message(msg)
   #     print("E-mail enviado com sucesso!")
        
        # Encerrar a conexão
  #      servidor.quit()        
        
 #   except Exception as e:
#        print(f"Erro ao enviar o e-mail: {e}")
    

## Função para carregar as variáveis do arquivo .env
def load_env(filepath):
    ## Carrega as variáveis do arquivo
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"O arquivo {filepath} não foi encontrado.")
    
    envVars = {}
    try:
        with open(filepath, "r") as file:
            for line in file:
                # Ignora linhas vazias ou comentários
                if line.strip() and not line.startswith("#"):
                    # Divide chave e valor no '='
                    key, value = line.strip().split("=", 1)
                    envVars[key.strip()] = value.strip()
                    
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return False
    return envVars
    
## Função para buscar a variável carregada
def get_env(keyEnv):
    envVars = load_env("C:/Users/Matheus Gomes/Downloads/.env")
    
    if keyEnv in envVars:
        return envVars[keyEnv]
    else:
        return f"Variável '{keyEnv}' não encontrada no arquivo .env"