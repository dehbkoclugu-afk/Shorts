import unittest

from fasttrack.src.compliance import check_text


class ComplianceTests(unittest.TestCase):
    def assertBlocked(self, text: str, rule_id: str):
        findings = check_text(text)
        self.assertTrue(any(item.rule_id == rule_id for item in findings), findings)

    def test_blocks_guaranteed_weight_loss(self):
        self.assertBlocked("Bu yöntemle kesin kilo ver.", "guaranteed_weight_loss")

    def test_blocks_disease_treatment(self):
        self.assertBlocked("Bu plan diyabeti iyileştirir.", "disease_treatment")

    def test_blocks_fake_testimonial(self):
        self.assertBlocked("This app made me lose 10 lbs.", "fake_testimonial")

    def test_blocks_minor_targeting(self):
        self.assertBlocked("Fast fasting for teenagers.", "minor_targeting")

    def test_blocks_universal_exact_timing(self):
        self.assertBlocked(
            "Autophagy always starts at 16 hours.", "universal_exact_timing"
        )

    def test_requires_metabolic_estimate_disclaimer(self):
        self.assertBlocked("Otofaji sürecini saat saat izle.", "metabolic_estimate")

    def test_allows_cautious_metabolic_copy(self):
        findings = check_text(
            "Otofaji aşamaları genel tahmindir ve zamanlama kişiden kişiye değişir."
        )
        self.assertEqual(findings, [])

    def test_allows_ordinary_product_demo(self):
        findings = check_text(
            "FastTrack başlangıç ve bitiş saatini gösterir; su takibini aynı yerde tutar."
        )
        self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()

