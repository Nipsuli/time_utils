import datetime
import pytz
import pytest
from freezegun import freeze_time
from dateutil import parser as dateutil_parser
from dateutil.tz import tzoffset
from unittest.mock import patch

import time_utils


def test_end_of_day_no_tz():
    dat = datetime.datetime(2017, 11, 12, 3, 5, 4)
    assert time_utils.end_of_day(dat, 'Europe/Helsinki') == pytz.timezone('Europe/Helsinki').localize(datetime.datetime(2017, 11, 12, 23, 59, 59))


def test_end_of_day_with_tz():
    dat = datetime.datetime(2017, 11, 12, 3, 5, 4, tzinfo=pytz.timezone('Europe/Helsinki'))
    assert time_utils.end_of_day(dat, 'Europe/Helsinki') == pytz.timezone('Europe/Helsinki').localize(datetime.datetime(2017, 11, 12, 23, 59, 59))


def test_end_of_day_with_tz_ignores_original_tz():
    dat = datetime.datetime(2017, 11, 12, 3, 5, 4, tzinfo=pytz.timezone('Asia/Singapore'))
    assert time_utils.end_of_day(dat, 'Europe/Helsinki') == pytz.timezone('Europe/Helsinki').localize(datetime.datetime(2017, 11, 12, 23, 59, 59))


def test_end_of_day_with_date():
    dat = datetime.date(2017, 11, 12)
    assert time_utils.end_of_day(dat, 'Europe/Helsinki') == pytz.timezone('Europe/Helsinki').localize(datetime.datetime(2017, 11, 12, 23, 59, 59))


def test_beginning_of_day():
    dat = datetime.datetime(2017, 11, 12, 3, 5, 4)
    assert time_utils.beginning_of_day(dat, 'Europe/Helsinki') == pytz.timezone('Europe/Helsinki').localize(datetime.datetime(2017, 11, 12, 0, 0))


def test_beginning_of_day_with_tz():
    dat = datetime.datetime(2017, 11, 12, 3, 5, 4, tzinfo=pytz.timezone('Europe/Helsinki'))
    assert time_utils.beginning_of_day(dat, 'Europe/Helsinki') == pytz.timezone('Europe/Helsinki').localize(datetime.datetime(2017, 11, 12, 0, 0))


def test_beginning_of_day_with_date():
    dat = datetime.date(2017, 11, 12)
    assert time_utils.beginning_of_day(dat, 'Europe/Helsinki') == pytz.timezone('Europe/Helsinki').localize(datetime.datetime(2017, 11, 12, 0, 0))


@freeze_time("2017-11-13")
def test_get_current_utc_offset_winter():
    assert 2 == time_utils.get_current_utc_offset('Europe/Helsinki')


@freeze_time("2017-06-13")
def test_get_current_utc_offset_summer():
    assert 3 == time_utils.get_current_utc_offset('Europe/Helsinki')


def test_now():
    time_now = time_utils.now()
    assert type(time_now) == datetime.datetime
    assert time_now.tzinfo == pytz.utc


def test_min_datetime():
    assert datetime.datetime(1, 1, 1, 0, 0, 0, tzinfo=pytz.utc) == time_utils.min_datetime()


def test_max_datetime():
    assert datetime.datetime(9999, 12, 31, 23, 59, 59, 999999, tzinfo=pytz.utc) == time_utils.max_datetime()


def test_timedelta():
    assert datetime.datetime(2017, 11, 1) == time_utils.timedelta(datetime.datetime(2017, 11, 2), days=-1)


def test_timedelta_with_date():
    assert datetime.date(2017, 11, 1) == time_utils.timedelta(datetime.date(2017, 11, 2), days=-1)


@freeze_time("2017-11-13 12:15:01")
def test_time_ago():
    ago = time_utils.time_ago(days=4)
    assert 2017 == ago.year
    assert 11 == ago.month
    assert 9 == ago.day
    assert 12 == ago.hour
    assert 15 == ago.minute
    assert 1 == ago.second
    assert pytz.utc == ago.tzinfo


