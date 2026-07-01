import mlflow
import random
import time

# host de azure
mlflow.set_tracking_uri("azureml://swedencentral.api.azureml.ms/mlflow/v1.0/subscriptions/4773c19c-c549-42a0-9cc6-82fc2fd8077f/resourceGroups/TFM/providers/Microsoft.MachineLearningServices/workspaces/FashionCLIP")

# nombramos el exp
mlflow.set_experiment("prueba-conexion-fashionclip")

print("Iniciando el registro en MLflow...")

# abrimos la conexion
with mlflow.start_run():
    # parametros
    mlflow.log_param("modelo", "FashionCLIP_Simulado")
    mlflow.log_param("batch_size", 32)
    mlflow.log_param("dataset_size", 3000)
    
    # simulamos 3 epochs
    for epoch in range(1, 4):
        print(f'Simulando epoch {epoch}')
        
        # inventamos valore de perdida
        simulated_loss = random.uniform(0.5, 1.5) / epoch 
        
        # registramos la metrica
        mlflow.log_metric("loss", simulated_loss, step=epoch)
        time.sleep(1) # esperamos 1s para simular calculo
        
print("¡Prueba finalizada! Ya puedes ir a revisar el panel.")
