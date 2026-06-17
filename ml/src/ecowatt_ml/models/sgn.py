from __future__ import annotations

import torch
from torch import nn


class SGNClassifier(nn.Module):
    """Compact SGN-inspired temporal classifier for low-frequency NILM signals."""

    def __init__(
        self,
        input_features: int,
        classes: int,
        hidden_size: int = 64,
        dropout: float = 0.2,
    ) -> None:
        super().__init__()
        self.temporal_encoder = nn.GRU(
            input_size=input_features,
            hidden_size=hidden_size,
            batch_first=True,
            bidirectional=True,
        )
        self.semantic_gate = nn.Sequential(
            nn.Linear(hidden_size * 2, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size * 2),
            nn.Sigmoid(),
        )
        self.classifier = nn.Sequential(
            nn.LayerNorm(hidden_size * 2),
            nn.Dropout(dropout),
            nn.Linear(hidden_size * 2, classes),
        )

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        encoded, _ = self.temporal_encoder(inputs)
        pooled = encoded.mean(dim=1)
        gated = pooled * self.semantic_gate(pooled)
        return self.classifier(gated)
