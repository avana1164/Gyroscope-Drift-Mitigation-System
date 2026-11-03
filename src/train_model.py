"""Train the sequence model against the phone's fused orientation quaternion."""

import argparse
import random
from collections import defaultdict
from pathlib import Path

import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from .database import fetch_training_rows
from .model_inference import OrientationSequenceModel


FEATURE_COLUMNS = (
    "accel_x", "accel_y", "accel_z", "gyro_x", "gyro_y", "gyro_z"
)
TARGET_COLUMNS = (
    "orientation_qx", "orientation_qy", "orientation_qz", "orientation_qw"
)


def make_windows(rows, window_size):
    """Make windows within each recording session; the target is the last row."""
    sessions = defaultdict(list)
    for row in rows:
        sessions[row["session_id"]].append(row)

    windows_by_session = {}
    for session_id, session_rows in sessions.items():
        features = torch.tensor(
            [[float(row[column]) for column in FEATURE_COLUMNS] for row in session_rows],
            dtype=torch.float32,
        )
        targets = torch.tensor(
            [[float(row[column]) for column in TARGET_COLUMNS] for row in session_rows],
            dtype=torch.float32,
        )
        target_norms = targets.norm(dim=1, keepdim=True)
        valid = target_norms.squeeze(1) > 1e-6
        targets = targets / target_norms.clamp_min(1e-6)

        windows = []
        for start in range(len(session_rows) - window_size + 1):
            end = start + window_size - 1
            if not bool(valid[end]):
                continue
            windows.append((start, features[start : end + 1], targets[end]))
        if windows:
            windows_by_session[session_id] = windows
    return windows_by_session, sessions


def split_sessions(windows_by_session, sessions, seed=42):
    """Split by session when possible; otherwise split one session in time."""
    session_ids = list(windows_by_session)
    if len(session_ids) >= 2:
        random.Random(seed).shuffle(session_ids)
        validation_count = max(1, round(len(session_ids) * 0.2))
        if validation_count == len(session_ids):
            validation_count -= 1
        validation_ids = set(session_ids[:validation_count])
        train_samples = [
            (x, y) for sid, samples in windows_by_session.items()
            if sid not in validation_ids for _, x, y in samples
        ]
        validation_samples = [
            (x, y) for sid, samples in windows_by_session.items()
            if sid in validation_ids for _, x, y in samples
        ]
        return train_samples, validation_samples

    if len(session_ids) == 1:
        session_id = session_ids[0]
        session_rows = sessions[session_id]
        windows = windows_by_session[session_id]
        cutoff = int(len(session_rows) * 0.8)
        window_size = len(windows[0][1])
        train_samples = [
            (x, y) for start, x, y in windows if start + window_size <= cutoff
        ]
        validation_samples = [
            (x, y) for start, x, y in windows if start >= cutoff
        ]
        return train_samples, validation_samples
    return [], []


def quaternion_loss(prediction, target):
    """Quaternion loss treats q and -q as the same orientation."""
    same = (prediction - target).pow(2).sum(dim=1)
    opposite = (prediction + target).pow(2).sum(dim=1)
    return torch.minimum(same, opposite).mean()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--window-size", type=int, default=32)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=Path("models/orientation_model.pt"),
    )
    args = parser.parse_args()
    if args.window_size < 1:
        parser.error("--window-size must be at least 1")

    torch.manual_seed(42)
    rows = fetch_training_rows()
    windows_by_session, sessions = make_windows(rows, args.window_size)
    train_samples, validation_samples = split_sessions(windows_by_session, sessions)
    if not train_samples or not validation_samples:
        raise SystemExit(
            "Not enough labeled data for training and validation. Collect complete "
            "paired accel/gyro rows with orientation quaternions across enough time "
            "(and preferably multiple sessions), then retry."
        )

    train_x = torch.stack([sample[0] for sample in train_samples])
    train_y = torch.stack([sample[1] for sample in train_samples])
    validation_x = torch.stack([sample[0] for sample in validation_samples])
    validation_y = torch.stack([sample[1] for sample in validation_samples])

    feature_mean = train_x.reshape(-1, 6).mean(dim=0)
    feature_std = train_x.reshape(-1, 6).std(dim=0, unbiased=False).clamp_min(1e-6)
    train_x = (train_x - feature_mean) / feature_std
    validation_x = (validation_x - feature_mean) / feature_std

    model = OrientationSequenceModel()
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
    train_loader = DataLoader(
        TensorDataset(train_x, train_y), batch_size=args.batch_size, shuffle=True
    )

    for epoch in range(1, args.epochs + 1):
        model.train()
        train_loss_sum = 0.0
        for batch_x, batch_y in train_loader:
            optimizer.zero_grad()
            loss = quaternion_loss(model(batch_x), batch_y)
            loss.backward()
            optimizer.step()
            train_loss_sum += loss.item() * len(batch_x)

        model.eval()
        with torch.no_grad():
            validation_loss = quaternion_loss(model(validation_x), validation_y).item()
        train_loss = train_loss_sum / len(train_samples)
        print(
            f"Epoch {epoch:03d}/{args.epochs}: "
            f"train_loss={train_loss:.6f}, validation_loss={validation_loss:.6f}"
        )

    args.checkpoint.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "feature_mean": feature_mean,
            "feature_std": feature_std,
            "window_size": args.window_size,
            "hidden_size": 64,
            "feature_columns": FEATURE_COLUMNS,
            "target_columns": TARGET_COLUMNS,
        },
        args.checkpoint,
    )
    print(f"Saved trained model to {args.checkpoint}")


if __name__ == "__main__":
    main()
