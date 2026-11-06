"""Recharger un modèle et son prétraitement sans retélécharger ImageNet."""
from pathlib import Path
from ..provenance import sha256_file


def load_run(checkpoint_path, manifest_path):
    import torch
    from torchvision.models import resnet18, ResNet18_Weights
    from .train import transforms_for
    # N'ouvrir que les checkpoints produits par le projet ou une source fiable.
    checkpoint = torch.load(checkpoint_path, map_location='cpu', weights_only=True)
    config = checkpoint['config']
    if sha256_file(manifest_path) != config['manifest_sha256']:
        raise ValueError('Manifeste différent de celui de l’entraînement : vérifier la provenance.')
    model = resnet18(weights=None)
    model.fc = torch.nn.Linear(model.fc.in_features, 2)
    model.load_state_dict(checkpoint['model'])
    weights = getattr(ResNet18_Weights, config['normalization_weights'])
    transform = transforms_for(config['image_size'], weights)
    model.eval()
    return model, transform, config
