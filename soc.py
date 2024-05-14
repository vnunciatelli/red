import socket
import json
from datetime import datetime
from random import randbytes
import hashlib
import requests
import uuid
import os

csrf = (hashlib.md5(randbytes(32))).hexdigest()
mac_address = uuid.getnode() #nuc
mac_address_hex = ''.join(['{:02x}'.format((mac_address >> elements) & 0xff) for elements in range(0,8*6,8)][::-1]) #nuc
publicIP = '0.0.0.0'
localIP = [(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]

HOST = localIP  # Standard loopback interface address (localhost)
PORT = 55502  # Port to listen on (non-privileged ports are > 1023)

#hdmi_status = 999

def hdmi_status():
    global hdmi_status
    print('[PLATAFORMA IOT]','executando CMD HDMI STATUS ...')
    while True:                        
        cmd1 = bytes.fromhex('ff 55 04 57 01 01 00 b1') ; ack1 = bytes.fromhex('ff 55 04 57 01 01 01 b2') ; ack2 = bytes.fromhex('ff 55 04 57 01 01 00 b1') #STATUS HDMI ON / OFF
        #cmd_ack = conn.recv(BUFFER_SIZE) #RECEBE ACK
        conn.send(cmd1)
        print('>>> Status HDMI:', cmd1, 'aguardando ACK ... ..')
        cmd_ack = conn.recv(1024) #RECEBE ACK
        #print('ACK:',cmd_ack)
        if len(cmd_ack) == 8:
            print('ACK:',cmd_ack)
            if cmd_ack == ack1:
                #print('ACK:',cmd_ack)
                print('hdmi ON')
                hdmi_status = 1
                #time.sleep(2)

            if cmd_ack == ack2:
                #print('ACK:',cmd_ack)
                print('hdmi OFF')
                hdmi_status = 0
                #time.sleep(2)

def pega_artefato():
    try:
        with open("artifact.json", "r") as file:
            global artifact
            artifact = json.load(file)
            print('artifact:',artifact)
    except:
        print('artifact.json NAO encontrado')

def envia_dac():
    print('[PLATAFORMA IOT]','ENVIANDO DADOS PARA O SERVIDOR ... ..')
    p = 'csrf='+(csrf)+'&nucMac='+str(mac_address_hex)+'&artifact='+artifact+'&localIP='+localIP+'&rmcIP='+clientIP+'&data='+dados+'&timestamp='+hora_certa+'&hdmi_status='+str(hdmi_status)+'&rmcMac='+mac_rmc    
    purl = 'https://boe-php.eletromidia.com.br/rmc/nuc/unpaserd'
    h = {'Content-Type': 'application/x-www-form-urlencoded'}
    r = requests.request('POST', purl, headers = h, data = p)
    print(r.headers)
    print(r.text)
    print(p)
    print('PLATAFORMA IOT]','HTTP STATUS RESPONSE >>>',r.status_code)

def dac():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, PORT))
            print('bind')
            s.listen()
            print('listen')
            s.settimeout(10)
            global conn
            conn, addr = s.accept()
            global clientIP
            clientIP = addr[0]
            print('accept')
            with conn:
                hdmi_status()
                global hora_certa
                global dados
                print(f"Connected by {addr}")
                #data = conn.recv(1024)
                hora_certa = datetime.now().strftime('%Y/%m/%d %H:%M')
                print('procurando INFOS...',hora_certa)
                while True:               
                    data = conn.recv(1024)   
                    if (len(data)==91 and data[3]==32):
                        hora_certa = datetime.now().strftime('%Y/%m/%d %H:%M')
                        print(hora_certa)
                        print('len:',len(data))                
                        print('data:',(data))
                        firmware = data[6:16].decode("utf-8")
                        print('firmware:',firmware)
                        global mac_rmc
                        mac_rmc = data[16:22].hex()
                        print('mac_rmc:',mac_rmc)
                        placaRMC = data[22:28].decode("utf-8")
                        print('placaRMC:',placaRMC)        
                        placaFAN = data[38:60].decode("utf-8")
                        print('placaFAN:', placaFAN)
                        placaADBOARD = data[79:87].decode("utf-8")
                        print('placaADBOARD:',placaADBOARD)
                        dados = ('infos'+';'+str(firmware)+';'+(mac_rmc)+';'+str(placaRMC)+';'+str(placaFAN)+';'+str(placaADBOARD))
                        envia_dac()
                        break
                    #print('len:',len(data),'procurando INFOS...',hora_certa) 

                hora_certa = datetime.now().strftime('%Y/%m/%d %H:%M')
                print('procurando TYPES...',hora_certa)
                #data = conn.recv(1024)
                while True: 
                    data = conn.recv(1024) 
                    if (len(data)==528 and data[3]==16 and data[5]==1):
                        hora_certa = datetime.now().strftime('%Y/%m/%d %H:%M')
                        print(hora_certa)
                        print('len:',len(data))
                        print('data:',(data))
                        dados = ('types'+';'+data.hex())
                        envia_dac()
                        break
                    #print('len:',len(data),'procurando TYPES...',hora_certa) 

                hora_certa = datetime.now().strftime('%Y/%m/%d %H:%M')
                print('procurando HOT BIT...',hora_certa)
                #data = conn.recv(1024) 
                while True: 
                    data = conn.recv(13)                                        
                    if (len(data)==13 and data[0]==255 and data[1]==85 and data[2]==7):
                        hora_certa = datetime.now().strftime('%Y/%m/%d %H:%M')
                        print(hora_certa)
                        print('len:',len(data))
                        print('data:',(data))
                        dados = ('hotBit'+';'+data.hex())
                        envia_dac()
                        break

                hora_certa = datetime.now().strftime('%Y/%m/%d %H:%M')
                print('procurando RESUMO...',hora_certa)
                #data = conn.recv(64)
                while True: 
                    data = conn.recv(1024) 
                    if (len(data)>=63 and data[3]==64):
                        hora_certa = datetime.now().strftime('%Y/%m/%d %H:%M')
                        print(hora_certa)
                        print('len:',len(data))
                        #print('data[0]:',(data[0]))
                        print('data:',(data))
                        dados = ('resumo'+';'+data.hex())
                        envia_dac()
                        break
                    #print('len:',len(data),data,'procurando RESUMO...',hora_certa)                                           
                            
                    if not data:
                        print('no data today')
                        break
        print('achou tudo')
        try:
            os.system('taskkill /IM soc.exe /F')
        except:
            print('NOT windowns')
    except:
        try:
            print('falha SOC')
            clientIP = '0'
            dados = 'falhaRMC'
            hora_certa = datetime.now().strftime('%Y/%m/%d %H:%M')
            hdmi_status = 'err'
            mac_rmc = '0'
            envia_dac()
        except:
            print('system failure')
        try:
            os.system('taskkill /IM soc.exe /F')
        except:
            print('NOT windowns')

pega_artefato()
dac()