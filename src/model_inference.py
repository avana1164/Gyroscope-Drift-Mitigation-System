"""Sequence model and checkpoint helpers for phone-orientation inference."""

from pathlib import Path

import torch
from torch import nn
from torch.nn import functional as F


class OrientationSequenceModel(nn.Module):
    """Predict an orientation quaternion from a sequence of accel/gyro samples."""

    def __init__(self, hidden_size=64):
        super().__init__()
        self.gru = nn.GRU(input_size=6, hidden_size=hidden_size, batch_first=True)
        self.output = nn.Linear(hidden_size, 4)

    def forward(self, sample_window):
        _, hidden = self.gru(sample_window)
        quaternion = self.output(hidden[-1])
        return F.normalize(quaternion, p=2, dim=-1, eps=1e-8)


DEFAULT_CHECKPOINT = (
    Path(__file__).resolve().parent.parent / "models" / "orientation_model.pt"
)


def load_orientation_model(checkpoint_path=DEFAULT_CHECKPOINT):
    """Load a trained model checkpoint; return None if none has been trained."""
    checkpoint_path = Path(checkpoint_path)
    if not checkpoint_path.exists():
        return None

    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    model = OrientationSequenceModel(hidden_size=checkpoint["hidden_size"])
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    feature_mean = checkpoint["feature_mean"].float()
    feature_std = checkpoint["feature_std"].float().clamp_min(1e-6)
    return model, feature_mean, feature_std, int(checkpoint["window_size"])


def predict_orientation(loaded_model, sample_window):
    """Predict a unit quaternion from an unnormalized [time, 6] sample window."""
    model, feature_mean, feature_std, _ = loaded_model
    features = torch.tensor(sample_window, dtype=torch.float32)
    features = (features - feature_mean) / feature_std
    with torch.no_grad():
        prediction = model(features.unsqueeze(0))[0]
    return prediction.tolist()
