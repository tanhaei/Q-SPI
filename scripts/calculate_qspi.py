"""
Core Q-SPI calculation utilities.

This module implements the metric defined in the paper:
Q-SPI = SPI * exp(-lambda * (TD_new / (beta * EV_raw)))

Article-aligned defaults:
- BioArc: beta=8 h/SP, lambda=10.0
- Apache Dubbo: beta=6 h/SP, lambda=6.0
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

import pandas as pd


@dataclass(frozen=True)
class QSPIConfig:
    """Configuration for a calibrated Q-SPI series."""

    lambda_sensitivity: float
    hours_per_sp: float


ARTICLE_PRESETS = {
    "bioarc": QSPIConfig(lambda_sensitivity=10.0, hours_per_sp=8.0),
    "dubbo": QSPIConfig(lambda_sensitivity=6.0, hours_per_sp=6.0),
}


class QSPICalculator:
    """Calculator for the Quality-Adjusted Schedule Performance Index (Q-SPI)."""

    def __init__(self, lambda_sensitivity: float, hours_per_sp: float) -> None:
        if hours_per_sp <= 0:
            raise ValueError("hours_per_sp (beta) must be positive.")
        if lambda_sensitivity < 0:
            raise ValueError("lambda_sensitivity must be non-negative.")

        self.lambda_sensitivity = float(lambda_sensitivity)
        self.hours_per_sp = float(hours_per_sp)

    @classmethod
    def from_case(cls, case_name: str) -> "QSPICalculator":
        key = case_name.strip().lower()
        if key not in ARTICLE_PRESETS:
            valid = ", ".join(sorted(ARTICLE_PRESETS))
            raise ValueError(f"Unknown case '{case_name}'. Expected one of: {valid}.")
        cfg = ARTICLE_PRESETS[key]
        return cls(lambda_sensitivity=cfg.lambda_sensitivity, hours_per_sp=cfg.hours_per_sp)

    def calculate_spi(self, ev_raw: float, pv: float) -> float:
        """Compute traditional SPI = EV_raw / PV."""
        if pv == 0:
            return 0.0
        return ev_raw / pv

    def calculate_debt_density(self, td_new_hours: float, ev_raw: float) -> float:
        """Compute rho = TD_new / (beta * EV_raw)."""
        if ev_raw <= 0:
            return 0.0
        return td_new_hours / (self.hours_per_sp * ev_raw)

    def calculate_quality_factor(self, debt_density: float) -> float:
        """Compute QF = exp(-lambda * rho)."""
        return math.exp(-self.lambda_sensitivity * debt_density)

    def calculate_q_spi(self, ev_raw: float, pv: float, td_new: float) -> float:
        """Compute Q-SPI = SPI * QF."""
        spi = self.calculate_spi(ev_raw, pv)
        rho = self.calculate_debt_density(td_new, ev_raw)
        qf = self.calculate_quality_factor(rho)
        return spi * qf

    def calculate_row(self, pv: float, ev_raw: float, td_new: float) -> dict[str, float]:
        """Return all derived metrics for one sprint row."""
        spi = self.calculate_spi(ev_raw, pv)
        rho = self.calculate_debt_density(td_new, ev_raw)
        qf = self.calculate_quality_factor(rho)
        q_spi = spi * qf
        return {
            "PV": pv,
            "EV_raw": ev_raw,
            "TD_new": td_new,
            "SPI": spi,
            "Debt_Density": rho,
            "Quality_Factor": qf,
            "Q_SPI": q_spi,
        }

    def calculate_table(self, rows: Iterable[Mapping[str, float]], label_field: str = "Sprint") -> pd.DataFrame:
        """Calculate a Q-SPI table from sprint-like row mappings."""
        output_rows: list[dict[str, float | str]] = []

        for row in rows:
            label = row[label_field]
            pv = float(row["pv"])
            ev_raw = float(row["ev"])
            td_new = float(row["td"])
            derived = self.calculate_row(pv=pv, ev_raw=ev_raw, td_new=td_new)
            output_rows.append(
                {
                    label_field: label,
                    **derived,
                }
            )

        return pd.DataFrame(output_rows)


def format_table(df: pd.DataFrame, label_field: str = "Sprint") -> str:
    """Format a calculation table for console output."""
    printable = df.copy()
    for col in ["SPI", "Debt_Density", "Quality_Factor", "Q_SPI"]:
        printable[col] = printable[col].map(lambda x: f"{x:.4f}")
    return printable[[label_field, "SPI", "Debt_Density", "Quality_Factor", "Q_SPI"]].to_string(index=False)


def bioarc_example_data() -> Sequence[dict[str, float | str]]:
    """Sprint data reported in the BioArc table of the paper."""
    return [
        {"Sprint": "S4", "pv": 100, "ev": 115, "td": 35},
        {"Sprint": "S5", "pv": 100, "ev": 120, "td": 55},
        {"Sprint": "S6", "pv": 100, "ev": 120, "td": 80},
        {"Sprint": "S7", "pv": 100, "ev": 110, "td": 100},
        {"Sprint": "S8", "pv": 100, "ev": 40, "td": 5},
        {"Sprint": "S9", "pv": 100, "ev": 85, "td": 10},
        {"Sprint": "S10", "pv": 100, "ev": 95, "td": 8},
    ]


def dubbo_example_data() -> Sequence[dict[str, float | str]]:
    """Sprint data reported in the Apache Dubbo table of the paper."""
    return [
        {"Sprint": "Sprint 1", "pv": 45, "ev": 30, "td": 0},
        {"Sprint": "Sprint 2", "pv": 50, "ev": 42, "td": 15},
        {"Sprint": "Sprint 3", "pv": 48, "ev": 48, "td": -5},
        {"Sprint": "Sprint 4", "pv": 60, "ev": 55, "td": 15},
        {"Sprint": "Sprint 5", "pv": 65, "ev": 40, "td": 35},
        {"Sprint": "Sprint 6", "pv": 55, "ev": 55, "td": -20},
        {"Sprint": "Sprint 7", "pv": 35, "ev": 35, "td": -5},
        {"Sprint": "Sprint 8", "pv": 70, "ev": 60, "td": 35},
        {"Sprint": "Sprint 9", "pv": 80, "ev": 65, "td": 20},
        {"Sprint": "Sprint 10", "pv": 75, "ev": 70, "td": -5},
        {"Sprint": "Sprint 11", "pv": 60, "ev": 60, "td": -10},
        {"Sprint": "Sprint 12", "pv": 50, "ev": 45, "td": -5},
        {"Sprint": "Sprint 13", "pv": 85, "ev": 72, "td": 40},
        {"Sprint": "Sprint 14", "pv": 90, "ev": 80, "td": 20},
        {"Sprint": "Sprint 15", "pv": 70, "ev": 70, "td": -10},
    ]


def main() -> None:
    calculator = QSPICalculator.from_case("bioarc")
    df = calculator.calculate_table(bioarc_example_data())
    print("BioArc article-aligned Q-SPI reproduction")
    print(format_table(df))


if __name__ == "__main__":
    main()