def test_microsoft_timezone_to_timezone():
    assert 'Europe/Kiev' == time_utils.microsoft_timezone_to_timezone('FLE Standard Time')


def test_timezone_to_microsoft_timezone():
    assert 'FLE Standard Time' == time_utils.timezone_to_microsoft_timezone('Europe/Helsinki')


def test_ensure_tz_object_standard_format():
    assert pytz.timezone('Europe/Helsinki') == time_utils.ensure_tz_object('Europe/Helsinki')


def test_ensure_tz_object_with_tz_obj():
    assert pytz.timezone('Europe/Helsinki') == time_utils.ensure_tz_object(pytz.timezone('Europe/Helsinki'))


def test_ensure_tz_object_ms_format():
    assert pytz.timezone('Europe/Kiev') == time_utils.ensure_tz_object('FLE Standard Time')


def test_ensure_tz_object_raises():
    with pytest.raises(pytz.exceptions.UnknownTimeZoneError) as excinfo:
        time_utils.ensure_tz_object('asd asd')

    assert "pytz.exceptions.UnknownTimeZoneError: 'asd asd'" in str(excinfo)


def test_localize():
    datetime_obj = datetime.datetime(2017, 11, 13, 12, 15, 1)
    assert "2017-11-13T12:15:01+02:00" == time_utils.localize(datetime_obj, 'FLE Standard Time').isoformat()


@freeze_time("2017-11-12 23:00:01")
def test_today():
    assert datetime.date(2017, 11, 13) == time_utils.today('Europe/Helsinki')
    assert datetime.date(2017, 11, 12) == time_utils.today('UTC')


def test_datetime_from_timestamp():
    t0 = time_utils.datetime_from_timestamp(1511876065)
    t1 = time_utils.datetime_from_timestamp(1511876065, 'UTC')
    t2 = time_utils.datetime_from_timestamp(1511876065, 'Europe/Helsinki')
    t3 = time_utils.datetime_from_timestamp(1511876065000, is_ms=True)
    assert datetime.datetime(2017, 11, 28, 13, 34, 25, tzinfo=pytz.utc) == t0 == t1 == t2 == t3
    assert t0.tzinfo == t1.tzinfo == pytz.timezone('UTC')
    helsinki_tz = pytz.timezone('Europe/Helsinki').localize(datetime.datetime(2017, 11, 28)).tzinfo
    assert t2.tzinfo == helsinki_tz
    assert t2.tzinfo.zone == 'Europe/Helsinki'


def test_localize_with_tz_aware():
    datetime_obj = datetime.datetime(2017, 11, 13, 12, 15, 1, tzinfo=pytz.utc)
    with pytest.raises(ValueError) as excinfo:
        time_utils.localize(datetime_obj, 'FLE Standard Time')

    assert 'Not naive datetime (tzinfo is already set)' in str(excinfo.value)


def test_localize_overwrite():
    datetime_obj = datetime.datetime(2017, 11, 13, 12, 15, 1, tzinfo=pytz.utc)
    assert "2017-11-13T12:15:01+02:00" == time_utils.localize(datetime_obj, 'FLE Standard Time', overwrite=True).isoformat()


@patch('dateutil.parser.parse', autospec=True, side_effect=dateutil_parser.parse)
def test_datetime_parse_zero_time(dateuil_spy):
    assert time_utils.datetime_parse("0000-00-00T00:00:00.000Z") == datetime.datetime(1, 1, 1, 0, 0, 0, tzinfo=pytz.utc)
    assert dateuil_spy.call_count == 0


@patch('dateutil.parser.parse', autospec=True, side_effect=dateutil_parser.parse)
def test_datetime_parse_no_tz(dateuil_spy):
    assert time_utils.datetime_parse("2017-11-13T12:15:01") == datetime.datetime(2017, 11, 13, 12, 15, 1)
    assert dateuil_spy.call_count == 0


