"""0396: the search page's period to the day, and the rule a period becomes."""

from __future__ import annotations

from datetime import date

from media_hygiene.classify.rules.kinds import RuleMatch
from media_hygiene.config.classify_rules import ClassifyRule
from media_hygiene.search.rule_models import PeriodRuleIn, dated_rules
from media_hygiene.search.views import SearchAsked
from media_hygiene.services.rule_trial import tried_rules


def test_the_days_name_the_search_as_a_rule_does() -> None:
    """Two days, one day alone, reversed days, a year alone."""
    two = SearchAsked(day_from=date(2017, 8, 5), day_to=date(2017, 8, 6))
    assert two.found_by() == "2017-08-05..2017-08-06"
    assert two.query().filters.days == (date(2017, 8, 5), date(2017, 8, 6))
    one = SearchAsked(day_to=date(2017, 8, 5))
    assert one.found_by() == "2017-08-05"
    reversed_days = SearchAsked(day_from=date(2017, 8, 6), day_to=date(2017, 8, 5))
    assert reversed_days.period() == (date(2017, 8, 5), date(2017, 8, 6))
    year = SearchAsked(year_from=2017)
    assert year.found_by() == "2017-2017"
    assert year.period() == (date(2017, 1, 1), date(2017, 12, 31))
    assert SearchAsked().period() is None


def test_a_period_rule_is_a_date_range_rule() -> None:
    """The days put in order, the folder's slashes trimmed."""
    asked = PeriodRuleIn(
        name=" Wedding ",
        first=date(2017, 8, 6),
        last=date(2017, 8, 5),
        category="/Parties/Weddings/",
    )
    rule = asked.rule()
    assert (rule.name, rule.dates, rule.category) == (
        "Wedding",
        "2017-08-05..2017-08-06",
        "Parties/Weddings",
    )
    assert rule.keep_folders


def _dated(name: str, dates: str) -> ClassifyRule:
    return ClassifyRule(
        name=name, match=RuleMatch.DATE_RANGE, dates=dates, category=name
    )


EXISTING = ClassifyRule(name="Existing folders", match=RuleMatch.EXISTING_FOLDER)


def test_the_date_rules_are_listed_latest_first() -> None:
    """Only the date rules, by their first day, the latest first."""
    rules = (
        _dated("Old", "2005-01-01..2005-01-02"),
        EXISTING,
        _dated("New", "2019-07-12..2019-07-19"),
    )
    assert [line["name"] for line in dated_rules(rules)] == ["New", "Old"]


def test_the_rule_tried_goes_where_saving_puts_it() -> None:
    """Above Existing folders; in place of the one it replaces; a same name left out."""
    old = _dated("Old", "2005-01-01..2005-01-02")
    new = _dated("New", "2019-07-12..2019-07-19")
    assert tried_rules((old, EXISTING), new, "") == (old, new, EXISTING)
    assert tried_rules((EXISTING, old), new, "Old") == (EXISTING, new)
    renamed = _dated("Old", "2006-01-01..2006-01-02")
    assert tried_rules((old, EXISTING), renamed, "") == (renamed, EXISTING)
    assert tried_rules((old,), new, "") == (old, new)
