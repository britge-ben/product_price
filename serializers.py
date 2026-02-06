from rest_framework import serializers

from .models import *
from apps_base.api.serializer_class import BaseModelSerializer, BaseTranslateModelSerializer
from django.utils.translation import gettext_lazy as _
from apps_shared.customer.serializers import CustomerSerializer
from apps_base.api import serializer_fields
from apps_base._base.utils import safe_get

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
    def get_fields(self):
        fields = super().get_fields()
        if bool(self.instance and not isinstance(self.instance, list) and not self.instance.pricing_type in [PRICING_TYPE.PRICE_PER_HOUR, PRICING_TYPE.PRICE_PER_DAY]):
            fields.pop('min_duration')
            fields.pop('max_duration')
        return fields
class ProductPriceGroupSerializer(BaseModelSerializer):
    product_price_objects = ProductPriceSerializer(source='productprice_set', label=_('Prices'), fields=['id', 'price', 'pricing_type', 'min_order_quantity', 'max_order_quantity', 'min_duration', 'max_duration', 'valid_from', 'valid_to'], read_only=True, many=True)
    duplicate_prices = serializer_fields.BooleanField(label=_('Duplicate prices'), write_only=True, initial=False)
    class Meta:
        model = ProductPriceGroup
        fields = '__all__'
    
    def save(self, **kwargs):
        self.validated_data.pop('duplicate_prices', False)
        return super().save(**kwargs)


    
class CustomerDiscountGroupSerializer(BaseModelSerializer):
    class Meta:
        model = CustomerDiscountGroup
        fields = '__all__'

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
            many=True
        )
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
    discount_label= serializers.CharField(label=_('Discount label'))

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


class DiscountCouponSerializer(BaseModelSerializer):
    discount_code = serializers.CharField(label=_('Discount code'))
    class Meta:
        model = DiscountCoupon
        fields = ['discount_code']

    def validate_discount_code(self, value):
        if not DiscountCoupon.objects.filter(discount_code=value).exists():
            raise serializers.ValidationError(_('Invalid discount code'))
        return value



class DiscountCouponFieldMixin:
    discount_code = serializer_fields.CharField( label=_('Discount Coupon'),write_only=True,allow_null=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not hasattr(self.Meta.model, 'add_discount_coupon') and not callable(getattr(self.Meta.model, 'add_discount_coupon', None)):
            raise TypeError(
                f'Class {self.__class__.__name__} must define add_discount_coupon method on model {self.Meta.model.__name__}. '
            )

    def validate_discount_code(self, discount_code):
        if not discount_code:
            return None
        coupon = DiscountCoupon.objects.filter(discount_code=discount_code).first()
        if not coupon:
            raise serializer_fields.ValidationError(_('Invalid discount code'))
        error = coupon.validate_coupon(
            emails=[self.instance.email, safe_get(self.instance, 'account', 'email')],
            order_amount=self.instance.calc_total_amount_in_vat,
            lines=self.instance.reservationlines.all(),
        )
        if error:
            raise serializer_fields.ValidationError(error)
        return coupon

    def save(self, **kwargs):
        discount_code = self.validated_data.pop('discount_code', None)
        instance = super().save(**kwargs)
        if discount_code: 
            instance.add_discount_coupon(discount_code)
        return instance