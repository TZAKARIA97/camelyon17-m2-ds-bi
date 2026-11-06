"""Contrôles tensoriels optionnels sur bruit aléatoire ; aucun score clinique."""
import importlib.util
import unittest
import numpy as np
import tempfile
import json
import sys
from pathlib import Path
from unittest.mock import patch

AVAILABLE = all(importlib.util.find_spec(name) is not None for name in ('torch', 'torchvision'))


@unittest.skipUnless(AVAILABLE, 'PyTorch/torchvision non installés')
class TensorTests(unittest.TestCase):
    def test_training_checkpoint_evaluation_roundtrip(self):
        """Tester l'orchestration sur bruit, sans téléchargement de poids ImageNet."""
        import torch
        import pandas as pd
        from PIL import Image
        from src.models.train import main as train_main
        from src.evaluation.evaluate import main as evaluate_main
        torch.set_num_threads(2)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rows = []
            rng = np.random.default_rng(42)
            for split, center in [('train', '0'), ('val', '1'), ('test', '2')]:
                for i in range(4):
                    path = root / f'{split}_{i}.png'
                    Image.fromarray(rng.integers(0, 256, (96, 96, 3), dtype=np.uint8)).save(path)
                    rows.append(dict(path=str(path), patient_id=f'{split}_{i}',
                                     slide_id=f'{split}_{i}', center_id=center,
                                     label=i % 2, split=split, source='synthetic'))
            manifest = root / 'manifest.csv'
            pd.DataFrame(rows).to_csv(manifest, index=False)
            config = json.loads(Path('configs/baseline.json').read_text())
            config['epochs'] = 1
            config['batch_size'] = 2
            config_path = root/'config.json'
            config_path.write_text(json.dumps(config))
            train_main(['--manifest', str(manifest), '--config', str(config_path),
                        '--out', str(root/'run'), '--demo'])
            evaluate_main(['--manifest', str(manifest), '--checkpoint', str(root/'run/best.pt'),
                           '--split', 'test', '--out', str(root/'eval')])
            result = json.loads((root/'eval/metrics.json').read_text())
            self.assertEqual(result['overall']['n'], 4)
            self.assertEqual(result['dataset_kind'], 'synthetic')
            self.assertEqual(len(pd.read_csv(root/'eval/predictions.csv')), 4)
            config_saved = json.loads((root/'run/config.json').read_text())
            self.assertEqual(config_saved['initial_weights'], 'random')
            # Un résultat modifié ne doit plus pouvoir produire un rapport présenté comme traçable.
            from src.visualization.report import load_evaluation
            load_evaluation(root/'eval')
            with (root/'eval/predictions.csv').open('a') as stream:
                stream.write('\n')
            with self.assertRaisesRegex(ValueError, 'changé'):
                load_evaluation(root/'eval')
            from src.models.inference import load_run
            manifest.write_text(manifest.read_text() + '\n')
            with self.assertRaisesRegex(ValueError, 'Manifeste différent'):
                load_run(root/'run/best.pt', manifest)

    def test_frozen_model_gradcam(self):
        import torch
        from torchvision.models import resnet18
        from src.visualization.gradcam import gradcam
        torch.set_num_threads(2)
        torch.manual_seed(42)
        model = resnet18(weights=None)
        for p in model.parameters():
            p.requires_grad = False
        model.fc = torch.nn.Linear(model.fc.in_features, 2)
        image = torch.randn(1, 3, 96, 96)
        result = gradcam(model, image)
        self.assertEqual(result.shape, (96, 96))
        self.assertTrue(np.isfinite(result).all())
        self.assertTrue(((result >= 0) & (result <= 1.000001)).all())
        self.assertEqual(len(model.layer4._forward_hooks), 0)

    def test_forward_backward_and_transform(self):
        import torch
        from PIL import Image
        from torchvision.models import resnet18, ResNet18_Weights
        from src.models.train import transforms_for
        torch.set_num_threads(2)
        transform = transforms_for(96, ResNet18_Weights.DEFAULT)
        image = transform(Image.fromarray(np.zeros((96, 96, 3), dtype=np.uint8)))
        self.assertEqual(tuple(image.shape), (3, 96, 96))
        model = resnet18(weights=None)
        model.fc = torch.nn.Linear(model.fc.in_features, 2)
        model.eval()
        loss = torch.nn.functional.cross_entropy(model(image.repeat(2, 1, 1, 1)), torch.tensor([0, 1]))
        loss.backward()
        self.assertTrue(torch.isfinite(loss))
        self.assertIsNotNone(model.fc.weight.grad)
