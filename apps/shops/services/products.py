from typing import Tuple
from django.shortcuts import get_object_or_404
from apps.shops.models import Product

class ProductService:
    @staticmethod
    def approve_product(product_id: str) -> Tuple[Product, bool]:
        product = get_object_or_404(Product, id=product_id)
        if product.status == Product.ProductStatus.ACTIVE:
            return product, False
        
        product.status = Product.ProductStatus.ACTIVE
        product.save(update_fields=['status', 'updated_at'])
        return product, True
        
    @staticmethod
    def reject_product(product_id: str) -> Tuple[Product, bool]:
        product = get_object_or_404(Product, id=product_id)
        if product.status == Product.ProductStatus.REJECTED:
            return product, False
            
        product.status = Product.ProductStatus.REJECTED
        product.save(update_fields=['status', 'updated_at'])
        return product, True
        
    @staticmethod
    def suspend_product(product_id: str) -> Tuple[Product, bool]:
        product = get_object_or_404(Product, id=product_id)
        if product.status == Product.ProductStatus.SUSPENDED:
            return product, False
            
        product.status = Product.ProductStatus.SUSPENDED
        product.save(update_fields=['status', 'updated_at'])
        return product, True
        
    @staticmethod
    def restore_product(product_id: str) -> Tuple[Product, bool]:
        product = get_object_or_404(Product, id=product_id)
        if product.status == Product.ProductStatus.ACTIVE:
            return product, False
            
        product.status = Product.ProductStatus.ACTIVE
        product.save(update_fields=['status', 'updated_at'])
        return product, True
