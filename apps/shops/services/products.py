from typing import Tuple
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from apps.shops.models import Product

class ProductService:
    @staticmethod
    def approve_product(product_id: str) -> Tuple[Product, bool]:
        product = get_object_or_404(Product, id=product_id)
        if product.status == Product.ProductStatus.ACTIVE:
            return product, False
            
        if product.status != Product.ProductStatus.PENDING:
            raise ValidationError("Only pending products can be approved.")
        
        product.status = Product.ProductStatus.ACTIVE
        product.save(update_fields=['status', 'updated_at'])
        return product, True
        
    @staticmethod
    def reject_product(product_id: str) -> Tuple[Product, bool]:
        product = get_object_or_404(Product, id=product_id)
        if product.status == Product.ProductStatus.REJECTED:
            return product, False
            
        if product.status != Product.ProductStatus.PENDING:
            raise ValidationError("Only pending products can be rejected.")
            
        product.status = Product.ProductStatus.REJECTED
        product.save(update_fields=['status', 'updated_at'])
        return product, True
        
    @staticmethod
    def suspend_product(product_id: str) -> Tuple[Product, bool]:
        product = get_object_or_404(Product, id=product_id)
        if product.status == Product.ProductStatus.SUSPENDED:
            return product, False
            
        if product.status != Product.ProductStatus.ACTIVE:
            raise ValidationError("Only active products can be suspended.")
            
        product.status = Product.ProductStatus.SUSPENDED
        product.save(update_fields=['status', 'updated_at'])
        return product, True
        
    @staticmethod
    def restore_product(product_id: str) -> Tuple[Product, bool]:
        product = get_object_or_404(Product, id=product_id)
        if product.status == Product.ProductStatus.ACTIVE:
            return product, False
            
        if product.status != Product.ProductStatus.SUSPENDED:
            raise ValidationError("Only suspended products can be restored.")
            
        product.status = Product.ProductStatus.ACTIVE
        product.save(update_fields=['status', 'updated_at'])
        return product, True
