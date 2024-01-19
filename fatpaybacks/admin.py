from django.contrib import admin
from .models import FatPaybackSetup, FatPaybackRecord


def generate_formatter(name, str_format):
    def formatter(o): return str_format.format(getattr(o, name) or 0)
    formatter.short_description = name
    formatter.admin_order_field = name
    return formatter


@admin.register(FatPaybackSetup)
class FATPaybackAdmin(admin.ModelAdmin):
    filter_horizontal = ('alliances', 'types_in_active')
    select_related = True


@admin.register(FatPaybackRecord)
class FATPaybackRecordAdmin(admin.ModelAdmin):
    list_display = ('actioned', 'total_actives', ('isk_per_active', "{:,}"))
    select_related = True

    # generate a custom formater cause i am lazy...
    def __init__(self, *args, **kwargs):
        all_fields = []
        for f in self.list_display:
            if isinstance(f, str):
                all_fields.append(f)
            else:
                new_field_name = "_" + f[0]
                setattr(self, new_field_name, generate_formatter(f[0], f[1]))
                all_fields.append(new_field_name)
        self.list_display = all_fields

        super().__init__(*args, **kwargs)
