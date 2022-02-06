import socket
import pickle
s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((socket.gethostname(), 47))
print(socket.gethostname())
s.listen(5)
import sqlite3

while True:
    clt, addr = s.accept()
    print("Connection is established with", addr)

    try:
        # try connecting to database
        conn = sqlite3.connect('productivity.sqlite')
        cur = conn.cursor()
        tosend = 'proceed'
        clt.send(bytes(tosend,"utf-8"))
    except:
        tosend = 'busy'
        clt.send(bytes(tosend,"utf-8"))
        clt.close()
        # continue to listen for connections
        continue

    while(True):
        encoded = clt.recv(1024)
        string_command = encoded.decode("utf-8")
        print('got')
        print(string_command)
        if(string_command == 'done'):
            print('closing connection with current client')
            break

        else:
            try:
                cur.execute(string_command)
                conn.commit()
                result = cur.fetchall()
                tosend = 'success'
                clt.send(bytes(tosend,"utf-8"))

            except:
                tosend = 'error'
                clt.send(bytes(tosend,"utf-8"))
                clt.close()
                exit()

            # receive ok response from client
            encoded = clt.recv(1024)

            data=pickle.dumps(result)
            print('data size:',len(data))

            data_size = str(len(data))
            clt.send(bytes(data_size,"utf-8"))

            # receive ok response from client
            encoded = clt.recv(1024)

            clt.send(data)

    clt.close()
