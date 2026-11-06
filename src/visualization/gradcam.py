"""Grad-CAM pour ResNet18 ; à commenter sur les succès ET les erreurs."""


def gradcam(model, image_batch, target_class=1):
    """Retourner une carte 0..1 pour une seule image BCHW prétraitée.

    Les gradients restent activés même avec un backbone gelé. La carte montre
    une contribution au score, pas une segmentation ni une validation clinique.
    """
    import torch
    import torch.nn.functional as F
    if image_batch.ndim != 4 or image_batch.shape[0] != 1:
        raise ValueError('Une seule image BCHW attendue.')
    saved = {}
    def capture(_module, _inputs, output):
        saved['activation'] = output
    handle = model.layer4.register_forward_hook(capture)
    was_training = model.training
    try:
        model.eval()
        with torch.enable_grad():
            image = image_batch.detach().requires_grad_(True)
            output = model(image)
            activation = saved['activation']
            gradients = torch.autograd.grad(output[:, target_class].sum(), activation)[0]
            cam = (activation * gradients.mean((2, 3), keepdim=True)).sum(1, keepdim=True).relu()
            cam = F.interpolate(cam, image.shape[-2:], mode='bilinear', align_corners=False)
            maximum = cam.amax((2, 3), keepdim=True)
            cam = cam / maximum.clamp_min(1e-12)
            return cam[0, 0].detach().cpu().numpy()
    finally:
        handle.remove()
        model.train(was_training)
