"""
Fees model defined here.
"""
from django.conf import settings
from django.db import models
from core.mixins.models import (TimeStampFlagModelMixin)
from django.utils.translation import ugettext_lazy as _
from django.contrib.postgres.fields import (ArrayField,)


class OrderVariable(TimeStampFlagModelMixin,models.Model):
    """
    Class implementing  order variables
    """
    PROGRAM_TIER_GOLD = 'gold'
    PROGRAM_TIER_SILVER = 'silver'
    PROGRAM_TIER_BRONZE = 'bronze'
    PROGRAM_TIER_CHOICES = (
        (PROGRAM_TIER_GOLD, _('Gold')),
        (PROGRAM_TIER_SILVER, _('Silver')),
        (PROGRAM_TIER_BRONZE, _('Bronze')),
        
    )
    
    tier = models.CharField(verbose_name=_("Tier"), max_length=255, choices=PROGRAM_TIER_CHOICES)
    mcsp_fee = models.CharField(verbose_name=_("MCSP Fee(%)"), max_length=255,blank=True, null=True)
    net_7_14 = models.CharField(verbose_name=_("Net 7-14(%)"), max_length=255,blank=True, null=True)
    net_14_30 = models.CharField(verbose_name=_("Net 14-30(%)"), max_length=255,blank=True, null=True)
    cash = models.CharField(verbose_name=_("Cash(%)"), max_length=255,blank=True, null=True)
    transportation_fee = models.CharField(verbose_name=_("Transportation Fee/Mile($)"), max_length=255,blank=True, null=True)
    
    def __str__(self):
        return self.tier

    class Meta:
        verbose_name = _('Order Variable')
        verbose_name_plural = _('Order Variables')      