@patch('dateutil.parser.parse', autospec=True, side_effect=dateutil_parser.parse)
def test_datetime_parse_no_tz_default_tz(dateuil_spy):
    assert time_utils.datetime_parse("2017-11-13T12:15:01", "UTC") == datetime.datetime(2017, 11, 13, 12, 15, 1, tzinfo=pytz.utc)
    assert dateuil_spy.call_count == 0


@patch('dateutil.parser.parse', autospec=True, side_effect=dateutil_parser.parse)
def test_datetime_parse_no_tz_micro(dateuil_spy):
    assert time_utils.datetime_parse("2017-11-13T12:15:01.021000") == datetime.datetime(2017, 11, 13, 12, 15, 1, 21000)
    assert dateuil_spy.call_count == 0


@patch('dateutil.parser.parse', autospec=True, side_effect=dateutil_parser.parse)
def test_datetime_parse_utc(dateuil_spy):
    assert time_utils.datetime_parse("2017-11-13T12:15:01Z") == datetime.datetime(2017, 11, 13, 12, 15, 1, tzinfo=pytz.utc)
    assert dateuil_spy.call_count == 0


@patch('dateutil.parser.parse', autospec=True, side_effect=dateutil_parser.parse)
def test_datetime_parse_utc_micro(dateuil_spy):
    assert time_utils.datetime_parse("2017-11-13T12:15:01.124000Z") == datetime.datetime(2017, 11, 13, 12, 15, 1, 124000, tzinfo=pytz.utc)
    assert dateuil_spy.call_count == 0


@patch('dateutil.parser.parse', autospec=True, side_effect=dateutil_parser.parse)
def test_datetime_parse_utc_ms(dateuil_spy):
    assert time_utils.datetime_parse("2017-11-13T12:15:01.124Z") == datetime.datetime(2017, 11, 13, 12, 15, 1, 124000, tzinfo=pytz.utc)
    assert dateuil_spy.call_count == 0


@patch('dateutil.parser.parse', autospec=True, side_effect=dateutil_parser.parse)
def test_datetime_parse_tz_offset_positive(dateuil_spy):
    assert time_utils.datetime_parse("2017-11-13T12:15:01+02:00") == datetime.datetime(2017, 11, 13, 12, 15, 1, tzinfo=tzoffset(None, 7200))
    assert dateuil_spy.call_count == 0


@patch('dateutil.parser.parse', autospec=True, side_effect=dateutil_parser.parse)
def test_datetime_parse_tz_offset_positive_micro(dateuil_spy):
    assert time_utils.datetime_parse("2017-11-13T12:15:01.023000+02:00") == datetime.datetime(2017, 11, 13, 12, 15, 1, 23000, tzinfo=tzoffset(None, 7200))
    assert dateuil_spy.call_count == 0


@patch('dateutil.parser.parse', autospec=True, side_effect=dateutil_parser.parse)
def test_datetime_parse_tz_offset_negative(dateuil_spy):
    assert time_utils.datetime_parse("2017-11-13T12:15:01-02:00") == datetime.datetime(2017, 11, 13, 12, 15, 1, tzinfo=tzoffset(None, -7200))
    assert dateuil_spy.call_count == 0


@patch('dateutil.parser.parse', autospec=True, side_effect=dateutil_parser.parse)
def test_datetime_parse_tz_offset_negative_micro(dateuil_spy):
    assert time_utils.datetime_parse("2017-11-13T12:15:01.321000-02:00") == datetime.datetime(2017, 11, 13, 12, 15, 1, 321000, tzinfo=tzoffset(None, -7200))
    assert dateuil_spy.call_count == 0


@patch('dateutil.parser.parse', autospec=True, side_effect=dateutil_parser.parse)
def test_datetime_parse_tz_short_offset_positive(dateuil_spy):
    assert time_utils.datetime_parse("2017-11-13T12:15:01+0600") == datetime.datetime(2017, 11, 13, 12, 15, 1, tzinfo=tzoffset(None, 21600))
    assert dateuil_spy.call_count == 0


