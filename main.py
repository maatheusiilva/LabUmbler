from functions import *

# URL de base da API
API_URL_BASE = "http://177.55.115.29/ocsapi/v1/"  # URL de produção

# URL da API para listar todos os IDs das máquinas
urlIDs = API_URL_BASE + "computers/listID"

# URL base para consultar informações de cada máquina
urlBase = API_URL_BASE + "computer/"

# Pasta para armazenar os arquivos do inventário coletado 
outputDir = "C:/Users/Matheus Gomes/Desktop/files"

# Pasta para armazenar os arquivos já inventariados
folderIventoriado = outputDir + "/iventariado"

# Mensagem para o log
message = ""

# ----------- Blacklist de softwares -------------
software_blacklist = [
    "Google Chrome",
    "Mozilla Firefox",
    "7-Zip",
    "VLC media player",
    "Adobe Reader"
]

# Função para filtrar softwares ignorados pela blacklist
def filter_blacklist(software_list, blacklist):
    return [
        s for s in software_list
        if not any(b.lower() in s.lower() for b in blacklist)
    ]

# ------------------------------------------------

# Obtendo todos os IDs das máquinas
computerIDs = get_computer_ids(urlIDs)
if not computerIDs:
    print("Nenhum ID encontrado.")
    exit()

# Para cada ID, obter informações e salvar
for computerID in computerIDs:
    computerInfo = get_computer_info(computerID, urlBase)
    
    if computerIDs:
        folderExist = verify_folder_exist(outputDir)
        
        if folderExist:            
            if verify_folder_is_empty(outputDir):
                fileOld = search_file_for_id(computerID, outputDir)                
                fileNew = save_computer_info(computerID, computerInfo, outputDir)               

                if fileOld and fileNew:
                    softwaresFileOld = get_softwares(outputDir + "/" + fileOld)
                    softwaresFileNew = get_softwares(outputDir + "/" + fileNew)

                    # Aplica blacklist de softwares
                    softwaresFileOld = filter_blacklist(softwaresFileOld, software_blacklist)
                    softwaresFileNew = filter_blacklist(softwaresFileNew, software_blacklist)

                    softwaresDiff = diff_files(softwaresFileOld, softwaresFileNew)
                                        
                    usersFileOld = get_users(outputDir + "/" + fileOld)
                    usersFileNew = get_users(outputDir + "/" + fileNew)
                    
                    usersDiff = diff_files(usersFileOld, usersFileNew)
                    
                    if bool(softwaresDiff) or bool(usersDiff):                        
                        nameAndIp = get_name_and_ip_computer(outputDir + "/" + fileNew)
                        message += f"{nameAndIp}\n"
                                                
                        if bool(softwaresDiff):
                            message += f" - SOFTWARE: {softwaresDiff}\n"                            
                            
                        if bool(usersDiff):
                            message += f" - USER: {usersDiff}\n"
                        
                        message += "---------------------------------------\n"
                    
                    move_file_to_folder(outputDir, folderIventoriado, fileOld)
                    continue
                
            else:                
                fileNew = save_computer_info(computerID, computerInfo, outputDir)
        
        else:
            fileNew = save_computer_info(computerID, computerInfo, outputDir)

if not message:
    message = "Verificação de RSI Feita - Nenhuma alteração encontrada!"

print(message)

# Salva a mensagem como log na área de trabalho
with open("C:/Users/Matheus Gomes/Desktop/inventario_log.txt", "w", encoding="utf-8") as f:
    f.write(message)
