import argparse
import yaml
import torch
import torch.optim as optim
from torch.utils.data import DataLoader
import mlflow
from ia.modelos.AttentionOutfitGenerator import AttentionOutfitGenerator
from ia.device import DEVICE
from training.dataset import TripletOutfitDataset
from training.perdida import perdida_coseno

def main(config_path):
    '''
    Ejecuta el flujo principal de entrenamiento para el modelo AttentionOutfitGenerator, gestionando la carga de la configuración YAML, la preparación del dataset mediante DataLoader, el bucle de entrenamiento con optimización de tripletas, el registro de métricas en MLflow y el guardado final del modelo.

    Parameters
    ----------
    config_path : str
        Ruta del archivo de configuración en formato YAML que contiene los hiperparámetros del modelo, parámetros de entrenamiento y rutas de archivos.

    Returns
    ----------
    None
    '''

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    mlflow.set_tracking_uri(config["mlflow_uri"])
    mlflow.set_experiment(config["experiment_name"])

    train_dataset = TripletOutfitDataset(config["data_path"])
    train_loader = DataLoader(
        train_dataset, 
        batch_size=config["batch_size"], 
        shuffle=True, 
        num_workers=4 
    )

    device = DEVICE
    print(f"Entrenando en: {device}")
    
    model = AttentionOutfitGenerator(
        hidden_dim=config["hidden_dim"],
        num_heads=config["num_heads"],
        num_layers=config["num_layers"]
    ).to(device)
    
    optimizer = optim.AdamW(model.parameters(), lr=config["learning_rate"])

    with mlflow.start_run():
        mlflow.log_params(config)
        
        for epoch in range(config["num_epochs"]):
            model.train() 
            total_loss = 0.0
            
            for batch_idx, (contexto, positivo, negativo) in enumerate(train_loader):
                positivo = positivo.to(device)
                negativo = negativo.to(device)
                
                history_clips = contexto["history_clips"].to(device)
                target_slot = contexto["target_slot"].to(device)
                tags = contexto["tags"].to(device)
                color = contexto["color"].to(device)
                
                optimizer.zero_grad()
                
                anchor_predicho = model(
                    history_clips=history_clips,
                    target_slot=target_slot,
                    tags=tags,
                    color=color
                )
                
                loss = perdida_coseno(
                    anchor=anchor_predicho, 
                    positive=positivo, 
                    negative=negativo, 
                    margin=config["margin"]
                )
                
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()

            avg_loss = total_loss / len(train_loader)
            print(f"Epoch [{epoch+1}/{config['num_epochs']}] - Triplet Cosine Loss: {avg_loss:.4f}")

            mlflow.log_metric("train_loss", avg_loss, step=epoch)

        mlflow.pytorch.log_model(model, "attention_outfit_generator")
        torch.save(model.state_dict(), f"{config['model_save_path']}/modelo_final.pth")
        print("Entrenamiento completado y modelo guardado.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Entrenar el Generador de Outfits")
    parser.add_argument("--config", type=str, default="training/config.yaml")
    args = parser.parse_args()
    
    main(args.config)