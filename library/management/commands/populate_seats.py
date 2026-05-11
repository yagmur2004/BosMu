from django.core.management.base import BaseCommand
from library.models import Library, Zone, Seat


class Command(BaseCommand):
    help = "Kütüphaneye 144 koltuğu otomatik ekler (Sol 93 + Orta 22 + Sağ 29)"

    def handle(self, *args, **options):
        # Kütüphane var mı kontrol et, yoksa oluştur
        library, created = Library.objects.get_or_create(
            name="Üniversite Kütüphanesi",
            defaults={
                "address": "İstanbul",
                "opening_time": "08:00",
                "closing_time": "20:00",
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"✓ Kütüphane oluşturuldu: {library.name}"))
        else:
            self.stdout.write(self.style.WARNING(f"ℹ Kütüphane zaten var: {library.name}"))

        # Bölgeler
        zones_data = [
            ("Sol Bölge", "silent"),
            ("Orta Bölge", "computer"),
            ("Sağ Bölge", "group"),
        ]

        zones = {}
        for zone_name, zone_type in zones_data:
            zone, _ = Zone.objects.get_or_create(
                library=library,
                name=zone_name,
                defaults={"zone_type": zone_type}
            )
            zones[zone_name] = zone

        self.stdout.write(self.style.SUCCESS(f"✓ {len(zones)} bölge oluşturuldu"))

        # Koltuk sayaçları
        seat_codes = {
            "Sol Bölge": [f"L-{i:03d}" for i in range(1, 94)],  # L-001 to L-093
            "Orta Bölge": [f"M-{i:03d}" for i in range(1, 23)],  # M-001 to M-022
            "Sağ Bölge": [f"R-{i:03d}" for i in range(1, 30)],   # R-001 to R-029
        }

        total_added = 0
        for zone_name, codes in seat_codes.items():
            zone = zones[zone_name]
            for code in codes:
                seat, created = Seat.objects.get_or_create(
                    zone=zone,
                    code=code,
                    defaults={"is_active": True}
                )
                if created:
                    total_added += 1

            self.stdout.write(
                self.style.SUCCESS(f"✓ {zone_name}: {len(codes)} koltuk")
            )

        self.stdout.write(
            self.style.SUCCESS(f"\n✅ Toplam {total_added} yeni koltuk veritabanına eklendi!")
        )
        self.stdout.write(
            self.style.SUCCESS(f"Şimdi admin panelini kontrol edebilirsin: http://127.0.0.1:8000/admin/")
        )
