"""
Sensitivity analysis for the Q-SPI paper.

This script keeps the analysis local to the calibrated case-study values reported
in the article instead of using a generic global lambda.
It generates:
1. sensitivity_analysis.pdf
2. numerical console tables for the BioArc and Apache Dubbo calibrations
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


sns.set_theme(style="whitegrid")
plt.rcParams.update(
    {
        "font.family": "serif",
        "font.size": 12,
        "axes.labelsize": 12,
        "axes.titlesize": 14,
        "legend.fontsize": 9,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "lines.linewidth": 2.2,
    }
)

CASES = {
    "BioArc": 10.0,
    "Apache Dubbo": 6.0,
}
PERTURBATION = 0.1


def calculate_quality_factor(rho: np.ndarray | float, lambd: float) -> np.ndarray | float:
    """Compute QF = exp(-lambda * rho)."""
    return np.exp(-lambd * rho)


def generate_plot() -> None:
    """Generate the article-aligned sensitivity figure."""
    print("Generating sensitivity analysis plot...")

    rho_values = np.linspace(0, 1.5, 200)
    line_styles = ["-", "--", ":"]

    plt.figure(figsize=(10, 6))

    for case_name, base_lambda in CASES.items():
        for line_style, lambd in zip(
            line_styles,
            [base_lambda - PERTURBATION, base_lambda, base_lambda + PERTURBATION],
        ):
            label = f"{case_name}: λ={lambd:.1f}"
            plt.plot(rho_values, calculate_quality_factor(rho_values, lambd), linestyle=line_style, label=label)

    plt.title(r"Local sensitivity of the quality factor $e^{-\lambda\rho}$")
    plt.xlabel(r"Debt Density ($\rho$) = $TD_{new} / (\beta \cdot EV_{raw})$")
    plt.ylabel("Quality Factor (QF)")
    plt.xlim(0, 1.5)
    plt.ylim(0, 1.05)
    plt.legend(loc="upper right", ncol=2)

    output_file = "sensitivity_analysis.pdf"
    plt.savefig(output_file, format="pdf", bbox_inches="tight", dpi=300)
    plt.close()
    print(f"Saved '{output_file}'.")


def build_sensitivity_table(case_name: str, base_lambda: float) -> pd.DataFrame:
    """Return a local sensitivity table for one calibrated case."""
    scenarios = [
        {"Scenario": "Low debt", "Debt Density (ρ)": 0.1},
        {"Scenario": "Medium debt", "Debt Density (ρ)": 0.5},
        {"Scenario": "High debt", "Debt Density (ρ)": 0.9},
    ]

    rows: list[dict[str, float | str]] = []
    for scenario in scenarios:
        rho = scenario["Debt Density (ρ)"]
        base_qf = float(calculate_quality_factor(rho, base_lambda))
        lower_qf = float(calculate_quality_factor(rho, base_lambda - PERTURBATION))
        upper_qf = float(calculate_quality_factor(rho, base_lambda + PERTURBATION))
        max_diff = max(abs(lower_qf - base_qf), abs(upper_qf - base_qf))
        volatility_pct = (max_diff / base_qf) * 100 if base_qf else 0.0

        rows.append(
            {
                "Case": case_name,
                "Scenario": scenario["Scenario"],
                "Debt Density (ρ)": rho,
                f"QF (λ={base_lambda:.1f})": round(base_qf, 3),
                f"QF (λ={base_lambda - PERTURBATION:.1f})": round(lower_qf, 3),
                f"QF (λ={base_lambda + PERTURBATION:.1f})": round(upper_qf, 3),
                "Volatility (%)": round(volatility_pct, 2),
            }
        )

    return pd.DataFrame(rows)


def generate_numerical_tables() -> None:
    """Print local sensitivity tables for all calibrated cases."""
    print("\n--- Numerical Sensitivity Analysis Tables ---")
    for case_name, base_lambda in CASES.items():
        df = build_sensitivity_table(case_name, base_lambda)
        print(f"\n{case_name} (local perturbation: λ ± {PERTURBATION})")
        print(df.to_string(index=False))


def main() -> None:
    generate_plot()
    generate_numerical_tables()


if __name__ == "__main__":
    main()
