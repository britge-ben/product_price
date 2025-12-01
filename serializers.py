from rest_framework import serializers

from .models import *
from apps_base.api.serializer_class import BaseModelSerializer, BaseTranslateModelSerializer
from django.utils.translation import gettext_lazy as _


class ProductSerializer(BaseModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class PriceGroupSerializer(BaseModelSerializer):
    class Meta:
        model = PriceGroup
        fields = '__all__'
        
class ProductPriceSerializer(BaseModelSerializer):
    price_group_object = PriceGroupSerializer(source='price_group', label=_('Price group'), read_only=True)
    product_object = ProductSerializer(source='product', label=_('Product'), read_only=True)
    class Meta:
        model = ProductPrice
        fields = '__all__'
        extra_kwargs = {
            'product':{'style':{'class':'select2'}, 'html_cutoff':10000}
        }
    
class CustomerDiscountGroupSerializer(BaseModelSerializer):
    class Meta:
        model = CustomerDiscountGroup
        fields = '__all__'

from apps_shared.customer.serializers import CustomerSerializer
class DiscountSerializer(BaseModelSerializer):
    product_object = ProductSerializer(source='product', label=_('Product'), read_only=True)
    product_discount_group_object = PriceGroupSerializer(source='product_discount_group', label=_('Price group'), read_only=True)
    customer_object = CustomerSerializer(source='customer', label=_('Customer'), read_only=True, fields=['id', 'company'])
    customer_discount_group_object = CustomerDiscountGroupSerializer(source='customer_discount_group', label=('Customer Discount Group'), read_only=True)

    class Meta:
        model = Discount
        fields = '__all__'
        
    def get_discount_group(self, obj):
        return ProductDiscountGroupSerializer(obj.discount_group).data

    def validate_min_order_quantity(self, min_order_quantity):
        discounts = Discount.objects.filter(discount_group = self.instance.discount_group, min_order_quantity__lte = min_order_quantity, max_order_quantity__gte = min_order_quantity).exclude(id = self.instance.pk)
        if discounts:
            raise serializers.ValidationError(_('A discount with this minimal order quantity already exists'))
        return min_order_quantity
        
    def validate_max_order_quantity(self, max_order_quantity):
        discounts = Discount.objects.filter(discount_group = self.instance.discount_group, min_order_quantity__lte = max_order_quantity, max_order_quantity__gte = max_order_quantity).exclude(id = self.instance.pk)
        if discounts:
            raise serializers.ValidationError(_('A discount with this maximum order quantity already exists'))
        return max_order_quantity
    
class ProductDiscountGroupSerializer(BaseModelSerializer):
    discount_label= serializers.CharField(label=_('discount label'))
    discount_objects = DiscountSerializer(
            source='discounts.all', 
            label=_('Discounts'),
            fields= [
                'id', 
                'customer_object',
                'discount_abs',
                'discount_perc',
                'min_order_quantity',
                'max_order_quantity',
            ], 
            many=True)
    class Meta:
        model = ProductDiscountGroup
        fields = '__all__'


class DiscountCouponTranslationSerializer(BaseTranslateModelSerializer):

    class Meta:
        model = DiscountCoupon
        fields = [ 
            'discount_label'
        ]

class DiscountCouponSerializer(BaseTranslateModelSerializer):
    discount_label= serializers.CharField(label=_('discount label'))

    class Meta:
        model = DiscountCoupon
        fields = '__all__'

    def validate_discount_perc(self, value):
            """
            Discount Percentage must be between 0 and 1
            """
            if value > 1 or value < 0:
                raise serializers.ValidationError("Discount Percentage must be between 0 and 1")
            return value

