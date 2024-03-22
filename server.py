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
        self.aggregated_weights = []

    # Envia round atual para todos os clientes
    def __sendRound(self):
        for cid in self.clients:
            channel = grpc.insecure_channel(self.clients[cid])
            client = fed_grpc_pb2_grpc.FederatedServiceStub(channel)

            client.sendRound(fed_grpc_pb2.currentRound(round = (self.round)))

    # Inicia treinamento de determinado clientes
    def __callClientLearning(self, client_ip, q):
        channel = grpc.insecure_channel(client_ip)
        client = fed_grpc_pb2_grpc.FederatedServiceStub(channel)

        weight_list = client.startLearning(fed_grpc_pb2.void()).weight
        sample_size = client.getSampleSize(fed_grpc_pb2.void()).size

        q.put([weight_list, sample_size])

    # Teste para nova lista de pesos global
    def __callModelValidation(self):
        acc_list = []
        for cid in self.clients:
            channel = grpc.insecure_channel(self.clients[cid])

            client = fed_grpc_pb2_grpc.FederatedServiceStub(channel)
            acc_list.append(client.modelValidation(fed_grpc_pb2.weightList(weight = (self.aggregated_weights))).acc)

        return acc_list
    
    def __modelsDistances(self, n_clients, weights_clients_list):
        distance_list = []
        for i in range(n_clients):
            distance_list.append(aux.euclidean_distances(self.aggregated_weights, weights_clients_list[i]))
        return distance_list
    
    def __identifyDistanceOutliers(self, lower_limit, upper_limit, distance_list):
        outlier_cid = []
        for i in range(len(distance_list)):
            if distance_list[i] < lower_limit or distance_list[i] > upper_limit:
                print(f"Outlier detected: CID {i}")
                outlier_cid.append(i)
        return outlier_cid 

    # Calcula a média ponderada dos pesos resultantes do treino
    ## Proposta: Adicionar camada para deteceção de outliers e reduzir o impacto de modelos distantes
    ## Ideia: Manter um vetor local com uma "confiabilidade" para cada cliente
    def __FedAvg(self, n_clients, weights_clients_list, sample_size_list):
        if len(self.aggregated_weights) != 0:
            distance_list = self.__modelsDistances(n_clients, weights_clients_list)
            lower_limit, upper_limit = aux.inter_quarlite_rage_limits(distance_list)
            outliers_cid = self.__identifyDistanceOutliers(lower_limit, upper_limit, distance_list)

        self.aggregated_weights = []
        #Itercao por todos os pesos de uma lista específica
        for j in range(len(weights_clients_list[0])):
            element = 0.0
            sample_sum = 0.0
            #Iteracao para todos os clientes presentes
            for i in range(n_clients):
                sample_sum += sample_size_list[i]
                element += weights_clients_list[i][j] * sample_size_list[i]
            self.aggregated_weights.append(element/sample_sum)
        
    # Encerra estado de wait_for_termination dos clients
    def killClients(self):
        for cid in self.clients:
            channel = grpc.insecure_channel(self.clients[cid])

            client = fed_grpc_pb2_grpc.FederatedServiceStub(channel)
            client.killClient(fed_grpc_pb2.void())

    def clientRegister(self, request, context):
        ip = request.ip
        port = request.port
        cid = int(request.cid)

        if cid in self.clients:
            print(f"Could not register Client with ID {cid} - Duplicated Id")
            return fed_grpc_pb2.registerOut(connectedClient = (False), round = (self.round))
        
        self.clients[cid] = ip + ":" + port
        print(f"Client {cid} registered!")
        return fed_grpc_pb2.registerOut(connectedClient = (True), round = (self.round))
    
    def startServer(self, n_round_clients, min_clients, max_rounds):
        while self.round < max_rounds:
            #Verificando se o mínimo de clientes foi estabelecido
            if len(self.clients) < min_clients:
                print("Waiting for the minimum number of clients to connect...")
                while len(self.clients) < min_clients:
                    continue

                print("The minimum number of clients has been reached.")
            
            self.round += 1
            self.__sendRound()

            # Criando lista de clientes alvo
            cid_targets = aux.createRandomClientList(self.clients, n_round_clients)

            # Inicializando chamada de aprendizado para os clients
            thread_list = []
            q = Queue()
            for i in range(n_round_clients):
                thread = threading.Thread(target=self.__callClientLearning, args=(self.clients[cid_targets[i]], q))
                thread_list.append(thread)
                thread.start()
            for thread in thread_list:
                thread.join()

            # Capturando lista de pesos resultantes do treinamento
            weights_clients_list = []
            sample_size_list = []
            while not q.empty():
                thread_results = q.get()

                weights_clients_list.append(thread_results[0])
                sample_size_list.append(thread_results[1])

            # Agregando lista de pesos
            self.__FedAvg(n_round_clients, weights_clients_list, sample_size_list)

            # Validando o modelo global
            acc_list = self.__callModelValidation()
    
            acc_global = sum(acc_list)/len(acc_list)
            print(f"Round: {self.round} / Accuracy Mean: {acc_global}")

if __name__ == "__main__":
    try:
        n_round_clients = 3
        min_clients = 3
        max_rounds = 4

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