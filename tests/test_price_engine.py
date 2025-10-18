import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.price_engine import calculate_price


def test_price_2016_2023():
    price, status = calculate_price(2016, 1)
    assert price == 1000
    assert status == 'valid'

    price, status = calculate_price(2023, 12)
    assert price == 1000
    assert status == 'valid'


def test_price_2024_jan_apr():
    price, status = calculate_price(2024, 1)
    assert price == 300
    assert status == 'valid'

    price, status = calculate_price(2024, 4)
    assert price == 300
    assert status == 'valid'


def test_price_2024_may_onwards():
    price, status = calculate_price(2024, 5)
    assert price == 0
    assert status == 'not_valid'

    price, status = calculate_price(2024, 12)
    assert price == 0
    assert status == 'not_valid'


def test_price_2025_plus():
    price, status = calculate_price(2025, 1)
    assert price == 0
    assert status == 'manual_review'


def test_price_before_2016():
    price, status = calculate_price(2015, 1)
    assert price == 0
    assert status == 'manual_review'


if __name__ == '__main__':
    test_price_2016_2023()
    test_price_2024_jan_apr()
    test_price_2024_may_onwards()
    test_price_2025_plus()
    test_price_before_2016()

    print("✅ All price engine tests passed!")
