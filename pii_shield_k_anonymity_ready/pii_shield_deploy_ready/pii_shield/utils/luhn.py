"""Luhn checksum helper."""
def luhn_valid(number: str) -> bool:
    """Validate a digit-only number with the Luhn checksum."""
    if not number.isdigit() or len(number) < 2: return False
    digits = [int(x) for x in number][::-1]
    total = 0
    for i, digit in enumerate(digits):
        if i % 2:
            digit *= 2
            if digit > 9: digit -= 9
        total += digit
    return total % 10 == 0
