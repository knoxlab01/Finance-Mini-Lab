"""Finance Mini Lab：交互式复利计算器。"""

from math import isfinite

from src.compound_interest import (
    calculate_future_value as calculate_compound_interest,
)


def read_number(prompt: str) -> float:
    """读取有限数值，为非数字输入提供易懂的提示。"""
    try:
        value = float(input(prompt))
    except ValueError:
        raise ValueError("请输入有效数字，例如 10000、8 或 10。") from None
    if not isfinite(value):
        raise ValueError("请输入有限数值，不能使用 nan 或 inf。")
    return value


def main() -> None:
    print("## Finance Mini Lab v0.2.0")
    print()
    try:
        principal = read_number("principal（本金）: ")
        rate_percent = read_number("annual return rate (%)（年化收益率百分比）: ")
        years = read_number("years（投资年限）: ")

        annual_rate = rate_percent / 100
        future_value = calculate_compound_interest(principal, annual_rate, years)
        if not isfinite(future_value):
            raise OverflowError
    except ValueError as error:
        message = str(error)
        if message == "annual_rate 必须大于 -1":
            message = "年化收益率必须大于 -100%。"
        print(f"输入错误：{message}")
        return
    except OverflowError:
        print("计算结果超出支持范围，请减小输入数值后重新运行。")
        return
    except (EOFError, KeyboardInterrupt):
        print("\n输入已取消，请重新运行程序。")
        return

    print()
    print(f"Initial Investment: ¥{principal:,.2f}")
    print(f"Annual Return: {rate_percent:.2f}%")
    print(f"Investment Period: {years:g} years")
    print(f"Future Value: ¥{future_value:,.2f}")


if __name__ == "__main__":
    main()
