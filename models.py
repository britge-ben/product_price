from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import decimal
import datetime

from parler.models import TranslatedFields
from apps_shared.product.models import Product
from apps_base._base.models import BaseModel, BaseTranslationModel, SequenceMixin
from apps_base.entity.models import Store
from apps_base._base import model_fields

from .manager import DiscountGroupManager, DiscountManager, DiscountCouponManager
from apps_base._base.models import DefaultMixin
from apps_shared.product.choices import PRICING_TYPE


import logging
logger = logging.getLogger(__name__)

def return_date_time_latest():
    return datetime.datetime(9999, 12, 31)

def get_default_store():
    return Store.objects.get_current().pk

class PriceGroup(DefaultMixin, BaseModel):
    DEFAULTS = {'store': get_default_store}
    store = model_fields.ForeignKey("entity.Store", verbose_name=_("Store"),  on_delete=model_fields.CASCADE, default=get_default_store)
    description = model_fields.CharField(_("Price group"), unique=True, max_length=50)

    class Meta:
        verbose_name = _('Price group')
        verbose_name_plural = _('Price groups')

    def __str__(self):
        return self.description

class ProductPriceGroup(BaseModel):
    description = model_fields.CharField(_("Product price group"), unique=True, max_length=50)

    class Meta:
        verbose_name = _('Product price group')
        verbose_name_plural = _('Product price groups')

    def __str__(self):
        return self.description

class ProductPrice(SequenceMixin, BaseModel):
    SEQUENCE_FIELDS = []
    importable_model = True

    price_group = model_fields.ForeignKey("product_price.PriceGroup", verbose_name=_("Price Group"), null=True, blank=True, on_delete=model_fields.CASCADE)
    product_price_group = model_fields.ForeignKey("product_price.ProductPriceGroup", verbose_name=_("Product Price Group"), null=True, blank=True, style={'wrapper_class': 'col-6'}, on_delete=model_fields.CASCADE)
    product = model_fields.ForeignKey("product.Product", verbose_name=_("Product"), null=True, blank=True, style={'wrapper_class': 'col-6'}, on_delete=model_fields.CASCADE)

    price = model_fields.DecimalField(verbose_name=_('Price'),style={'wrapper_class': 'col-6'},max_digits=12, decimal_places=2, default=0)

    pricing_type = model_fields.CharField(
        verbose_name=_('Pricing type'), 
        max_length=100, 
        default=PRICING_TYPE.PRICE, 
        choices=PRICING_TYPE.choices,
        style={'wrapper_class': 'col-6'}
    )

    min_order_quantity = model_fields.IntegerField(verbose_name=_('min quantity order discount'), default=0, style={'wrapper_class': 'col-6'})
    max_order_quantity = model_fields.IntegerField(verbose_name=_('max quantity order discount'), default=9999999, style={'wrapper_class': 'col-6'})

    min_duration = model_fields.DurationField(verbose_name=_('Min duration'), default=timezone.timedelta(days=0), style={'wrapper_class': 'col-6'})
    max_duration = model_fields.DurationField(verbose_name=_('Max duration'), default=timezone.timedelta(days=100), style={'wrapper_class': 'col-6'})

    valid_from = model_fields.DateTimeField(verbose_name=_("valid from"),default= timezone.now, style={'wrapper_class': 'col-6'})  
    valid_to = model_fields.DateTimeField(verbose_name=_("valid to"),default= return_date_time_latest, style={'wrapper_class': 'col-6'})  

    class Meta:
        verbose_name = _('Price group price')
        verbose_name_plural = _('Price group prices')

    def save(self, *args, **kwargs):
        # check uniqueness
        unique = ProductPrice.objects.filter(
            product = self.product,
            price_group = self.price_group,
            price = round(self.price,2)
        ).first()
        if unique:
            return unique
        # check other prices
        olds = ProductPrice.objects.filter(
            product = self.product,
            price_group = self.price_group,
            valid_from__lte = self.valid_from, 
            valid_to__gte = self.valid_to
        ).update(valid_to = self.valid_from)
        super().save()

    class BritgePortal:
        viewset = 'apps_shared.product_price.viewsets.ProductPriceViewSet'
        portal_urls = [
            {
                'id': 'product_price',
                'url': 'product/price-group/',
                'title': 'Price group',
                'menu':{
                    'id': 'product_price',
                    'sequence':0, 
                    'parent': 'product',  
                    'url': 'product/price-group/', 
                    'title': _('Price groups')
                }
            }
        ]

