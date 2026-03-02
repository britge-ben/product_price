from typing import Any
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

from apps_shared.product.utils import get_create_product
from apps_shared.product_price.models import PRICING_TYPE
from django.db.models import Func, Value
import logging
logger = logging.getLogger(__name__)

def return_date_time_latest():
    return datetime.datetime(9999, 12, 31)


def get_default_store():
    return Store.get_default()

class PriceGroup(DefaultMixin, BaseModel):
    DEFAULTS = {'store': get_default_store, 'description': 'Default'}
    store = model_fields.ForeignKey("entity.Store", verbose_name=_("Store"),  on_delete=model_fields.CASCADE, default=get_default_store)
    description = model_fields.CharField(_("Price group"), unique=True, max_length=50)

    class Meta:
        verbose_name = _('Price group')
        verbose_name_plural = _('Price groups')

    def __str__(self):
        return self.description

    class BritgePortal:
        viewset = 'apps_shared.product_price.viewsets.PriceGroupViewSet'
        portal_urls = [
            {
                'id': 'price_group',
                'url': 'product/price-group/',
                'title': 'Price group',
                'menu':{
                    'id': 'price_group',
                    'sequence':0, 
                    'parent': 'product',  
                    'url': 'product/price-group/', 
                    'title': _('Price groups')
                }
            }
        ]
class ProductPriceGroup(BaseModel):
    description = model_fields.CharField(_("Product price group"), unique=True, max_length=50)

    class Meta:
        verbose_name = _('Product price group')
        verbose_name_plural = _('Product price groups')

    def __str__(self):
        return self.description

    class BritgePortal:
        viewset = 'apps_shared.product_price.viewsets.ProductPriceGroupViewSet'
        portal_urls = [
            {
                'id': 'product_price_group',
                'url': 'product/product-price-group/',
                'title': 'Product price group',
                'menu':{
                    'id': 'product_price_group',
                    'sequence':0, 
                    'parent': 'product',  
                    'url': 'product/product-price-group/', 
                    'title': _('Product price groups')
                }
            }
        ]
class ProductPrice(SequenceMixin, BaseModel):
    SEQUENCE_FIELDS = []
    importable_model = True

    price_group = model_fields.ForeignKey("product_price.PriceGroup", verbose_name=_("Price Group"), style={'wrapper_class': 'col-6'}, default=PriceGroup.get_default_pk, on_delete=model_fields.CASCADE)
    product_price_group = model_fields.ForeignKey("product_price.ProductPriceGroup", verbose_name=_("Product Price Group"), null=True, blank=True, style={'wrapper_class': 'col-6'}, on_delete=model_fields.CASCADE)
    product = model_fields.ForeignKey("product.Product", verbose_name=_("Product"), null=True, blank=True, style={'wrapper_class': 'col-6'}, on_delete=model_fields.CASCADE)
    option = model_fields.ForeignKey("product.ProductOption", verbose_name=_("Option"), related_name='price_option', null=True, blank=True, style={'wrapper_class': 'col-6'}, on_delete=model_fields.CASCADE)

    price = model_fields.DecimalField(verbose_name=_('Price'),style={'wrapper_class': 'col-6'},max_digits=12, decimal_places=4, default=0)

    pricing_type = model_fields.CharField(
        verbose_name=_('Pricing type'), 
        max_length=100, 
        reload_field=True,
        default=PRICING_TYPE.PRICE, 
        choices=PRICING_TYPE.choices,
        style={'wrapper_class': 'col-6'}
    )

    min_order_quantity = model_fields.IntegerField(verbose_name=_('min quantity order discount'), default=0, style={'wrapper_class': 'col-6'})
    max_order_quantity = model_fields.IntegerField(verbose_name=_('max quantity order discount'), default=9999999, style={'wrapper_class': 'col-6'})

    min_duration = model_fields.DurationField(verbose_name=_('Min duration'), format='d h', default=timezone.timedelta(days=0), style={'wrapper_class': 'col-6'})
    max_duration = model_fields.DurationField(verbose_name=_('Max duration'), format='d h', default=timezone.timedelta(days=100), style={'wrapper_class': 'col-6'})

    valid_from = model_fields.DateTimeField(verbose_name=_("valid from"),default= timezone.now, style={'wrapper_class': 'col-6'})  
    valid_to = model_fields.DateTimeField(verbose_name=_("valid to"),default= return_date_time_latest, style={'wrapper_class': 'col-6'})  

    class Meta:
        verbose_name = _('Price group price')
        verbose_name_plural = _('Price group prices')

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
    option = model_fields.ForeignKey("product.ProductOption", verbose_name=_("Option"), related_name='discount_option', null=True, blank=True, style={'wrapper_class': 'col-6'}, on_delete=model_fields.CASCADE)

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

