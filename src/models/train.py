"""Baseline ResNet18 gelé ou fine-tuning partiel ; sélection sur validation uniquement."""
import argparse
import json
import random
import subprocess
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd
from PIL import Image
from ..data.audit import read_manifest, audit
from ..evaluation.metrics import binary_metrics
from ..provenance import sha256_file, code_version


def validate_config(config):
    """Refuser une configuration incohérente avant tout chargement de poids."""
    if config.get('model') != 'resnet18':
        raise ValueError('Seul resnet18 est implémenté.')
    for key, minimum in [('epochs', 1), ('batch_size', 1), ('image_size', 32),
                         ('num_workers', 0), ('seed', 0)]:
        value = config.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
            raise ValueError(f'Configuration invalide : {key}.')
    if config['seed'] > 2**32 - 1:
        raise ValueError('seed doit tenir dans un entier non signé 32 bits.')
    for key in ('fine_tune', 'class_weighted_loss'):
        if not isinstance(config.get(key), bool):
            raise ValueError(f'{key} doit être un booléen JSON.')
    for key in ('learning_rate', 'threshold'):
        value = config.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not np.isfinite(value):
            raise ValueError(f'Configuration invalide : {key}.')
    if config['learning_rate'] <= 0 or not 0 <= config['threshold'] <= 1:
        raise ValueError('learning_rate doit être positif ; threshold doit être dans [0,1].')
    if config.get('selection_split') not in {'val', 'id_val'}:
        raise ValueError('Sélection autorisée sur val ou id_val uniquement.')


def transforms_for(size, weights):
    """Redimensionner sans crop aléatoire : le label WILDS porte sur le centre."""
    from torchvision import transforms
    preprocessing = weights.transforms()
    return transforms.Compose([
        transforms.Resize((size, size)), transforms.ToTensor(),
        transforms.Normalize(mean=preprocessing.mean, std=preprocessing.std)
    ])


class PatchDataset:
    """Chaque ligne lie une image à son label et à son groupe d'origine."""
    def __init__(self, frame, transform):
        self.frame = frame.reset_index(drop=True)
        self.transform = transform

    def __len__(self):
        return len(self.frame)

    def __getitem__(self, index):
        row = self.frame.iloc[index]
        with Image.open(row.path) as image:
            image = self.transform(image.convert('RGB'))
        return image, int(row.label)


def predict(model, loader, device):
    """Conserver l'ordre du DataLoader pour rattacher les scores au manifeste."""
    import torch
    labels, scores = [], []
    model.eval()
    with torch.no_grad():
        for x, y in loader:
            scores.extend(model(x.to(device)).softmax(1)[:, 1].cpu().tolist())
            labels.extend(y.tolist())
    return labels, scores


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--config', default='configs/baseline.json')
    parser.add_argument('--out', required=True, help='Dossier nouveau pour chaque expérience')
    parser.add_argument('--demo', action='store_true',
                        help='Poids aléatoires, CPU : exige source=synthetic sur toutes les lignes')
    args = parser.parse_args(argv)
    out = Path(args.out)
    if out.exists():
        raise FileExistsError(f'Le dossier de sortie existe déjà : {out}')
    frame = read_manifest(args.manifest)
    audit(frame, check_files=True)
    config = json.loads(Path(args.config).read_text(encoding='utf-8'))
    validate_config(config)
    synthetic = 'source' in frame and (frame.source == 'synthetic').all()
    if args.demo != synthetic or ('source' in frame and (frame.source == 'synthetic').any() and not synthetic):
        raise ValueError('--demo exige un manifeste entièrement synthetic ; pas de mélange réel/synthétique.')
    selection = config['selection_split']
    train = frame[frame.split == 'train']
    validation = frame[frame.split == selection]
    if set(train.label) != {'0', '1'} or set(validation.label) != {'0', '1'}:
        raise ValueError('Train et validation doivent contenir les deux classes.')
    import torch
    from torch.utils.data import DataLoader
    from torchvision.models import resnet18, ResNet18_Weights
    seed = int(config['seed'])
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    device = 'cpu' if args.demo else ('cuda' if torch.cuda.is_available() else 'cpu')
    if args.demo:
        torch.set_num_threads(2)
    # Version explicite : DEFAULT pourrait évoluer avec une prochaine torchvision.
    weights = ResNet18_Weights.IMAGENET1K_V1
    transform = transforms_for(config['image_size'], weights)
    generator = torch.Generator().manual_seed(seed)
    loader = DataLoader(PatchDataset(train, transform), batch_size=config['batch_size'],
                        shuffle=True, generator=generator, num_workers=config['num_workers'])
    val_loader = DataLoader(PatchDataset(validation, transform), batch_size=config['batch_size'],
                            shuffle=False, num_workers=config['num_workers'])
    model = resnet18(weights=None if args.demo else weights)
    for parameter in model.parameters():
        parameter.requires_grad = False
    model.fc = torch.nn.Linear(model.fc.in_features, 2)
    if config['fine_tune']:
        for parameter in model.layer4.parameters():
            parameter.requires_grad = True
    model.to(device)
    class_weights = None
    if config['class_weighted_loss']:
        counts = train.label.value_counts()
        class_weights = torch.tensor([len(train)/(2*counts[str(c)]) for c in (0, 1)],
                                     dtype=torch.float32, device=device)
    loss_fn = torch.nn.CrossEntropyLoss(weight=class_weights)
    optimizer = torch.optim.Adam((p for p in model.parameters() if p.requires_grad),
                                 lr=config['learning_rate'])
    out.mkdir(parents=True, exist_ok=False)
    config['device'] = device
    config['manifest_sha256'] = sha256_file(args.manifest)
    config['initial_weights'] = 'random' if args.demo else weights.name
    config['normalization_weights'] = weights.name
    config['dataset_kind'] = 'synthetic' if args.demo else 'provided_not_clinically_validated'
    config['code_version'] = code_version()
    config['selection_metric'] = 'average_precision'
    config['split_sizes'] = frame.groupby('split').size().astype(int).to_dict()
    (out / 'config.json').write_text(json.dumps(config, indent=2), encoding='utf-8')
    freeze = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze'], text=True)
    (out / 'environment.txt').write_text(freeze, encoding='utf-8')
    history, best = [], -1.0
    start = time.perf_counter()
    for epoch in range(config['epochs']):
        # eval garde les BatchNorm gelées : leurs statistiques ne doivent pas apprendre en cachette.
        model.eval()
        model.fc.train()
        if config['fine_tune']:
            model.layer4.train()
        total_loss = 0.0
        for x, y in loader:
            optimizer.zero_grad()
            loss = loss_fn(model(x.to(device)), y.to(device))
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * len(y)
        labels, scores = predict(model, val_loader, device)
        metrics = binary_metrics(labels, scores, config['threshold'])
        metrics.update(epoch=epoch+1, train_loss=total_loss/len(train))
        history.append(metrics)
        print(json.dumps(metrics))
        # AP choisie à l'avance. Les images test ne sont jamais chargées ici.
        if metrics['average_precision'] > best:
            best = metrics['average_precision']
            torch.save({'model': model.state_dict(), 'config': config,
                        'epoch': epoch+1, 'validation_ap': best}, out / 'best.pt')
        pd.DataFrame(history).to_csv(out / 'history.csv', index=False)
    print('Entraînement terminé ; test final séparé, après gel du protocole.')
    summary = {'elapsed_seconds': time.perf_counter() - start, 'best_validation_ap': best,
               'dataset_kind': config['dataset_kind'], 'epochs_run': len(history)}
    (out / 'training_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
