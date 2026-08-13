"""
Pytest unit tests for category seed data and enums.
"""
import pytest
from app.models.enums import SEED_CATEGORIES, CategoryGroup


def test_seed_categories_have_both_groups():
    """Seed data should contain both business and personal categories."""
    assert CategoryGroup.BUSINESS in SEED_CATEGORIES
    assert CategoryGroup.PERSONAL in SEED_CATEGORIES


def test_seed_categories_not_empty():
    """Each group should have at least 5 categories."""
    for group, cats in SEED_CATEGORIES.items():
        assert len(cats) >= 5, f"{group.value} has too few categories"


def test_seed_categories_have_required_fields():
    """Each seed category should have name, icon, and color."""
    for group, cats in SEED_CATEGORIES.items():
        for cat in cats:
            assert "name" in cat, f"Missing name in {group.value} category"
            assert "icon" in cat, f"Missing icon in {group.value} category: {cat['name']}"
            assert "color" in cat, f"Missing color in {group.value} category: {cat['name']}"
            assert cat["color"].startswith("#"), f"Color should be hex in {cat['name']}"


def test_seed_category_names_are_unique():
    """All category names across all groups should be unique."""
    all_names = []
    for group, cats in SEED_CATEGORIES.items():
        for cat in cats:
            all_names.append(cat["name"])
    assert len(all_names) == len(set(all_names)), "Duplicate category names found"


def test_expected_business_categories():
    """Verify key business categories are present."""
    business_names = [c["name"] for c in SEED_CATEGORIES[CategoryGroup.BUSINESS]]
    assert "Office Supplies" in business_names
    assert "Travel" in business_names
    assert "Software & SaaS" in business_names


def test_expected_personal_categories():
    """Verify key personal categories are present."""
    personal_names = [c["name"] for c in SEED_CATEGORIES[CategoryGroup.PERSONAL]]
    assert "Groceries" in personal_names
    assert "Healthcare" in personal_names
    assert "Subscriptions" in personal_names
