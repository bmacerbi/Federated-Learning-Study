# Estudo de Ataques de Envenenamento em Aprendizado Federado

Este projeto investiga os danos causados por ataques de envenenamento em redes de aprendizado federado e propõe um algoritmo para mitigar esses danos.  
A descrição completa do algoritmo e os resultados estão na **monografia**; aqui, a documentação foca no uso dos scripts do experimento.

---

## Ambiente de Aprendizado Federado

O ambiente foi construído utilizando **gRPC** para a comunicação entre os processos `client.py` e `server.py`.  
O contexto inicial pode ser visualizado no repositório original:  
[https://github.com/bmacerbi/FederatedLearning_Implementation](https://github.com/bmacerbi/FederatedLearning_Implementation)  

---

## Preparação das Bases de Dados
Scripts disponíveis para criar as partições por cliente:

- `getCifarData.py`  
- `getCifarDataNonIid.py`  
- `getMnistData.py`  
- `getMnistDataNonIid.py`

Para gerar os dados, execute o script desejado informando a quantidade de clientes.  
Exemplo:  
```
python3 getMnistData.py 100
```
---

## Flipagem de Rótulos
Script para alterar rótulos dos dados (**label flipping**):  
```
python labelFlipScript.py base_directory num_clients use_coordinate  
```

> **Observação:** `base_directory` deve ser `cifar10_data` ou `mnist_data`.

---

## Inicializando o Servidor
Inicie o servidor passando os parâmetros de cliente por round, número mínimo de clientes e máximo de rounds
```
python server.py clientsRound minClients maxRounds  
```

Exemplo:  
```
python server.py 5 5 100
```
---

## Inicializando os Clientes
Antes de iniciar, ajuste a **linha 92** do `client.py` definindo o dataset (`cifar10` ou `mnist`).  

Formas de inicialização:

1. **Manual**  
   Executar cada cliente individualmente:  
   ```
   python client.py ClientId  
   ```
   > O `ClientId` deve corresponder a um diretório de dados existente para o cliente.

2. **Script Bash (`runClient.sh`)**  
   Cria *N* terminais e executa automaticamente cada cliente:  
   ```
   ./runClient.sh num_clients  
   ```

3. **Threads (`runThreadsClient.py`)**  
   Instancia *N* threads para criar vários clientes no mesmo terminal:  
   ```
   python runThreadsClient.py num_clients
   ```