@patch('dateutil.parser.parse', autospec=True, side_effect=dateutil_parser.parse)
def test_datetime_parse_tz_short_offset_positive_default_tz_does_not_overwrite(dateuil_spy):
    assert time_utils.datetime_parse("2017-11-13T12:15:01+0600", "UTC") == datetime.datetime(2017, 11, 13, 12, 15, 1, tzinfo=tzoffset(None, 21600))
    assert dateuil_spy.call_count == 0


@patch('dateutil.parser.parse', autospec=True, side_effect=dateutil_parser.parse)
def test_datetime_parse_tz_short_offset_positive_micro(dateuil_spy):
    assert time_utils.datetime_parse("2017-11-13T12:15:01.000213+0600") == datetime.datetime(2017, 11, 13, 12, 15, 1, 213, tzinfo=tzoffset(None, 21600))
    assert dateuil_spy.call_count == 0


@patch('dateutil.parser.parse', autospec=True, side_effect=dateutil_parser.parse)
def test_datetime_parse_tz_short_offset_negative(dateuil_spy):
    assert time_utils.datetime_parse("2017-11-13T12:15:01-0600") == datetime.datetime(2017, 11, 13, 12, 15, 1, tzinfo=tzoffset(None, -21600))
    assert dateuil_spy.call_count == 0


@patch('dateutil.parser.parse', autospec=True, side_effect=dateutil_parser.parse)
def test_datetime_parse_tz_short_offset_negative_micro(dateuil_spy):
    assert time_utils.datetime_parse("2017-11-13T12:15:01.999999-0600") == datetime.datetime(2017, 11, 13, 12, 15, 1, 999999, tzinfo=tzoffset(None, -21600))
    assert dateuil_spy.call_count == 0


@patch('dateutil.parser.parse', autospec=True, side_effect=dateutil_parser.parse)
def test_datetime_parse_no_tz_no_seconds(dateuil_spy):
    assert time_utils.datetime_parse("2017-11-13T12:15") == datetime.datetime(2017, 11, 13, 12, 15)
    assert dateuil_spy.call_count == 0


@patch('dateutil.parser.parse', autospec=True, side_effect=dateutil_parser.parse)
def test_datetime_parse_utc_no_seconds(dateuil_spy):
    assert time_utils.datetime_parse("2017-11-13T12:15Z") == datetime.datetime(2017, 11, 13, 12, 15, tzinfo=pytz.utc)
    assert dateuil_spy.call_count == 0


@patch('dateutil.parser.parse', autospec=True, side_effect=dateutil_parser.parse)
def test_datetime_parse_tz_offset_positive_no_seconds(dateuil_spy):
    assert time_utils.datetime_parse("2017-11-13T12:15+02:00") == datetime.datetime(2017, 11, 13, 12, 15, tzinfo=tzoffset(None, 7200))
    assert dateuil_spy.call_count == 0


@patch('dateutil.parser.parse', autospec=True, side_effect=dateutil_parser.parse)
def test_datetime_parse_not_matching(dateuil_spy):
    assert time_utils.datetime_parse("Wed, 06 Sep 2017 03:55:53 -0700") == datetime.datetime(2017, 9, 6, 3, 55, 53, tzinfo=tzoffset(None, -25200))
    assert dateuil_spy.call_count == 1


def test_ensure_datetime():
    dt = time_utils.ensure_datetime(time_utils.ensure_datetime("2017-11-13T12:15"))
    assert dt == datetime.datetime(2017, 11, 13, 12, 15)


def test_ensure_datetime_with_default_tz():
    dt = time_utils.ensure_datetime(time_utils.ensure_datetime("2017-11-13T12:15"), "UTC")
    assert dt == datetime.datetime(2017, 11, 13, 12, 15, tzinfo=pytz.utc)


def test_date_parse_default():
    assert datetime.date(2017, 11, 2) == time_utils.date_parse('2017-11-02')


def test_date_parse_not_matching():
    assert datetime.date(2017, 11, 2) == time_utils.date_parse('2017/11/02')


