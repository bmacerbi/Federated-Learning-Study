import threading
import sys
from client import main

def runClients(number_of_clients):
    threads = []
    for i in range(number_of_clients):
        thread = threading.Thread(target=main, args=(str(i), ))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()    

if __name__ == '__main__':
    try:
        number_of_clients = int(sys.argv[1])
    except IndexError:
        print("Missing argument! You need to pass: NuberOfClients")
        exit()

    runClients(number_of_clients)