class CustomerDiscountGroup(BaseModel):
    importable_model = True
    store = model_fields.ForeignKey("entity.Store", verbose_name=_("store"), on_delete=model_fields.CASCADE, null = True, blank = True)
    group_number = model_fields.CharField(verbose_name=_("Group number"),max_length=100, unique=True)
    description = model_fields.CharField(verbose_name=_("Discount reference"),max_length=100)

    def __str__(self):
        return self.group_number

    class Meta:
        verbose_name = _('Customer Group')
        verbose_name_plural = _('Customer Groups')
                
class ProductDiscountGroup(BaseTranslationModel):
    store = model_fields.ForeignKey("entity.Store", verbose_name=_("store"), on_delete=model_fields.CASCADE, null = True, blank = True)
    group_number = model_fields.CharField(verbose_name=_("Group number"),max_length=100, unique=True)
    description = model_fields.CharField(verbose_name=_("Discount reference"),max_length=100)
    
    translations = TranslatedFields(
        discount_label = model_fields.CharField(verbose_name=_("discount label"),max_length=100, default="Not translated")
    )

    include_children = model_fields.BooleanField(default=False)

    objects = DiscountGroupManager()

    def __str__(self):
        return "{description}".format(description = self.group_number)

    class Meta:
        # default_related_name = 'discountgroups'
        verbose_name = _('Discount group')
        verbose_name_plural = _('Discount groups')

    def save(self, *args, **kwargs):
        if not self.translations.all():
            self.discount_label = self.group_number
        if not self.description:
            self.name = self.description
        return super().save()
    @property
    def max_discount(self):
        abs_max = 0
        perc_max = 0
        for x in self.discountgroupsdiscounts.all():
            abs_max = max(abs_max, x.discount_abs)
            perc_max = max(perc_max, x.discount_perc)
        return (abs_max, perc_max)

    def discount_obj(self, q):
        abs_max = 0
        perc_max = 0
        for x in self.discountgroupsdiscounts.all():
            if x.min_order_quantity <= q and x.max_order_quantity >= q:
                return (x.discount_abs, x.discount_perc)
        return (abs_max, perc_max)        


    class BritgePortal:
        viewset = 'apps_shared.product_price.viewsets.ProductPriceViewSet'
        portal_urls = [
            {
                'id': 'discount_group',
                'url': 'product/discount-group/',
                'title': 'Discount group',
                'menu':{
                    'id': 'discount_group',
                    'sequence':0, 
                    'parent': 'product',  
                    'url': 'product/discount-group/', 
                    'title': _('Discount groups')
                }
            }
        ]
from django.db.models import CheckConstraint

