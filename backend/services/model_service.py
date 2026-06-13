import io
import os
import warnings
from typing import Tuple

import cv2
import numpy as np
import torch
import torch.nn as nn
from PIL import Image, ImageOps

import segmentation_models_pytorch as smp

warnings.filterwarnings("ignore")


# =============================================================================
# Fallback model — used when checkpoint is missing
# =============================================================================
class FallbackColorizationModel(nn.Module):
    def __init__(self):
        super().__init__()

    def forward(self, x):
        # x is the L-channel-as-3ch input: (B, 3, H, W)
        b, _, h, w = x.shape
        # Output ab in [0,1] centered at 0.5 (= grayscale in this convention)
        return torch.full((b, 2, h, w), 0.5, dtype=x.dtype, device=x.device)


# =============================================================================
# Model architecture — must match the notebook EXACTLY
#   UNet + EfficientNet-b3 encoder
#   in_channels = 3   (L channel replicated to 3 channels)
#   classes     = 2   (a, b)
#   activation  = sigmoid       → outputs in [0, 1]
#   decoder_attention_type = scse
# =============================================================================
class ColorizationModel(nn.Module):
    """
    UNet + EfficientNet-b3 encoder
    Input  : L channel ×3  → (B, 3, H, W)   in [0, 1]
    Output : ab channels   → (B, 2, H, W)   in [0, 1]
    """

    def __init__(
        self,
        encoder_name: str = "efficientnet-b3",
        encoder_weights: str = None,   # None at inference — weights come from checkpoint
    ):
        super().__init__()
        self.unet = smp.Unet(
            encoder_name=encoder_name,
            encoder_weights=encoder_weights,
            in_channels=3,
            classes=2,
            activation="sigmoid",
            decoder_attention_type="scse",
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.unet(x)


# =============================================================================
# ModelService — backend wrapper
# =============================================================================
class ModelService:
    """
    Inference wrapper for the notebook's UNet colorization model.

    LAB convention used (matches training notebook):
        L  ∈ [0, 1]    = lab_L / 100
        ab ∈ [0, 1]    = (lab_ab + 128) / 255
    Image size: 256 × 256.
    """

    IMAGE_SIZE = 256
    ENCODER    = "efficientnet-b3"

    def __init__(self, checkpoint_path: str, device: str = "cpu"):
        self.device          = torch.device(device)
        self.checkpoint_path = checkpoint_path
        self.model           = self._load_model()

    # ---------------------------------------------------------------- internal
    def _load_model(self) -> nn.Module:
        print("checkpoint_path =", self.checkpoint_path, flush=True)

        if not os.path.exists(self.checkpoint_path):
            print("⚠️ MODEL NOT FOUND → FALLBACK", flush=True)
            model = FallbackColorizationModel().to(self.device)
            model.eval()
            return model

        print("Loading model:", self.checkpoint_path, flush=True)

        # encoder_weights=None → don't try to download imagenet weights at inference
        model = ColorizationModel(
            encoder_name=self.ENCODER,
            encoder_weights=None,
        ).to(self.device)

        checkpoint = torch.load(
            self.checkpoint_path,
            map_location=self.device,
            weights_only=False,
        )

        # Notebook saves either {'model_state_dict': ...} or a raw state_dict
        if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
            state_dict = checkpoint["model_state_dict"]
        else:
            state_dict = checkpoint

        model.load_state_dict(state_dict, strict=True)
        model.eval()

        print("✅ Model loaded", flush=True)
        return model

    # ----------------------------------------------------------- preprocessing
    def prepare_image(self, image_bytes: bytes) -> Tuple[torch.Tensor, np.ndarray]:
        """
        bytes → (L_tensor (1,3,H,W) on device, L_norm (H,W,1) numpy in [0,1])
        Replicates Cell 4 / Cell 15 of the notebook.
        """
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_rgb = np.array(img)

        # Resize via OpenCV (matches notebook: INTER_AREA)
        img_rgb = cv2.resize(
            img_rgb,
            (self.IMAGE_SIZE, self.IMAGE_SIZE),
            interpolation=cv2.INTER_AREA,
        )

        # float32 BEFORE LAB conversion → L in [0,100], ab in [-127,127]
        img_float = img_rgb.astype(np.float32) / 255.0
        img_lab   = cv2.cvtColor(img_float, cv2.COLOR_RGB2LAB)

        L_norm = img_lab[:, :, 0:1] / 100.0          # (H, W, 1) in [0, 1]

        # Replicate L to 3 channels (the model expects in_channels=3)
        L_3ch = np.concatenate([L_norm, L_norm, L_norm], axis=2)   # (H, W, 3)

        L_tensor = (
            torch.from_numpy(L_3ch)
            .permute(2, 0, 1)     # (3, H, W)
            .unsqueeze(0)         # (1, 3, H, W)
            .float()
            .to(self.device)
        )

        return L_tensor, L_norm

    # ---------------------------------------------------------- postprocessing
    def decode_to_rgb(self, L_norm: np.ndarray, ab_pred: torch.Tensor) -> np.ndarray:
        """
        L_norm  : (H, W, 1) numpy in [0, 1]
        ab_pred : (1, 2, H, W) torch in [0, 1]
        Returns : (H, W, 3) uint8 RGB
        """
        ab_pred = torch.clamp(ab_pred, 0, 1)
        ab_np   = ab_pred.squeeze(0).detach().cpu().numpy()   # (2, H, W)

        # Notebook decode (Cell 14 / Cell 15) — go directly through OpenCV uint8 LAB
        L_cv = np.clip(L_norm[:, :, 0] * 255.0, 0, 255)   # uint8 L scale
        a_cv = np.clip(ab_np[0]      * 255.0, 0, 255)
        b_cv = np.clip(ab_np[1]      * 255.0, 0, 255)

        lab_u8 = np.stack([L_cv, a_cv, b_cv], axis=2).astype(np.uint8)
        rgb    = cv2.cvtColor(lab_u8, cv2.COLOR_LAB2RGB)
        rgb    = np.nan_to_num(rgb)
        return rgb.astype(np.uint8)

    # -------------------------------------------------------------- public API
    def predict_image(self, image_bytes: bytes) -> Image.Image:
        """
        bytes (any common image format) → colorized PIL.Image (RGB, 256×256)
        """
        if isinstance(self.model, FallbackColorizationModel):
            print("❌ USING FALLBACK MODEL", flush=True)
            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            return (
                ImageOps.grayscale(img)
                .convert("RGB")
                .resize((self.IMAGE_SIZE, self.IMAGE_SIZE))
            )

        L_tensor, L_norm = self.prepare_image(image_bytes)

        with torch.no_grad():
            ab_pred = self.model(L_tensor)

        print("\n===== DEBUG =====", flush=True)
        print("ab_pred shape:", tuple(ab_pred.shape), flush=True)
        print("ab_pred min  :", ab_pred.min().item(), flush=True)
        print("ab_pred max  :", ab_pred.max().item(), flush=True)
        print("ab_pred mean :", ab_pred.mean().item(), flush=True)
        print("=================\n", flush=True)

        rgb = self.decode_to_rgb(L_norm, ab_pred)
        return Image.fromarray(rgb)