from django.db.models import Sum
class DiscountCoupon(BaseTranslationModel):
    products = model_fields.ManyToManyField(Product,verbose_name=_("Allowed for Products"), blank = True, help_text=_("Leave empty to make available for all products"), through='product_price.ProductDiscountCoupon')  
    needs_products = model_fields.IntegerField(verbose_name=_("Quantity needed of allowed products"), null=True, blank = True, help_text=_(f"Fill in number of products that for the discount coupon to be valid. Use -quantity to use distinct number of products, leave empty to use all products."))  
    email = model_fields.CharField(_("Email"), max_length=100, null=True, blank = True)

    discount_code = model_fields.CharField(verbose_name=_("Discount code"), max_length=30, unique=True)  
    translations = TranslatedFields(
        discount_label = model_fields.CharField(verbose_name=_("discount label"),max_length=100)
    )

    discount_abs = model_fields.DecimalField(verbose_name=_("Absolute discount"), max_digits=10, decimal_places=4, default = decimal.Decimal(0))
    discount_perc = model_fields.DecimalField(verbose_name=_("Discount Percentage"), max_digits=10, decimal_places=4, default = decimal.Decimal(0))
    
    minimal_order_amount = model_fields.DecimalField(verbose_name=_("Minimal order amount"), max_digits=10, decimal_places=2, default = decimal.Decimal(0))
    
    valid_from = model_fields.DateTimeField(verbose_name=_("Valid from"), default= timezone.now )  
    valid_to = model_fields.DateTimeField(verbose_name=_("Valid to"), default= timezone.datetime(9999, 12, 31)  )  
    
    objects = DiscountCouponManager()

    def __str__(self):
        return str(self.discount_code)
        
    def save(self, *args, **kwargs):
        if self.email == '':
            self.email = None
        super().save(*args, **kwargs)

    def get_product(self, store):
        if self.discount_abs:
            product = get_create_product('DISCOUNT_COUPON_ABS', {'name':_('Discount Coupon'), 'pricing_type': PRICING_TYPE.PRICE, 'default_price': 0}, store)
        elif self.discount_perc:
            product = get_create_product('DISCOUNT_COUPON_PERC', {'name':_('Discount Coupon'), 'pricing_type': PRICING_TYPE.PERCENTAGE_TOTAL, 'default_price': 0}, store)
        product = product[0]
        return product

    def validate_coupon(self, emails, order_amount, lines):
        if emails: 
            valid = False
            for email in emails:
                if email == self.email:
                    valid = True
            if not valid:
                return _('This is not a valid code for you')
        if order_amount < self.minimal_order_amount:
            return _('Order amount has to be a minimum of €{min} ').format(min=self.minimal_order_amount)
        product_list = self.products.all()
        if product_list:
            if self.needs_products is None or self.needs_products < 0:
                needed = self.needs_products or len(product_list)
                if lines.filter(product__in=product_list).values('product').distinct().count() < needed:
                    return _('This discount coupon is not valid for this order')
            elif self.needs_products > 0:
                if lines.filter(product__in=product_list).aggregate(Sum('quantity')) < self.needs_products:
                    return _('This discount coupon is not valid for this order')
        return False

    class Meta:
        verbose_name = _('Discount coupon')
        verbose_name_plural = _('Discount coupons')
        
class ProductDiscountCoupon(BaseModel):
    discount_coupon = model_fields.ForeignKey(DiscountCoupon, verbose_name=_("Discount Coupon"),on_delete=model_fields.CASCADE)  
    product = model_fields.ForeignKey(Product, verbose_name=_("product"),on_delete=model_fields.CASCADE)  

    class Meta:
        verbose_name = _('Product discount coupon')
        verbose_name_plural = _('Product discount coupons')



from .price_calculations import calculate_price_expression
from apps_base._base.model_fields import F, Value, Cast
from django.db import models
from apps_shared.product.choices import UNIT_TYPE
from apps_shared.vat.models import Country