class Discount(BaseModel):
    importable_model = True

    product_discount_group = model_fields.ForeignKey('product_price.ProductDiscountGroup', verbose_name=_("Product discount group"),on_delete=model_fields.CASCADE, null=True)  
    product = model_fields.ForeignKey(Product, verbose_name=_("Product"),on_delete=model_fields.CASCADE, blank=True, null=True)  

    customer_discount_group = model_fields.ForeignKey('product_price.CustomerDiscountGroup', verbose_name=_("Customer discount group"),on_delete=model_fields.CASCADE, blank=True, null=True)  
    customer = model_fields.ForeignKey('customer.Customer', verbose_name=_("Customer"),on_delete=model_fields.CASCADE, blank=True, null=True)  

    discount_perc = model_fields.DecimalField(verbose_name=_("Discount percentage"),max_digits=10, decimal_places=4, default = decimal.Decimal(0))

    min_order_quantity = model_fields.IntegerField(verbose_name=_('Min quantity order discount'), default=0)
    max_order_quantity = model_fields.IntegerField(verbose_name=_('Max quantity order discount'), default=9999999)

    min_duration = model_fields.DurationField(verbose_name=_('Min duration'), default=timezone.timedelta(days=0), style={'wrapper_class': 'col-6'})
    max_duration = model_fields.DurationField(verbose_name=_('Max duration'), default=timezone.timedelta(days=100), style={'wrapper_class': 'col-6'})

    valid_from = model_fields.DateTimeField(verbose_name=_("valid from"),default=timezone.now )  
    valid_to = model_fields.DateTimeField(verbose_name=_("valid to"), default=return_date_time_latest )  

    objects = DiscountManager()

    class Meta:
        # default_related_name = 'discounts'
        verbose_name = _('Discount group discount')
        verbose_name_plural = _('Discount group discounts')
        constraints = [
            CheckConstraint(check=model_fields.Q(product__isnull=False) | model_fields.Q(product_discount_group__isnull=False), name="new_product_or_group"),
        ]
        indexes = [
            model_fields.Index(
                fields=['product','product_discount_group','customer_discount_group','customer','valid_from', 'valid_to'],
                include=['discount_perc', 'product'],
                name="product_prices_index"
            )
        ]


    def save(self, *args, **kwargs):
        if self.discount_perc > 1:
            self.discount_perc = self.discount_perc / 100
        #check if discount exists
        exists = Discount.objects.filter(
                    product_discount_group = self.product_discount_group,
                    product = self.product,
                    customer_discount_group = self.customer_discount_group,
                    customer = self.customer,
                    discount_perc = round(self.discount_perc,4),
                    discount_abs = round(self.discount_abs,4),
                ).first()
        if exists:
            return exists
        # check other prices
        olds = Discount.objects.filter(
            product_discount_group = self.product_discount_group,
            product = self.product,
            customer_discount_group = self.customer_discount_group,
            customer = self.customer,
            valid_from__lte = self.valid_from, 
            valid_to__gte = self.valid_to
        ).update(valid_to = self.valid_from)
        
        # if not self.translations.all():
        # #     self.discount_label = self.group_number
        # if not self.description:
        #     self.name = self.description
        return super().save()


class DiscountCoupon(BaseTranslationModel):
    products = model_fields.ManyToManyField(Product, blank = True, help_text=_("Leave empty to make available for all products"), through='product_price.ProductDiscountCoupon')  
    email = model_fields.CharField(max_length=100, null = True, blank = True)

    discount_code = model_fields.CharField( max_length=30, unique=True)  
    translations = TranslatedFields(
        discount_label = model_fields.CharField(verbose_name=_("discount label"),max_length=100)
    )

    discount_abs = model_fields.DecimalField(max_digits=10, decimal_places=4, default = decimal.Decimal(0))
    discount_perc = model_fields.DecimalField(max_digits=10, decimal_places=4, default = decimal.Decimal(0))
    
    minimal_order_amount = model_fields.DecimalField(max_digits=10, decimal_places=2, default = decimal.Decimal(0))
    
    valid_from = model_fields.DateTimeField(default= timezone.now )  
    valid_to = model_fields.DateTimeField(default= return_date_time_latest  )  
    
    objects = DiscountCouponManager()
    def __str__(self):
        return str(self.discount_code)
        
    def save(self, *args, **kwargs):
        if self.email == '':
            self.email = None
        super().save(*args, **kwargs)
        
    class Meta:
        # default_related_name = 'discountcoupons'
        verbose_name = _('Discount coupon')
        verbose_name_plural = _('Discount coupons')
        
class ProductDiscountCoupon(BaseModel):
    discount_coupon = model_fields.ForeignKey(DiscountCoupon, verbose_name=_("Discount Coupon"),on_delete=model_fields.CASCADE)  
    product = model_fields.ForeignKey(Product, verbose_name=_("product"),on_delete=model_fields.CASCADE)  

    class Meta:
        # default_related_name = 'productdiscountcoupons'
        verbose_name = _('Product discount coupon')
        verbose_name_plural = _('Product discount coupons')
