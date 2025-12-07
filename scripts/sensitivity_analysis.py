"""
Sensitivity Analysis Script for Q-SPI Paper
-------------------------------------------
This script performs a robustness check on the 'Quality Factor' (QF) model proposed in the paper.
It generates:
1. A PDF visualization (sensitivity_analysis.pdf) comparing exponential decay curves.
2. A numerical table showing the volatility of Q-SPI against parameter variations.

Dependencies: numpy, matplotlib, pandas, seaborn
Usage: python sensitivity_analysis.py
"""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# --- Configuration for Academic Plotting ---
sns.set_theme(style="whitegrid")
plt.rcParams.update({
    'font.family': 'serif',       # Serif font for LaTeX compatibility
    'font.size': 12,
    'axes.labelsize': 12,
    'axes.titlesize': 14,
    'legend.fontsize': 10,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'lines.linewidth': 2.5
})

def calculate_quality_factor(rho, lambd):
    """
    Computes the Quality Factor based on the exponential decay model.
    Formula: QF = e^(-lambda * rho)
    """
    return np.exp(-lambd * rho)

def generate_plot():
    """Generates and saves the sensitivity analysis figure."""
    print("Generating Sensitivity Analysis Plot...")
    
    # 1. Define Data Range
    rho_values = np.linspace(0, 1.5, 100) # Debt Density from 0 to 1.5
    
    # 2. Define Scenarios (Lambda values)
    lambda_scenarios = {
        0.5: 'Low Sensitivity (MVP)',
        1.0: 'Standard Sensitivity',
        1.5: 'High Sensitivity (Healthcare/BioArc)',
        2.0: 'Critical (Safety-Critical)'
    }
    
    # 3. Plotting
    plt.figure(figsize=(10, 6))
    
    # Define line styles for better black-and-white printing visibility
    line_styles = ['-', '--', '-.', ':']
    
    for (lam, label), ls in zip(lambda_scenarios.items(), line_styles):
        qf_values = calculate_quality_factor(rho_values, lam)
        plt.plot(rho_values, qf_values, label=f'λ = {lam} ({label})', linestyle=ls)

    # 4. Add Threshold Line (Technical Bankruptcy)
    plt.axhline(y=0.5, color='red', linestyle='-', alpha=0.2, linewidth=4, label='Bankruptcy Threshold (QF=0.5)')
    
    # 5. Annotations & Formatting
    plt.title(r'Sensitivity Analysis of Quality Factor ($e^{-\lambda \rho}$) to Debt Density', fontweight='bold')
    plt.xlabel(r'Debt Density ($\rho$) = New Debt / Adjusted EV')
    plt.ylabel('Quality Factor (Penalty Coefficient)')
    plt.legend(loc='upper right')
    plt.xlim(0, 1.5)
    plt.ylim(0, 1.05)
    
    # 6. Save as PDF
    output_file = "sensitivity_analysis.pdf"
    plt.savefig(output_file, format='pdf', bbox_inches='tight', dpi=300)
    print(f"✅ Plot saved successfully as '{output_file}'")

def generate_numerical_table():
    """Calculates and prints the robustness table."""
    print("\n--- Numerical Sensitivity Analysis Table ---")
    
    base_lambda = 1.5 # The value used in BioArc case study
    perturbation = 0.1 # Testing a +/- 0.1 error margin
    
    scenarios = [
        {'name': 'Low Debt (Stable)', 'rho': 0.1},
        {'name': 'Medium Debt',       'rho': 0.5},
        {'name': 'High Debt (Crisis)','rho': 0.9}
    ]
    
    results = []
    
    for sc in scenarios:
        rho = sc['rho']
        base_qf = calculate_quality_factor(rho, base_lambda)
        lower_qf = calculate_quality_factor(rho, base_lambda - perturbation)
        upper_qf = calculate_quality_factor(rho, base_lambda + perturbation)
        
        # Calculate maximum percentage deviation
        max_diff = max(abs(upper_qf - base_qf), abs(lower_qf - base_qf))
        volatility_pct = (max_diff / base_qf) * 100
        
        results.append({
            'Scenario': sc['name'],
            'Debt Density (ρ)': rho,
            f'QF (λ={base_lambda})': round(base_qf, 3),
            f'QF (λ={base_lambda - perturbation})': round(lower_qf, 3),
            f'QF (λ={base_lambda + perturbation})': round(upper_qf, 3),
            'Volatility (%)': round(volatility_pct, 2)
        })
        
    df = pd.DataFrame(results)
    
    # Display formatted table
    print(df.to_string(index=False))
    print("-" * 80)
    print("Interpretation:")
    print(f"1. Low Volatility ({df.iloc[0]['Volatility (%)']}%) in low-debt zones confirms model stability.")
    print(f"2. Higher Volatility ({df.iloc[2]['Volatility (%)']}%) in crisis zones confirms the model correctly")
    print("   amplifies penalty sensitivity when debt is high.")

if __name__ == "__main__":
    generate_plot()
    generate_numerical_table()
