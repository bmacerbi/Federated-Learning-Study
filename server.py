import sys
import grpc
import fed_grpc_pb2
import fed_grpc_pb2_grpc
import threading
from concurrent import futures
import aux
from queue import Queue

class FedServer(fed_grpc_pb2_grpc.FederatedServiceServicer):
    def __init__(self):
        self.clients = {}
        self.round = 0
        self.global_weights = []
        self.clients_models = {}
        self.reliability = {}
        self.k = 4 ##
        self.variation = 1.0/self.k

    # Envia round atual para todos os clientes
    def __sendRound(self):
        for cid in self.clients:
            channel = grpc.insecure_channel(self.clients[cid])
            client = fed_grpc_pb2_grpc.FederatedServiceStub(channel)

            client.sendRound(fed_grpc_pb2.currentRound(round = (self.round)))

    # Inicia treinamento de determinado clientes
    def __callClientLearning(self, cid, q):
        channel = grpc.insecure_channel(self.clients[cid])
        client = fed_grpc_pb2_grpc.FederatedServiceStub(channel)

        weight_list = client.startLearning(fed_grpc_pb2.void()).weight
        sample_size = client.getSampleSize(fed_grpc_pb2.void()).size

        q.put([weight_list, sample_size, cid])

    # Teste para nova lista de pesos global
    def __callModelValidation(self):
        acc_list = []
        for cid in self.clients:
            channel = grpc.insecure_channel(self.clients[cid])

            client = fed_grpc_pb2_grpc.FederatedServiceStub(channel)
            acc_list.append(client.modelValidation(fed_grpc_pb2.weightList(weight = (self.global_weights))).acc)

        return acc_list
    
    def __modelsDistances(self):
        distance_list = {}
        for cid in self.clients_models:
            distance_list[cid] = aux.euclidean_distances(self.global_weights, self.clients_models[cid]["weights"])
        return distance_list
    
    def __classifieDistance(self, lower_limit, upper_limit, client_distance):
        outlier_cid = []
        not_outlier = []
        for cid in client_distance:
            if client_distance[cid] < lower_limit or client_distance[cid] > upper_limit:
                outlier_cid.append(cid)
            else:
                not_outlier.append(cid)
        return outlier_cid, not_outlier
    
    def __decreaseReliability(self, outliers):
        for cid in outliers:
            print(f"Removing credibility from client CID {cid}")
            self.reliability[cid] -= self.variation 
            if self.reliability[cid] == 0:
                if output_file_exclusions:
                    with open(output_file_exclusions, 'a') as f:
                        f.write(f'{cid}, {self.round}\n')
                print(f"CID {cid} lost all the credibility / Removing from available clients...")
                self.clients_models.pop(cid)
                client_ip = self.clients.pop(cid)
                self.__killClient(client_ip)


    def __increaseReliability(self, not_outliers):
        for cid in not_outliers:
            if self.reliability[cid] != 1:
                print(f"Incrising credibillity from client CID {cid}")
                self.reliability[cid] += self.variation

    def __handleOutliers(self):
        client_distance = self.__modelsDistances()
        lower_limit, upper_limit = aux.inter_quarlite_rage_limits(list(client_distance.values()))
        outliers, not_outliers = self.__classifieDistance(lower_limit, upper_limit, client_distance)
        self.__decreaseReliability(outliers)
        self.__increaseReliability(not_outliers)

    def __fedAvg(self):
        if len(self.global_weights) != 0:
            self.__handleOutliers()

        self.global_weights = []
        #Itercao por todos os pesos de uma lista específica
        for j in range(len(self.clients_models[next(iter(self.clients_models))]["weights"])):
            element = 0.0
            sample_sum = 0.0
            #Iteracao para todos os clientes presentes
            for cid in self.clients_models:
                sample_sum += self.clients_models[cid]["sample_size"] * self.reliability[cid]
                element += self.clients_models[cid]["weights"][j] * self.clients_models[cid]["sample_size"] * self.reliability[cid]
            
            self.global_weights.append(element/sample_sum)
        
    # Encerra estado de wait_for_termination dos clients
    def killClients(self):
        for cid in self.clients:
            self.__killClient(self.clients[cid])

    def __killClient(self, client_ip):
        try:
            channel = grpc.insecure_channel(client_ip)
            client = fed_grpc_pb2_grpc.FederatedServiceStub(channel)
            client.killClient(fed_grpc_pb2.void())
        except grpc.RpcError as e:
            print(f"Error killing client at {client_ip}: {e}")

    def clientRegister(self, request, context):
        ip = request.ip
        port = request.port
        cid = int(request.cid)

        if cid in self.clients:
            print(f"Could not register Client with ID {cid} - Duplicated Id")
            return fed_grpc_pb2.registerOut(connectedClient = (False), round = (self.round))
        
        self.clients[cid] = ip + ":" + port
        self.reliability[cid] = 1.0
        print(f"Client {cid} registered!")
        return fed_grpc_pb2.registerOut(connectedClient = (True), round = (self.round))
    
    def startServer(self, n_round_clients, min_clients, max_rounds):
        #Verificando se o mínimo de clientes foi estabelecido
        if len(self.clients) < min_clients:
            print("Waiting for the minimum number of clients to connect...")
            while len(self.clients) < min_clients:
                continue

            print("The minimum number of clients has been reached.")

        while self.round < max_rounds:           
            self.round += 1
            self.__sendRound()

            # Criando lista de clientes alvo
            ## Tratando caso de cliente ser removido
            if n_round_clients > len(self.clients):
                n_round_clients = len(self.clients)
            cid_targets = aux.createRandomClientList(self.clients, n_round_clients)

            # Inicializando chamada de aprendizado para os clients
            print(f"Round: {self.round}")
            thread_list = []
            q = Queue()
            for i in range(n_round_clients):
                thread = threading.Thread(target=self.__callClientLearning, args=(cid_targets[i], q))
                thread_list.append(thread)
                thread.start()
            for thread in thread_list:
                thread.join()

            # Capturando os resultados de treinamento de todos os clients
            self.clients_models = {}
            while not q.empty():
                thread_results = q.get()
                self.clients_models[thread_results[2]] = {
                    "weights": thread_results[0],
                    "sample_size": thread_results[1],
                }

            # Agregando lista de pesos
            self.__fedAvg()

            # Validando o modelo global
            acc_list = self.__callModelValidation()
            acc_global = sum(acc_list)/len(acc_list)

            if output_file_accuracy:
                with open(output_file_accuracy, 'a') as f:
                    f.write(f'{acc_global}\n')

if __name__ == "__main__":
    global output_file_accuracy
    global output_file_exclusions

    output_file_accuracy = 'testes/cifar/nonIdd/coord/10infected'
    output_file_exclusions = 'testes/cifar/nonIdd/coord/10infectedEx'

    try:
        n_round_clients = int(sys.argv[1])
        min_clients = int(sys.argv[2])
        max_rounds = int(sys.argv[3])

    except IndexError:
        print("Missing argument! You need to pass: [clientsRound, minClients, maxRounds]")
        exit()

    fed_server = FedServer()

    #creating grpc server at ip [::]:8080
    grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    fed_grpc_pb2_grpc.add_FederatedServiceServicer_to_server(fed_server, grpc_server)
    grpc_server.add_insecure_port('[::]:8080')
    grpc_server.start()

    fed_server.startServer(n_round_clients, min_clients, max_rounds)
    fed_server.killClients()