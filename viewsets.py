
from apps_base.api.viewset_class import TranslateMixin, ModelViewSetForm, britge_action_detail, britge_action_detail_multiple
from .models import DiscountCoupon
from .serializers import *

from django.utils.translation import gettext_lazy as _


class PriceGroupViewSet(ModelViewSetForm):
    queryset = PriceGroup.objects.all()
    serializer_class = PriceGroupSerializer
    admin_roles = ['Admin']

class ProductPriceGroupViewSet(ModelViewSetForm):
    queryset = ProductPriceGroup.objects.all()
    serializer_class = ProductPriceGroupSerializer
    admin_roles = ['Admin']
    serializer_exclude = ['duplicate_prices']

    @britge_action_detail(
            action_icon="ICON_DUPLICATE", 
            add_another_button = _("Add another"), 
            title = _('Duplicate'), 
            sequence = 100, 
            serializer_exclude = [],
            serializer_fields=None,
    )
    def duplicate(self, request, pk=None ):
        instance = self.get_object()
        return super().return_response(request,  instance = self.instance, post_instance=self.instance._meta.model(), initial_data=duplicate_instance_related_uuid(instance))    

    @britge_action_detail_multiple(
        action_icon="ICON_PRICE", 
        title = _('Manage prices'), 
        sequence = 100, 
        serializer_class=ProductPriceSerializer, 
        serializer_exclude = ['product_price_group', 'product'],
        allow_delete = True,
        auto_save = True,
        form_style = {'width':'80vw'},
    )
    def manage_prices(self, request, pk=None ):
        self.callback_func = lambda request, instance: print('CALLBACK', instance.pricing_type)
        return super().multiple_form_handler(request, many_attr='productprice_set')    


from apps_base._base.utils import duplicate_instance_related_uuid
class ProductPriceViewSet(TranslateMixin, ModelViewSetForm):
    queryset = ProductPrice.objects.all().order_by('-created_time').select_related('product', 'price_group')
    serializer_class = ProductPriceSerializer
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

    @britge_action_detail( serializer_class=DiscountSerializer, serializer_fields = ['id', 'discount_abs', 'discount_perc', 'min_order_quantity', 'max_order_quantity', ] )
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
