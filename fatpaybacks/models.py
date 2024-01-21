import json

from datetime import timedelta
from django.db import models
from afat.models import FleetType, Fat
from allianceauth.eveonline.models import EveAllianceInfo, EveCorporationInfo
from django.utils import timezone
from django.db.models import F
from django.db.models.aggregates import Count, Sum
from taxtools.models import CorporateTaxCredits
from moons.models import InvoiceRecord


class FatPaybackSetup(models.Model):
    """
        Fats = Tax Credits
    """
    alliances = models.ManyToManyField(EveAllianceInfo, blank=True)

    name = models.CharField(max_length=500)

    time_to_look_back = models.IntegerField(default=30)

    types_in_active = models.ManyToManyField(
        FleetType,
        blank=True,
        related_name="payback_types"
    )
    active_threshold = models.IntegerField(default=15)

    value_from_moon_mining = models.BooleanField(default=True)
    percentage_of_moon_mininig = models.FloatField(default=0.1)

    def get_character_fleet_data(self):
        start_date = timezone.now() - timedelta(days=30)
        return Fat.objects.filter(
            # Only the selected types
            fatlink__link_type__in=self.types_in_active.all(),
            # within the time period
            fatlink__created__gte=start_date,
            # only mains in alliances chosen
            character__character_ownership__user__profile__main_character__alliance_id__in=self.alliances.all(
            ).values_list("alliance_id", flat=True)
        ).values(
            # Group by main character
            "character__character_ownership__user__profile__main_character__character_id",
        ).distinct().annotate(
            # Count fats per main
            fats=Count("id"),
            # corp id for simplicity
            corp=F(
                "character__character_ownership__user__profile__main_character__corporation_id")
        ).filter(
            # Only those that match the threshold
            fats__gte=self.active_threshold
        )

    def get_active_counts_per_corp(self):
        char_data = self.get_character_fleet_data()
        return char_data.values(
            "corp"
        ).distinct().annotate(
            actives=Count(
                "character__character_ownership__user__profile__main_character__character_id")
        )

    def get_income_total(self):
        total_share = 0
        if self.value_from_moon_mining:
            moon_income = InvoiceRecord.objects.filter(
                end_date__gte=timezone.now()-timedelta(days=self.time_to_look_back)
            ).aggregate(total_mined_value=Sum("total_mined"))
            total_share += float(moon_income['total_mined_value']
                                 ) * self.percentage_of_moon_mininig
        return total_share

    def get_payment_per_corp(self):
        corp_data = self.get_active_counts_per_corp()
        total_share = self.get_income_total()

        total_active_chars = corp_data.aggregate(total_active_chars=Sum("actives"))[
            'total_active_chars']
        single_share = round(total_share / total_active_chars)

        for c in corp_data:
            c['credit'] = single_share * c['actives']
        return corp_data, total_active_chars, single_share

    def credit_corps(self):
        payment_details, total_active_chars, single_share = self.get_payment_per_corp()

        for c in payment_details:
            credits, _ = CorporateTaxCredits.objects.get_or_create(
                corp=EveCorporationInfo.objects.get(corporation_id=c['corp'])
            )
            credits.credit_balance += c['credit']
            credits.save()

        FatPaybackRecord.objects.create(
            config=self,
            data=json.dumps(list(payment_details)),
            total_actives=total_active_chars,
            isk_per_active=single_share
        )

        return payment_details


class FatPaybackRecord(models.Model):
    config = models.ForeignKey(FatPaybackSetup, on_delete=models.CASCADE)
    data = models.TextField(blank=True)
    total_actives = models.IntegerField(default=0)
    isk_per_active = models.DecimalField(
        max_digits=20, decimal_places=2, default=0)
    actioned = models.DateTimeField(auto_now=True)
