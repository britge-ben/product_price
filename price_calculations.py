from django.db.models import F, Value, ExpressionWrapper, Case, When
from django.db.models.functions import Extract, Ceil
from apps_base._base.model_fields import CurrencyField
from typing import Optional

SECONDS_PER_HOUR = 3600  # 60 * 60
HOURS_PER_DAY = 24

def calculate_price_expression(
    base_price: F,
    quantity: F,
    duration: F,
    pricing_type: str,
) -> ExpressionWrapper:
    """
    Calculate price expression based on pricing type using Case/When expressions.
    
    Args:
        base_price: Base price field expression (F('price_ex_vat') etc)
        quantity: Quantity field expression
        duration: Duration field expression
        people: People field expression
        pricing_type_field: Field expression for pricing type
        output_field: Django model field type for output
    
    Returns:
        ExpressionWrapper: The calculated price expression
    """
    output_field = CurrencyField()

    expression = Case(
        When(**{pricing_type: 'price'},
             then=ExpressionWrapper(base_price * quantity, output_field=output_field)),
        When(**{pricing_type: 'price_per_hour'},
             then=ExpressionWrapper(base_price * quantity * Ceil(Extract(duration, 'epoch') / SECONDS_PER_HOUR), output_field=output_field)),
        When(**{pricing_type: 'price_per_day'},
             then=ExpressionWrapper(base_price * quantity * Ceil(Extract(duration, 'epoch') / SECONDS_PER_HOUR / HOURS_PER_DAY), output_field=output_field)),
        # When(**{pricing_type: 'price_per_person'},
        #      then=ExpressionWrapper(base_price * quantity * people, output_field=output_field)),
        # When(**{pricing_type: 'price_per_person_per_hour'},
        #      then=ExpressionWrapper(base_price * quantity * people * Extract(duration, 'epoch') / SECONDS_PER_HOUR, output_field=output_field)),
        # When(**{pricing_type: 'price_per_person_per_day'},
        #      then=ExpressionWrapper(base_price * quantity * people * Ceil(Extract(duration, 'epoch') / SECONDS_PER_HOUR / HOURS_PER_DAY), output_field=output_field)),
        When(**{pricing_type: 'pt'},
             then=base_price * quantity),
        default=ExpressionWrapper(base_price * quantity, output_field=output_field),
        output_field=output_field,
    )

    return ExpressionWrapper(expression, output_field=output_field)

def add_price_annotations(queryset, price_field='price_ex_vat', quantity_field='quantity', 
                        duration_field='duration', people_field='people', 
                        pricing_type_field='pricing_type', prefix=''):
    """
    Add standard price annotations to a queryset.
    
    Args:
        queryset: The queryset to annotate
        price_field: Name of the price field
        quantity_field: Name of the quantity field
        duration_field: Name of the duration field
        people_field: Name of the people field
        pricing_type_field: Name of the pricing type field
        prefix: Prefix for the field names (e.g., 'reservationlines__' or 'cartlines__')
    """
    return queryset.annotate(
        calc_total_amount_ex_vat=calculate_price_expression(
            F(f'{prefix}{price_field}'),
            F(f'{prefix}{quantity_field}'),
            F(f'{prefix}{duration_field}'),
            F(f'{prefix}{people_field}'),
            F(f'{prefix}{pricing_type_field}')
        ),
        calc_total_amount_vat=calculate_price_expression(
            F(f'{prefix}{price_field}') * F(f'{prefix}vat_percentage'),
            F(f'{prefix}{quantity_field}'),
            F(f'{prefix}{duration_field}'),
            F(f'{prefix}{people_field}'),
            F(f'{prefix}{pricing_type_field}')
        )
    ).annotate(
        calc_total_amount_in_vat=ExpressionWrapper(
            F('calc_total_amount_ex_vat') + F('calc_total_amount_vat'),
            output_field=CurrencyField()
        )
    ) 