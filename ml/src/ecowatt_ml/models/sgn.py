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


class _TemporalSubnetwork(nn.Module):
    def __init__(self, input_channels: int, hidden_size: int, dropout: float) -> None:
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv1d(input_channels, hidden_size // 2, kernel_size=9, padding=4),
            nn.BatchNorm1d(hidden_size // 2),
            nn.ReLU(),
            nn.Conv1d(hidden_size // 2, hidden_size, kernel_size=7, padding=3),
            nn.BatchNorm1d(hidden_size),
            nn.ReLU(),
            nn.Conv1d(hidden_size, hidden_size, kernel_size=5, padding=2),
            nn.ReLU(),
        )
        self.dropout = nn.Dropout(dropout)

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        encoded = self.features(inputs)
        center = encoded[:, :, encoded.shape[-1] // 2]
        return self.dropout(center)


class SGNApplianceModel(nn.Module):
    """Sequence-to-point Subtask Gated Network for one appliance.

    The regression estimate is multiplied by the on-state probability, as in
    Shin et al. (2018), instead of treating NILM as dominant-class prediction.
    """

    def __init__(
        self,
        input_channels: int = 3,
        hidden_size: int = 64,
        dropout: float = 0.15,
    ) -> None:
        super().__init__()
        self.power_network = _TemporalSubnetwork(
            input_channels,
            hidden_size,
            dropout,
        )
        self.state_network = _TemporalSubnetwork(
            input_channels,
            hidden_size,
            dropout,
        )
        self.power_head = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Linear(hidden_size // 2, 1),
            nn.Softplus(),
        )
        self.state_head = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Linear(hidden_size // 2, 1),
        )

    def forward(
        self,
        inputs: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        power = self.power_head(self.power_network(inputs)).squeeze(1)
        state_logit = self.state_head(self.state_network(inputs)).squeeze(1)
        gated_power = power * torch.sigmoid(state_logit)
        return power, state_logit, gated_power


class SGNDisaggregator(nn.Module):
    def __init__(
        self,
        appliances: list[str] | tuple[str, ...],
        input_channels: int = 3,
        hidden_size: int = 64,
        dropout: float = 0.15,
    ) -> None:
        super().__init__()
        self.appliances = tuple(appliances)
        self.models = nn.ModuleDict(
            {
                appliance: SGNApplianceModel(
                    input_channels=input_channels,
                    hidden_size=hidden_size,
                    dropout=dropout,
                )
                for appliance in self.appliances
            }
        )

    def forward(
        self,
        inputs: torch.Tensor,
    ) -> dict[str, tuple[torch.Tensor, torch.Tensor, torch.Tensor]]:
        return {
            appliance: self.models[appliance](inputs)
            for appliance in self.appliances
        }