class PriceFieldsMixin(models.Model):
    quantity = model_fields.DecimalField( _("Quantity"), max_digits=18, decimal_places=6, blank=True, style={'wrapper_class':'col-4'})
    unit = model_fields.CharField(choices=UNIT_TYPE.choices, max_length = 3, blank=True, verbose_name=_('Unit'), style={'wrapper_class':'col-4'} )
    pricing_type = model_fields.CharField(verbose_name=_("Pricing type"), choices=PRICING_TYPE.choices, max_length=256, blank=True, style={'wrapper_class':'col-4'})
    base_price = model_fields.CurrencyFloatField(_('Base price'),null=True, blank=True, editable=False,)
    price_ex_discount = model_fields.CurrencyFloatField(_('Price ex discount'), blank=True, style={'wrapper_class':'col-4'})
    price_discount = model_fields.CurrencyFloatField(_('Discount'), blank=True, style={'wrapper_class':'col-4'})
    vat_percentage = model_fields.DecimalField(verbose_name=_("VAT"), max_digits=5, decimal_places=4, editable=False)
    is_vat_included = model_fields.BooleanField(verbose_name=_("VAT included in price"), hidden_write_field=True, style={'wrapper_class':'col-4'})

    price = model_fields.CurrencyGeneratedField(
        expression = F('price_ex_discount') - F('price_discount'),
        verbose_name=_("Price"),
        output_field=model_fields.CurrencyFloatField(),
    )
    total_amount = model_fields.CurrencyGeneratedField(
        expression = calculate_price_expression(
            base_price=F('price_ex_discount') - F('price_discount'),
            quantity=F('quantity'),
            pricing_type='pricing_type'
        ),
        verbose_name=_("Total amount"),
        output_field=model_fields.CurrencyFloatField(),
    )
    unit_price = model_fields.CurrencyGeneratedField(
        expression = 
            calculate_price_expression(
                base_price=F('price_ex_discount'),
                quantity=Value(1),
                pricing_type='pricing_type'
            ),
        verbose_name=_("Unit amount"),
        output_field=model_fields.CurrencyFloatField(),
    )
    unit_discount = model_fields.CurrencyGeneratedField(
        expression = 
            calculate_price_expression(
                base_price=F('price_discount'),
                quantity=Value(1),
                pricing_type='pricing_type'
            ),
        verbose_name=_("Unit amount"),
        output_field=model_fields.CurrencyFloatField(),
    )
    unit_amount= model_fields.CurrencyGeneratedField(
        expression = 
            calculate_price_expression(
                base_price=F('price_ex_discount') - F('price_discount'),
                quantity=Value(1),
                pricing_type='pricing_type'
            ),
        verbose_name=_("Unit amount"),
        output_field=model_fields.CurrencyFloatField(),
    )
    unit_price_ex_vat = model_fields.CurrencyGeneratedField(
        expression = 
            calculate_price_expression(
                base_price=F('price_ex_discount'),
                quantity=Value(1),
                pricing_type='pricing_type'
            )  
            / (
                Value(1) + (
                F('vat_percentage') * 
                Cast(F('is_vat_included'), output_field=model_fields.IntegerField())
             )
            ),
        verbose_name=_("Total amount ex vat"),
        output_field=model_fields.CurrencyFloatField(),
    )
    unit_discount_ex_vat = model_fields.CurrencyGeneratedField(
        expression = 
            calculate_price_expression(
                base_price=F('price_discount'),
                quantity=Value(1),
                pricing_type='pricing_type'
            )  
            / (
                Value(1) + (
                F('vat_percentage') * 
                Cast(F('is_vat_included'), output_field=model_fields.IntegerField())
             )
            ),
        verbose_name=_("Total amount ex vat"),
        output_field=model_fields.CurrencyFloatField(),
    )
    unit_amount_ex_vat = model_fields.CurrencyGeneratedField(
        expression = 
            calculate_price_expression(
                base_price=F('price_ex_discount') - F('price_discount'),
                quantity=Value(1),
                pricing_type='pricing_type'
            )  
            / (
                Value(1) + (
                F('vat_percentage') * 
                Cast(F('is_vat_included'), output_field=model_fields.IntegerField())
             )
            ),
        verbose_name=_("Total amount ex vat"),
        output_field=model_fields.CurrencyFloatField(),
    )

    amount_ex_vat = model_fields.CurrencyGeneratedField(
        expression = 
            calculate_price_expression(
                base_price=F('price_ex_discount') - F('price_discount'),
                quantity=F('quantity'),
                pricing_type='pricing_type'
            )
            / (
                Value(1) + (
                F('vat_percentage') * 
                Cast(F('is_vat_included'), output_field=model_fields.IntegerField())
             )
            ),
        verbose_name=_("Total amount ex vat"),
        output_field=model_fields.CurrencyFloatField(),
    )
    amount_vat = model_fields.CurrencyGeneratedField(
        expression = 
            calculate_price_expression(
                base_price=F('price_ex_discount') - F('price_discount'),
                quantity=F('quantity'),
                pricing_type='pricing_type'
            )
            / (
                Value(1) + (
                F('vat_percentage') * 
                Cast(F('is_vat_included'), output_field=model_fields.IntegerField())
             )
            ) * F('vat_percentage')
        ,
        verbose_name=_("Total vat"),
        output_field=model_fields.CurrencyFloatField(),
    )
    amount_in_vat = model_fields.CurrencyGeneratedField(
        expression = 
            calculate_price_expression(
                base_price=F('price_ex_discount') - F('price_discount'),
                quantity=F('quantity'),
                pricing_type='pricing_type'
            ) *
            (
                Value(1) + (
                    F('vat_percentage')
                    * 
                    (Value(1) - Cast(F('is_vat_included'), output_field=model_fields.IntegerField()))
            )
            ),
        verbose_name=_("Total amount ex vat"),
        output_field=model_fields.CurrencyFloatField(),
    )

    def set_pricing(self):
        print('set_pricing', self.price_ex_discount, self.price_discount, self.unit, self.vat_percentage, self.pricing_type)
        if self.price_ex_discount is None or self.price_discount is None or self.unit is None or self.vat_percentage is None or self.pricing_type is None:
            self.quantity = self.quantity or self.product.default_quantity or 1
            product = Product.objects.all().add_prices(
                customer = self.header.customer,
                country = self.header.customer.country if self.header.customer else Country.get_default(),
                store = self.header.store,
                quantity = self.quantity,
            ).get(pk = self.product.pk)
            self.price_ex_discount = self.price_ex_discount or product.price
            self.price_discount = self.price_discount or product.price_discount
            self.unit = self.unit or product.unit 
            self.vat_percentage = self.vat_percentage or product.calc_vat_percentage
            self.pricing_type = self.pricing_type or product.calc_pricing_type
        self.is_vat_included = self.header.store.enter_vat

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.set_pricing()
        super().save(*args, **kwargs)

