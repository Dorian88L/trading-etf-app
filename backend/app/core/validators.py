"""
Validators sécurisés pour l'application Trading ETF
Validation des données critiques (ISIN, montants, symboles, etc.)
"""
import re
from typing import Union
from decimal import Decimal, InvalidOperation
from pydantic import validator


def validate_isin(isin: str) -> str:
    """
    Validation robuste du format ISIN (International Securities Identification Number)
    Format: 12 caractères alphanumériques (2 lettres pays + 9 alphanum + 1 check digit)
    Exemples: IE00B4L5Y983, LU0274208692, FR0010315770
    """
    if not isin or not isinstance(isin, str):
        raise ValueError("ISIN requis")
    
    # Nettoyage et normalisation
    isin = isin.strip().upper()
    
    # Validation du format de base
    if not re.match(r'^[A-Z]{2}[A-Z0-9]{9}[0-9]$', isin):
        raise ValueError(
            "Format ISIN invalide. "
            "Attendu: 2 lettres pays + 9 caractères alphanumériques + 1 chiffre de contrôle"
        )
    
    # Validation du code pays (2 premières lettres)
    country_code = isin[:2]
    valid_countries = {
        'AD', 'AE', 'AF', 'AG', 'AI', 'AL', 'AM', 'AO', 'AQ', 'AR', 'AS', 'AT',
        'AU', 'AW', 'AX', 'AZ', 'BA', 'BB', 'BD', 'BE', 'BF', 'BG', 'BH', 'BI',
        'BJ', 'BL', 'BM', 'BN', 'BO', 'BQ', 'BR', 'BS', 'BT', 'BV', 'BW', 'BY',
        'BZ', 'CA', 'CC', 'CD', 'CF', 'CG', 'CH', 'CI', 'CK', 'CL', 'CM', 'CN',
        'CO', 'CR', 'CU', 'CV', 'CW', 'CX', 'CY', 'CZ', 'DE', 'DJ', 'DK', 'DM',
        'DO', 'DZ', 'EC', 'EE', 'EG', 'EH', 'ER', 'ES', 'ET', 'FI', 'FJ', 'FK',
        'FM', 'FO', 'FR', 'GA', 'GB', 'GD', 'GE', 'GF', 'GG', 'GH', 'GI', 'GL',
        'GM', 'GN', 'GP', 'GQ', 'GR', 'GS', 'GT', 'GU', 'GW', 'GY', 'HK', 'HM',
        'HN', 'HR', 'HT', 'HU', 'ID', 'IE', 'IL', 'IM', 'IN', 'IO', 'IQ', 'IR',
        'IS', 'IT', 'JE', 'JM', 'JO', 'JP', 'KE', 'KG', 'KH', 'KI', 'KM', 'KN',
        'KP', 'KR', 'KW', 'KY', 'KZ', 'LA', 'LB', 'LC', 'LI', 'LK', 'LR', 'LS',
        'LT', 'LU', 'LV', 'LY', 'MA', 'MC', 'MD', 'ME', 'MF', 'MG', 'MH', 'MK',
        'ML', 'MM', 'MN', 'MO', 'MP', 'MQ', 'MR', 'MS', 'MT', 'MU', 'MV', 'MW',
        'MX', 'MY', 'MZ', 'NA', 'NC', 'NE', 'NF', 'NG', 'NI', 'NL', 'NO', 'NP',
        'NR', 'NU', 'NZ', 'OM', 'PA', 'PE', 'PF', 'PG', 'PH', 'PK', 'PL', 'PM',
        'PN', 'PR', 'PS', 'PT', 'PW', 'PY', 'QA', 'RE', 'RO', 'RS', 'RU', 'RW',
        'SA', 'SB', 'SC', 'SD', 'SE', 'SG', 'SH', 'SI', 'SJ', 'SK', 'SL', 'SM',
        'SN', 'SO', 'SR', 'SS', 'ST', 'SV', 'SX', 'SY', 'SZ', 'TC', 'TD', 'TF',
        'TG', 'TH', 'TJ', 'TK', 'TL', 'TM', 'TN', 'TO', 'TR', 'TT', 'TV', 'TW',
        'TZ', 'UA', 'UG', 'UM', 'US', 'UY', 'UZ', 'VA', 'VC', 'VE', 'VG', 'VI',
        'VN', 'VU', 'WF', 'WS', 'YE', 'YT', 'ZA', 'ZM', 'ZW'
    }
    
    if country_code not in valid_countries:
        raise ValueError(f"Code pays ISIN invalide: {country_code}")
    
    # Validation du check digit (algorithme Luhn modifié)
    try:
        validate_isin_checksum(isin)
    except ValueError as e:
        raise ValueError(f"Checksum ISIN invalide: {e}")
    
    return isin


