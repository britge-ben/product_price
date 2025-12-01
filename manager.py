from apps_base._base.managers import  BaseManager, BaseQuerySet, BaseTranslationManager, BaseTranslatableQuerySet
from django.db import models


class DiscountGroupQuerySet(BaseTranslatableQuerySet):
    pass

class DiscountGroupManager(BaseTranslationManager):

    def get_queryset(self):
        return DiscountGroupQuerySet(self.model, using=self._db)#.filter(is_active=True)

class DiscountQuerySet(BaseQuerySet):
    def filter_available_prices(self):
        return self.extra(where=['"validFrom" < NOW() AND "validTo" > NOW()' ])

class DiscountManager(models.Manager):
    def get_queryset(self):
        return DiscountQuerySet(self.model, using=self._db)#.filter(is_active=True)

class DiscountCouponQuerySet(BaseTranslatableQuerySet):
    def filter_available_prices(self):
        return self.extra(where=['"validFrom" < NOW() AND "validTo" > NOW()' ])

class DiscountCouponManager(BaseTranslationManager):
    def get_queryset(self):
        return DiscountCouponQuerySet(self.model, using=self._db)#.filter()