class DurationRounded(Func):
    """
    Round duration: < 7.5h → ceil to hour, >= 7.5h → ceil to day.
    PostgreSQL-only; pass the duration expression as the first arg.
    """
    function = None
    template = """
    CASE
        WHEN EXTRACT(epoch FROM %(expressions)s) < 27000
        THEN (CEIL(EXTRACT(epoch FROM %(expressions)s) / 3600) * 3600) * interval '1 second'
        ELSE (CEIL(EXTRACT(epoch FROM %(expressions)s) / 86400) * 86400) * interval '1 second'
    END
    """
    output_field = model_fields.DurationField()

class DurationPriceFieldsModel(PriceFieldsMixin):
    from_time = model_fields.DateTimeField(verbose_name=_("From time"))
    to_time = model_fields.DateTimeField(verbose_name=_("To time"))
    duration = model_fields.GeneratedField(
        expression = F('to_time')  - F('from_time'),
        verbose_name=_("Duration"), output_field=model_fields.DurationField(),
    )
    duration_rounded = model_fields.GeneratedField(
        expression=DurationRounded(F('duration')),
        verbose_name=_("Duration"),
        output_field=model_fields.DurationField(),
    )
    price = model_fields.CurrencyGeneratedField(
        expression = F('price_ex_discount') - F('price_discount'),
        verbose_name=_("Price"),
        output_field=model_fields.CurrencyFloatField(),
    )
    total_amount = model_fields.CurrencyGeneratedField(
        expression = calculate_price_expression(
            base_price=F('price_ex_discount') - F('price_discount'),
            quantity=F('quantity'),
            duration=F('to_time')  - F('from_time'),
            # people=F('people'),
            pricing_type='pricing_type'
        ),
        verbose_name=_("Total amount"),
        output_field=model_fields.CurrencyFloatField(),
    )
    unit_price = model_fields.CurrencyGeneratedField(
        expression = 
            calculate_price_expression(
                base_price=F('price_ex_discount'),
                quantity=Value(1),
                duration=F('to_time')  - F('from_time'),
                # people=F('people'),
                pricing_type='pricing_type'
            ),
        verbose_name=_("Unit amount"),
        output_field=model_fields.CurrencyFloatField(),
    )
    unit_discount = model_fields.CurrencyGeneratedField(
        expression = 
            calculate_price_expression(
                base_price=F('price_discount'),
                quantity=Value(1),
                duration=F('to_time')  - F('from_time'),
                # people=F('people'),
                pricing_type='pricing_type'
            ),
        verbose_name=_("Unit amount"),
        output_field=model_fields.CurrencyFloatField(),
    )
    unit_amount= model_fields.CurrencyGeneratedField(
        expression = 
            calculate_price_expression(
                base_price=F('price_ex_discount') - F('price_discount'),
                quantity=Value(1),
                duration=F('to_time')  - F('from_time'),
                # people=F('people'),
                pricing_type='pricing_type'
            ),
        verbose_name=_("Unit amount"),
        output_field=model_fields.CurrencyFloatField(),
    )
    unit_price_ex_vat = model_fields.CurrencyGeneratedField(
        expression = 
            calculate_price_expression(
                base_price=F('price_ex_discount'),
                quantity=Value(1),
                duration=F('to_time')  - F('from_time'),
                # people=F('people'),
                pricing_type='pricing_type'
            )  
            / (
                Value(1) + (
                F('vat_percentage') * 
                Cast(F('is_vat_included'), output_field=model_fields.IntegerField())
             )
            ),
        verbose_name=_("Total amount ex vat"),
        output_field=model_fields.CurrencyFloatField(),
    )
    unit_discount_ex_vat = model_fields.CurrencyGeneratedField(
        expression = 
            calculate_price_expression(
                base_price=F('price_discount'),
                quantity=Value(1),
                duration=F('to_time')  - F('from_time'),
                # people=F('people'),
                pricing_type='pricing_type'
            )  
            / (
                Value(1) + (
                F('vat_percentage') * 
                Cast(F('is_vat_included'), output_field=model_fields.IntegerField())
             )
            ),
        verbose_name=_("Total amount ex vat"),
        output_field=model_fields.CurrencyFloatField(),
    )
    unit_amount_ex_vat = model_fields.CurrencyGeneratedField(
        expression = 
            calculate_price_expression(
                base_price=F('price_ex_discount') - F('price_discount'),
                quantity=Value(1),
                duration=F('to_time')  - F('from_time'),
                # people=F('people'),
                pricing_type='pricing_type'
            )  
            / (
                Value(1) + (
                F('vat_percentage') * 
                Cast(F('is_vat_included'), output_field=model_fields.IntegerField())
             )
            ),
        verbose_name=_("Total amount ex vat"),
        output_field=model_fields.CurrencyFloatField(),
    )
    amount_ex_vat = model_fields.CurrencyGeneratedField(
        expression = 
            calculate_price_expression(
                base_price=F('price_ex_discount') - F('price_discount'),
                quantity=F('quantity'),
                duration=F('to_time')  - F('from_time'),
                # people=F('people'),
                pricing_type='pricing_type'
            )
            / (
                Value(1) + (
                F('vat_percentage') * 
                Cast(F('is_vat_included'), output_field=model_fields.IntegerField())
             )
            ),
        verbose_name=_("Total amount ex vat"),
        output_field=model_fields.CurrencyFloatField(),
    )
    amount_vat = model_fields.CurrencyGeneratedField(
        expression = 
            calculate_price_expression(
                base_price=F('price_ex_discount') - F('price_discount'),
                quantity=F('quantity'),
                duration=F('to_time')  - F('from_time'),
                # people=F('people'),
                pricing_type='pricing_type'
            )
            / (
                Value(1) + (
                F('vat_percentage') * 
                Cast(F('is_vat_included'), output_field=model_fields.IntegerField())
             )
            ) * F('vat_percentage')
        ,
        verbose_name=_("Total vat"),
        output_field=model_fields.CurrencyFloatField(),
    )
    amount_in_vat = model_fields.CurrencyGeneratedField(
        expression = 
            calculate_price_expression(
                base_price=F('price_ex_discount') - F('price_discount'),
                quantity=F('quantity'),
                duration=F('to_time')  - F('from_time'),
                # people=F('people'),
                pricing_type='pricing_type'
            ) *
            (
                Value(1) + (
                    F('vat_percentage')
                    * 
                    (Value(1) - Cast(F('is_vat_included'), output_field=model_fields.IntegerField()))
            )
            ),
        verbose_name=_("Total amount ex vat"),
        output_field=model_fields.CurrencyFloatField(),
    )


    class Meta:
        abstract = True