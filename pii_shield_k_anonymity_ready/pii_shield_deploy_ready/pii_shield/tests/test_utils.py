from utils.digits import normalize_digits
from utils.verhoeff import verhoeff_valid
from utils.luhn import luhn_valid
def test_digits(): assert normalize_digits("१२३৪৫৬௭")=="1234567"
def test_verhoeff_known_vector(): assert verhoeff_valid("2363")
def test_verhoeff_invalid(): assert not verhoeff_valid("2364")
def test_luhn_known_vector(): assert luhn_valid("79927398713")
def test_luhn_invalid(): assert not luhn_valid("79927398714")