def validate_isin_checksum(isin: str) -> bool:
    """
    Validation du checksum ISIN selon l'algorithme Luhn modifié
    """
    # Convertir lettres en chiffres (A=10, B=11, ..., Z=35)
    digits = ""
    for char in isin[:-1]:  # Exclure le dernier digit (checksum)
        if char.isalpha():
            digits += str(ord(char) - ord('A') + 10)
        else:
            digits += char
    
    # Algorithme Luhn modifié
    total = 0
    for i, digit in enumerate(reversed(digits)):
        n = int(digit)
        if i % 2 == 1:  # Position impaire (en partant de la droite)
            n *= 2
            if n > 9:
                n = n // 10 + n % 10
        total += n
    
    # Le check digit doit donner un total multiple de 10
    calculated_check = (10 - (total % 10)) % 10
    actual_check = int(isin[-1])
    
    if calculated_check != actual_check:
        raise ValueError(f"Checksum calculé: {calculated_check}, reçu: {actual_check}")
    
    return True


def validate_financial_amount(amount: Union[float, int, str, Decimal], 
                            min_value: float = 0.01, 
                            max_value: float = 1_000_000_000,
                            allow_negative: bool = False) -> Decimal:
    """
    Validation sécurisée des montants financiers
    """
    if amount is None:
        raise ValueError("Montant requis")
    
    # Conversion sécurisée vers Decimal
    try:
        if isinstance(amount, str):
            # Nettoyage de base
            amount = amount.strip().replace(',', '.')
            # Validation format numérique
            if not re.match(r'^-?\d+(\.\d+)?$', amount):
                raise ValueError("Format de montant invalide")
        
        decimal_amount = Decimal(str(amount))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("Format de montant invalide - doit être un nombre")
    
    # Validation des limites
    if not allow_negative and decimal_amount < 0:
        raise ValueError("Les montants négatifs ne sont pas autorisés")
    
    if decimal_amount < Decimal(str(min_value)):
        raise ValueError(f"Montant trop faible (minimum: {min_value})")
    
    if decimal_amount > Decimal(str(max_value)):
        raise ValueError(f"Montant trop élevé (maximum: {max_value})")
    
    # Validation du nombre de décimales (max 4 pour les prix financiers)
    if decimal_amount.as_tuple().exponent < -4:
        raise ValueError("Maximum 4 décimales autorisées")
    
    return decimal_amount


def validate_etf_symbol(symbol: str) -> str:
    """
    Validation des symboles ETF (Yahoo Finance, Bloomberg, etc.)
    """
    if not symbol or not isinstance(symbol, str):
        raise ValueError("Symbole ETF requis")
    
    # Nettoyage
    symbol = symbol.strip().upper()
    
    # Format de base (3-8 caractères alphanumériques + suffixe optionnel)
    if not re.match(r'^[A-Z0-9]{2,8}(\.[A-Z]{1,3})?$', symbol):
        raise ValueError(
            "Format de symbole ETF invalide. "
            "Attendu: 2-8 caractères alphanumériques + suffixe optionnel (.L, .PA, etc.)"
        )
    
    # Validation des suffixes de marché connus
    if '.' in symbol:
        base_symbol, suffix = symbol.split('.', 1)
        valid_suffixes = {
            'L',      # London Stock Exchange
            'PA',     # Euronext Paris
            'AS',     # Euronext Amsterdam
            'BR',     # Euronext Brussels
            'MI',     # Borsa Italiana Milan
            'DE',     # XETRA Frankfurt
            'SW',     # SIX Swiss Exchange
            'VI',     # Vienna Stock Exchange
            'ST',     # Stockholm Stock Exchange
            'OL',     # Oslo Stock Exchange
            'CO',     # Copenhagen Stock Exchange
            'HE',     # Helsinki Stock Exchange
            'MC',     # Moscow Exchange
            'TO',     # Toronto Stock Exchange
            'V',      # TSX Venture Exchange
        }
        
        if suffix not in valid_suffixes:
            raise ValueError(f"Suffixe de marché non reconnu: .{suffix}")
    
    return symbol


def validate_percentage(percentage: Union[float, int, str], 
                       min_value: float = 0.0, 
                       max_value: float = 100.0) -> float:
    """
    Validation des pourcentages (0-100)
    """
    try:
        if isinstance(percentage, str):
            percentage = percentage.strip().replace('%', '').replace(',', '.')
        
        float_percentage = float(percentage)
    except (ValueError, TypeError):
        raise ValueError("Format de pourcentage invalide")
    
    if float_percentage < min_value or float_percentage > max_value:
        raise ValueError(f"Pourcentage doit être entre {min_value}% et {max_value}%")
    
    return float_percentage


# Decorators Pydantic pour utilisation facile
def isin_validator(cls, v):
    """Validator Pydantic pour ISIN"""
    return validate_isin(v)

def amount_validator(cls, v):
    """Validator Pydantic pour montants financiers"""
    return validate_financial_amount(v)

def symbol_validator(cls, v):
    """Validator Pydantic pour symboles ETF"""
    return validate_etf_symbol(v)

def percentage_validator(cls, v):
    """Validator Pydantic pour pourcentages"""
    return validate_percentage(v)