"""Convenience entrypoint for reproducing the BioArc Q-SPI example from the paper."""

from scripts.calculate_qspi import QSPICalculator, bioarc_example_data, format_table


def main() -> None:
    calculator = QSPICalculator.from_case("bioarc")
    df = calculator.calculate_table(bioarc_example_data())

    print("BioArc Q-SPI reproduction based on the paper's reported parameters")
    print("Case: beta = 8 h/SP, lambda = 10.0")
    print(format_table(df))


if __name__ == "__main__":
    main()
