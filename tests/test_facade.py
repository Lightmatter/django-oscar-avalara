from decimal import Decimal as D

from django.test import TestCase
from oscar.test import factories
from oscar.apps.partner import strategy, models as partner_models
from oscar.apps.order import models
from oscar.apps.shipping import methods
from oscar.apps.checkout import calculators
from django_dynamic_fixture import G
import mock

import avalara
from . import responses


def build_submission():
    basket = factories.create_basket()
    # Ensure taxes aren't set by default
    basket.strategy = strategy.US()

    # Ensure partner has an address
    partner = basket.lines.all()[0].stockrecord.partner
    G(partner_models.PartnerAddress, partner=partner)

    shipping_address = G(models.ShippingAddress)
    shipping_method = methods.FixedPrice(D('0.99'))
    shipping_method.set_basket(basket)

    calculator = calculators.OrderTotalCalculator()
    total = calculator.calculate(basket, shipping_method)

    return {
        'user': None,
        'basket': basket,
        'shipping_address': shipping_address,
        'shipping_method': shipping_method,
        'order_total': total,
        'order_kwargs': {},
        'payment_kwargs': {}}


class TestApplyTaxesToSubmission(TestCase):

    def test_sets_taxes_on_basket_and_shipping_method(self):
        submission = build_submission()
        self.assertFalse(submission['basket'].is_tax_known)
        self.assertFalse(submission['shipping_method'].is_tax_known)

        with mock.patch('requests.request') as mocked_request:
            mocked_response = mock.Mock()
            mocked_response.status_code = 200
            mocked_response.json = mock.Mock(
                return_value=responses.SUCCESS)
            mocked_request.return_value = mocked_response

            avalara.apply_taxes_to_submission(submission)

        self.assertTrue(submission['basket'].is_tax_known)
        self.assertTrue(submission['shipping_method'].is_tax_known)
