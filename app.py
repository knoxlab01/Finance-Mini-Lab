"""Finance Mini Lab：Milestone 1 固定参数演示。"""

from src.compound_interest import calculate_future_value


def main() -> None:
    principal = 10000
    annual_rate = 0.08
    years = 10

    future_value = calculate_future_value(principal, annual_rate, years)
    print(f"{future_value:.2f}")


if __name__ == "__main__":
    main()
