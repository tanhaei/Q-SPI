import math
import pandas as pd
import matplotlib.pyplot as plt

class QSPICalculator:
    """
    A calculator for the Quality-Adjusted Schedule Performance Index (Q-SPI).
    Based on the paper: "Beyond Velocity: Integrating Technical Debt into Earned Value Management"
    """

    def __init__(self, lambda_sensitivity: float = 1.0, hours_per_sp: float = 1.0):
        """
        Initialize the Q-SPI Calculator.

        Args:
            lambda_sensitivity (float): The sensitivity coefficient (lambda). 
                                        Recommended: 1.0 (Standard), 1.5 (Healthcare/Critical).
            hours_per_sp (float): Conversion factor (beta) to normalize Debt (hours) vs EV (Story Points).
                                  Set to 1.0 if TD is already normalized relative to EV.
        """
        self.lambda_sensitivity = lambda_sensitivity
        self.hours_per_sp = hours_per_sp

    def calculate_spi(self, ev: float, pv: float) -> float:
        """Calculates traditional Schedule Performance Index (SPI)."""
        if pv == 0:
            return 0.0
        return ev / pv

    def calculate_debt_density(self, td_new_hours: float, ev_points: float) -> float:
        """
        Calculates Rho (Debt Density).
        Rho = TD_new / (Beta * EV)
        """
        if ev_points == 0:
            return 0.0
        
        # Normalize EV to hours if beta is provided, or keep as ratio
        denominator = self.hours_per_sp * ev_points
        return td_new_hours / denominator

    def calculate_quality_factor(self, debt_density: float) -> float:
        """
        Calculates the Quality Factor (QF) using exponential decay.
        QF = e^(-lambda * rho)
        """
        return math.exp(-self.lambda_sensitivity * debt_density)

    def calculate_q_spi(self, ev: float, pv: float, td_new: float) -> float:
        """
        Calculates the final Quality-Adjusted SPI.
        Q-SPI = SPI * QF
        """
        spi = self.calculate_spi(ev, pv)
        rho = self.calculate_debt_density(td_new, ev)
        qf = self.calculate_quality_factor(rho)
        
        return spi * qf

def main():
    # --- Example Usage based on BioArc Case Study (Sprint 4-7) ---
    
    # Configuration based on paper (calibrated to match Table 3 results)
    # Assuming lambda approx 1.2 for the "Rush Phase"
    calculator = QSPICalculator(lambda_sensitivity=1.2, hours_per_sp=1.0)

    # Sample Data (Sprint, PV, EV, TD_new_hours)
    sprint_data = [
        {"sprint": "S4 (Rush)", "pv": 100, "ev": 115, "td": 35},
        {"sprint": "S5 (Stack)", "pv": 100, "ev": 120, "td": 55},
        {"sprint": "S6 (Crisis)", "pv": 100, "ev": 120, "td": 80},
        {"sprint": "S7 (Bankruptcy)", "pv": 100, "ev": 110, "td": 100},
    ]

    results = []

    print(f"{'Sprint':<15} | {'SPI':<10} | {'Rho (Density)':<15} | {'QF':<10} | {'Q-SPI':<10}")
    print("-" * 75)

    for data in sprint_data:
        spi = calculator.calculate_spi(data['ev'], data['pv'])
        q_spi = calculator.calculate_q_spi(data['ev'], data['pv'], data['td'])
        rho = calculator.calculate_debt_density(data['td'], data['ev'])
        qf = calculator.calculate_quality_factor(rho)

        results.append({
            "Sprint": data['sprint'],
            "SPI": round(spi, 2),
            "Q-SPI": round(q_spi, 2)
        })

        print(f"{data['sprint']:<15} | {spi:<10.2f} | {rho:<15.2f} | {qf:<10.2f} | {q_spi:<10.2f}")

    # Visualization (Optional)
    df = pd.DataFrame(results)
    
    # Check if we are in a non-interactive environment (just print info)
    print("\n[Info] Data processing complete. You can use matplotlib to plot 'df' vs Sprint.")

if __name__ == "__main__":
    main()