def test_get_next_business_day():
    assert time_utils.get_next_business_day(datetime.date(2018, 2, 14)) == datetime.date(2018, 2, 15)
    assert time_utils.get_next_business_day(datetime.date(2018, 2, 16)) == datetime.date(2018, 2, 19)
    assert time_utils.get_next_business_day(datetime.date(2018, 2, 17)) == datetime.date(2018, 2, 19)
    assert time_utils.get_next_business_day(datetime.date(2018, 2, 18)) == datetime.date(2018, 2, 19)


def test_get_previous_business_day():
    assert time_utils.get_previous_business_day(datetime.date(2018, 2, 14)) == datetime.date(2018, 2, 13)
    assert time_utils.get_previous_business_day(datetime.date(2018, 2, 12)) == datetime.date(2018, 2, 9)
    assert time_utils.get_previous_business_day(datetime.date(2018, 2, 11)) == datetime.date(2018, 2, 9)
    assert time_utils.get_previous_business_day(datetime.date(2018, 2, 10)) == datetime.date(2018, 2, 9)


def test_get_next_even_15_minutes():
    f = time_utils.get_next_even_15_minutes
    tz = pytz.timezone('Europe/Helsinki')
    assert f(datetime.datetime(2018, 2, 15, 12, 38, 0)) == datetime.datetime(2018, 2, 15, 12, 45)
    assert f(datetime.datetime(2018, 2, 15, 12, 45, 0)) == datetime.datetime(2018, 2, 15, 12, 45, 0)
    assert f(datetime.datetime(2018, 2, 15, 12, 46, 0)) == datetime.datetime(2018, 2, 15, 13, 0, 0)
    assert f(datetime.datetime(2018, 2, 15, 13, 14, 0)) == datetime.datetime(2018, 2, 15, 13, 15, 0)
    assert f(datetime.datetime(2018, 2, 15, 13, 22, 0)) == datetime.datetime(2018, 2, 15, 13, 30, 0)
    assert f(datetime.datetime(2018, 2, 15, 23, 48, 0)) == datetime.datetime(2018, 2, 16, 0, 0, 0)
    assert f(datetime.datetime(2018, 2, 15, 12, 38, 0, tzinfo=tz)) == datetime.datetime(2018, 2, 15, 12, 45, tzinfo=tz)


def test_get_maybe_tz_from_date_objects_no_tz():
    assert time_utils.get_maybe_tz_from_date_objects(datetime.date(2018, 11, 3), datetime.datetime(2014, 12, 3, 5)) == pytz.utc


def test_get_maybe_tz_from_date_objects_tz():
    assert time_utils.get_maybe_tz_from_date_objects(datetime.date(2018, 11, 3), datetime.datetime(2014, 12, 3, 5, tzinfo=pytz.timezone('Europe/Helsinki'))) == pytz.timezone('Europe/Helsinki')


def test_ensure_date_objects_are_comparable():
    d1 = datetime.date(2018, 11, 3)
    d2 = datetime.datetime(2014, 12, 3, 5, tzinfo=pytz.timezone('Europe/Helsinki'))
    d3 = datetime.datetime(2014, 12, 3, 9)
    d4 = datetime.datetime(2014, 12, 3, 5, tzinfo=pytz.utc)
    r1, r2, r3, r4 = time_utils.ensure_date_objects_are_comparable(d1, d2, d3, d4)
    assert r1 == time_utils.localize(datetime.datetime(2018, 11, 3, 0, 0, 0), 'Europe/Helsinki')
    assert r2 == d2
    assert r3 == time_utils.localize(datetime.datetime(2014, 12, 3, 9), 'Europe/Helsinki')
    assert r4 == d4


def test_first_moment_of_month():
    ret = time_utils.first_moment_of_month(2018, 11, 'Europe/Helsinki')
    assert ret == pytz.timezone('Europe/Helsinki').localize(datetime.datetime(2018, 11, 1, 0, 0, 0))


def test_last_moment_of_month():
    ret = time_utils.last_moment_of_month(2018, 11, 'Europe/Helsinki')
    assert ret == pytz.timezone('Europe/Helsinki').localize(datetime.datetime(2018, 11, 30, 23, 59, 59))