class CustomInventoryVariable(TimeStampFlagModelMixin,models.Model):
    """
    Class implementing  CustomInventory variables
    """
    PROGRAM_TIER_GOLD = 'gold'
    PROGRAM_TIER_SILVER = 'silver'
    PROGRAM_TIER_BRONZE = 'bronze'
    PROGRAM_TIER_NO_TIER = 'no_tier'
    PROGRAM_TIER_CHOICES = (
        (PROGRAM_TIER_GOLD, _('Gold')),
        (PROGRAM_TIER_SILVER, _('Silver')),
        (PROGRAM_TIER_BRONZE, _('Bronze')),
        (PROGRAM_TIER_NO_TIER, _('No Tier')),
    )
    PROGRAM_TYPE_IFP = 'ifp'
    PROGRAM_TYPE_IBP = 'ibp'
    PROGRAM_TYPE_CHOICES = (
        (PROGRAM_TYPE_IFP, _('IFP Program')),
        (PROGRAM_TYPE_IBP, _('IBP Program')),
    )

    program_type = models.CharField(
        verbose_name=_("Program Type"),
        max_length=255,
        choices=PROGRAM_TYPE_CHOICES
    )
    tier = models.CharField(
        verbose_name=_("Tier"),
        max_length=255,
        choices=PROGRAM_TIER_CHOICES
    )
    mcsp_fee_flower_tops = models.DecimalField(
        verbose_name=_("MCSP Fee - Flower Tops ($/lb)"),
        # help_text='This fee will be for Flowers.',
        decimal_places=2,
        max_digits=6,
        blank=True,
        null=True
    )
    mcsp_fee_flower_smalls = models.DecimalField(
        verbose_name=_("MCSP Fee - Flower Smalls ($/lb)"),
        # help_text='This fee will be for Flowers.',
        decimal_places=2,
        max_digits=6,
        blank=True,
        null=True
    )
    mcsp_fee_trims = models.DecimalField(
        verbose_name=_("MCSP Fee - Trims ($/lb)"),
        # help_text='This fee will be for Trims.',
        decimal_places=2,
        max_digits=6,
        blank=True,
        null=True
    )
    mcsp_fee_concentrates = models.DecimalField(
        verbose_name=_("MCSP Fee - Concentrates (%)"),
        # help_text='This percentage will be used in MCSP Fee calculation for Concentrates.',
        decimal_places=2,
        max_digits=6,
        blank=True,
        null=True
    )
    mcsp_fee_isolates = models.DecimalField(
        verbose_name=_("MCSP Fee - Isolates (%)"),
        # help_text='This percentage will be used in MCSP Fee calculation for Isolates.',
        decimal_places=2,
        max_digits=6,
        blank=True,
        null=True
    )
    mcsp_fee_terpenes = models.DecimalField(
        verbose_name=_("MCSP Fee - Terpenes (%)"),
        # help_text='This percentage will be used in MCSP Fee calculation for Terpenes.',
        decimal_places=2,
        max_digits=6,
        blank=True,
        null=True
    )
    mcsp_fee_clones = models.DecimalField(
        verbose_name=_("MCSP Fee - Clones ($/pcs)"),
        # help_text='This fee will be used for Clones',
        decimal_places=2,
        max_digits=6,
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.program_type

    class Meta:
        verbose_name = _('Vendor Inventory Variable')
        verbose_name_plural = _('Vendor Inventory Variables')


class TaxVariable(TimeStampFlagModelMixin,models.Model):
    """
    Class implementing  Tax variables
    """
    dried_flower_tax = models.CharField(verbose_name=_("Dried Flower Tax"), max_length=255,blank=True, null=True)
    dried_leaf_tax = models.CharField(verbose_name=_("Dried Leaf Tax"), max_length=255,blank=True, null=True)
    fresh_plant_tax = models.CharField(verbose_name=_("Fresh Plant Tax"), max_length=255,blank=True, null=True)
    dried_flower_tax_item = models.CharField(verbose_name=_("Dried Flower Tax Item"), max_length=255, blank=True, null=True)
    dried_leaf_tax_item = models.CharField(verbose_name=_("Dried Leaf Tax Item"), max_length=255, blank=True, null=True)
    fresh_plant_tax_item = models.CharField(verbose_name=_("Fresh Plant Tax Item"), max_length=255, blank=True, null=True)
    # cultivar_tax = models.CharField(verbose_name=_("Cultivar Tax"), max_length=255,blank=True, null=True)
    # trim_tax = models.CharField(verbose_name=_("Trim Tax"), max_length=255,blank=True, null=True)
    # cultivar_tax_item = models.CharField(verbose_name=_("Cultivar Tax Item"), max_length=255, blank=True, null=True)
    # trim_tax_item = models.CharField(verbose_name=_("Trim Tax Item"), max_length=255, blank=True, null=True)

    def __str__(self):
        return f'{self.dried_flower_tax} | {self.dried_leaf_tax} | {self.fresh_plant_tax}'

    class Meta:
        verbose_name = _('Tax Variable')
        verbose_name_plural = _('Tax Variables')


class CampaignVariable(TimeStampFlagModelMixin,models.Model):
    """
    Zoho campaign variables.
    """
    from_email = models.EmailField(verbose_name=_("From Email"), max_length=255, blank=True, null=True)
    mailing_list_id = ArrayField(models.CharField(max_length=255), blank=True, null=True)

    class Meta:
        verbose_name = _('Campaign Variable')
        verbose_name_plural = _('Campaign Variables')


class VendorInventoryDefaultAccounts(TimeStampFlagModelMixin,models.Model):
    """
    Class implementing  CustomInventory variables
    """
    ZOHO_ORG_EFD = 'efd'
    ZOHO_ORG_EFL = 'efl'
    ZOHO_ORG_EFN = 'efn'
    ZOHO_ORG_CHOICES = (
        (ZOHO_ORG_EFD, _('Thrive Society (EFD LLC)')),
        (ZOHO_ORG_EFL, _('Eco Farm Labs (EFL LLC)')),
        (ZOHO_ORG_EFN, _('Eco Farm Nursery (EFN LLC)')),
    )

    zoho_organization = models.CharField(_('Zoho Organization'), unique=True, choices=ZOHO_ORG_CHOICES, max_length=20)

    sales_account = models.CharField(verbose_name=_("Default Sales Account"), max_length=255, null=True, blank=True)
    purchase_account = models.CharField(verbose_name=_("Default Purchase Account"), max_length=255, null=True, blank=True)
    inventory_account = models.CharField(verbose_name=_("Default inventory Account"), max_length=255, null=True, blank=True)

    def __str__(self):
        return self.zoho_organization

    def get_new_item_accounts_dict(self):
        resp = {}
        if self.sales_account:
            resp['account_id'] = self.sales_account
        if self.purchase_account:
            resp['purchase_account_id'] = self.purchase_account
        if self.inventory_account:
            resp['inventory_account_id'] = self.inventory_account
        return resp

    class Meta:
        verbose_name = _('Vendor Inventory Default Accounts')
        verbose_name_plural = _('Vendor Inventory Default Accounts')


class VendorInventoryCategoryAccounts(TimeStampFlagModelMixin,models.Model):
    """
    Class implementing  CustomInventory variables
    """
    CATEGORY_NAME_CHOICES = (
        ('Flower - Tops', _('Flower - Tops')),
        ('Flower - Small', _('Flower - Small')),
        ('Trim', _('Trim')),
        ('Isolates - CBD', _('Isolates - CBD')),
        ('Isolates - THC', _('Isolates - THC')),
        ('Isolates - CBG', _('Isolates - CBG')),
        ('Isolates - CBN', _('Isolates - CBN')),
        ('Crude Oil - THC', _('Crude Oil - THC')),
        ('Crude Oil - CBD', _('Crude Oil - CBD')),
        ('Distillate Oil - THC', _('Distillate Oil - THC')),
        ('Distillate Oil - CBD', _('Distillate Oil - CBD')),
        ('Shatter', _('Shatter')),
        ('Sauce', _('Sauce')),
        ('Crumble', _('Crumble')),
        ('Kief', _('Kief')),
        ('Terpenes - Cultivar Specific', _('Terpenes - Cultivar Specific')),
        ('Terpenes - Cultivar Blended', _('Terpenes - Cultivar Blended')),
        ('Clones', _('Clones')),
    )
    default_accounts = models.ForeignKey(VendorInventoryDefaultAccounts, verbose_name=_('Default Accounts'), related_name='category_accounts_set', on_delete=models.CASCADE)
    item_category = models.CharField(_('Item Category'), choices=CATEGORY_NAME_CHOICES, max_length=50)

    sales_account = models.CharField(verbose_name=_("Sales Account"), max_length=255, null=True, blank=True)
    purchase_account = models.CharField(verbose_name=_("Purchase Account"), max_length=255, null=True, blank=True)
    inventory_account = models.CharField(verbose_name=_("inventory Account"), max_length=255, null=True, blank=True)

    def __str__(self):
        return self.item_category

    def get_new_item_accounts_dict(self):
        resp = {}
        if self.sales_account:
            resp['account_id'] = self.sales_account
        if self.purchase_account:
            resp['purchase_account_id'] = self.purchase_account
        if self.inventory_account:
            resp['inventory_account_id'] = self.inventory_account
        return resp

    class Meta:
        unique_together = (('default_accounts', 'item_category'), )
        verbose_name = _('Vendor Inventory Category Accounts')
        verbose_name_plural = _('Vendor Inventory Category Accounts')
