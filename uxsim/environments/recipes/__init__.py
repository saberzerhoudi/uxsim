"""
Web parsing recipes for different websites
"""

from .amazon import AMAZON_RECIPES, get_amazon_config, extract_amazon_product_info

__all__ = [
    'AMAZON_RECIPES',
    'get_amazon_config', 
    'extract_amazon_product_info'
] 