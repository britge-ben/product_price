
from apps_base.api.viewset_class import TranslateMixin, ModelViewSetForm, britge_action_detail
from .models import DiscountCoupon
from .serializers import *

from django.utils.translation import gettext_lazy as _


class PriceGroupViewSet(TranslateMixin, ModelViewSetForm):
    queryset = PriceGroup.objects.all()
    serializer_class = PriceGroupSerializer
    field_name = 'price_group_objects'
    ordering_fields = ['created_time', 'modified_time']
    admin_roles = ['Admin']

class ProductPriceViewSet(TranslateMixin, ModelViewSetForm):
    queryset = ProductPrice.objects.all().order_by('-created_time').select_related('product', 'price_group')
    serializer_class = ProductPriceSerializer
    field_name = 'product_price_objects'
    ordering_fields = ['created_time', 'modified_time']
    search_fields = ['product__translations__name', 'product__product_number', ]
    admin_roles = ['Admin']

class ProductDiscountGroupViewSet(TranslateMixin, ModelViewSetForm):
    queryset = ProductDiscountGroup.objects.all().prefetch_related( 
        'translations',
        model_fields.Prefetch(
            'discount_set', 
            queryset=Discount.objects.all().select_related('customer')),
    )
    serializer_class = ProductDiscountGroupSerializer
    admin_roles = ['Admin']

    @britge_action_detail( serializer_class=DiscountSerializer, serializer_fields = [ 'id', 'discount_abs', 'discount_perc', 'min_order_quantity', 'max_order_quantity', ] )
    def add_discount(self, request, pk=None ):
        instance = Discount(
            discount_group = self.get_object()
        )
        return super().return_reponse(request, instance=instance)
    
    
class CustomerDiscountGroupViewSet(TranslateMixin, ModelViewSetForm):
    queryset = CustomerDiscountGroup.objects.all()
    serializer_class = CustomerDiscountGroupSerializer
    admin_roles = ['Admin']
    
class DiscountViewSet( ModelViewSetForm):
    queryset = Discount.objects.all()
    serializer_class = DiscountSerializer
    admin_roles = ['Admin']
             
class DiscountCoupoonViewSet(TranslateMixin, ModelViewSetForm):
    queryset = DiscountCoupon.objects.all()
    serializer_class = DiscountCouponSerializer

    admin_roles = ['Admin']
