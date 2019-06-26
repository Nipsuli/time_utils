import sys
import re
import pytz
import datetime
import calendar
import logging
from functools import partial
from tzlocal import windows_tz
from dateutil import parser as dateutil_parser
from dateutil.relativedelta import relativedelta
from dateutil.tz import tzoffset


logger = logging.getLogger(__name__)


ISO8601_DURATION = re.compile(
    r"^(?P<sign>[+-])?"
    r"P(?!\b)"
    r"(?P<years>[0-9]+([,.][0-9]+)?Y)?"
    r"(?P<months>[0-9]+([,.][0-9]+)?M)?"
    r"(?P<weeks>[0-9]+([,.][0-9]+)?W)?"
    r"(?P<days>[0-9]+([,.][0-9]+)?D)?"
    r"((?P<separator>T)(?P<hours>[0-9]+([,.][0-9]+)?H)?"
    r"(?P<minutes>[0-9]+([,.][0-9]+)?M)?"
    r"(?P<seconds>[0-9]+([,.][0-9]+)?S)?)?$"
)


# microsoft has their own timezone index ¿ⓧ_ⓧﮌ supporting those as well
# https://docs.microsoft.com/en-us/windows-hardware/manufacture/desktop/default-time-zones

def timezone_to_microsoft_timezone(tz):
    return windows_tz.tz_win[tz]


def microsoft_timezone_to_timezone(tz):
    return windows_tz.win_tz[tz]


def ensure_tz_object(tz_string_or_tz_obj):
    if isinstance(tz_string_or_tz_obj, datetime.tzinfo):
        return tz_string_or_tz_obj
    try:
        return pytz.timezone(tz_string_or_tz_obj)
    except pytz.exceptions.UnknownTimeZoneError as e:
        error = False
        try:
            tz = microsoft_timezone_to_timezone(tz_string_or_tz_obj)
        except KeyError:
            error = True
        if error:
            raise e
        return pytz.timezone(tz)


def get_current_utc_offset(tz_string_or_tz_obj):
    return int(ensure_tz_object(tz_string_or_tz_obj).utcoffset(datetime.datetime.utcnow()).total_seconds() / 3600)


def today(tz_string_or_tz_obj):
    return datetime.datetime.now(ensure_tz_object(tz_string_or_tz_obj)).date()


def now(tz_string_or_tz_obj='UTC'):
    return astimezone(datetime.datetime.now(pytz.utc), tz_string_or_tz_obj)


def astimezone(datetime_obj, tz_string_or_tz_obj):
    return datetime_obj.astimezone(ensure_tz_object(tz_string_or_tz_obj))


def min_datetime():
    return datetime.datetime(1, 1, 1, 0, 0, 0, tzinfo=pytz.utc)


def max_datetime():
    return datetime.datetime(9999, 12, 31, 23, 59, 59, 999999, tzinfo=pytz.utc)


def datetime_from_timestamp(timestamp, tz_string_or_tz_obj=None, is_ms=False):
    tz = ensure_tz_object(tz_string_or_tz_obj or 'UTC')
    if is_ms:
        timestamp /= 1000
    return pytz.utc.localize(datetime.datetime.utcfromtimestamp(timestamp)).astimezone(tz)


def localize(datetime_obj, tz_string_or_tz_obj, overwrite=False):
    tz = ensure_tz_object(tz_string_or_tz_obj)
    if overwrite:
        return tz.localize(datetime_obj.replace(tzinfo=None))
    else:
        return tz.localize(datetime_obj)


def get_maybe_tz_from_date_objects(*date_objects):
    for date_object in date_objects:
        if type(date_object) == datetime.datetime and date_object.tzinfo:
            return date_object.tzinfo
    return pytz.utc


def ensure_date_objects_are_comparable(*date_objects):
    tz = get_maybe_tz_from_date_objects(*date_objects)
    ret = []
    for date_object in date_objects:
        if type(date_object) == datetime.date:
            ret.append(beginning_of_day(date_object, tz))
        elif not date_object.tzinfo:
            ret.append(localize(date_object, tz))
        else:
            ret.append(date_object)
    return ret


def combine(date_obj, time_obj, tz_string_or_tz_obj):
    dat = datetime.datetime.combine(date_obj, time_obj)
    return localize(dat, tz_string_or_tz_obj, overwrite=True)


def end_of_day(date_obj, tz_string_or_tz_obj):
    return combine(date_obj, datetime.time(hour=23, minute=59, second=59), tz_string_or_tz_obj)


def beginning_of_day(date_obj, tz_string_or_tz_obj):
    return combine(date_obj, datetime.time(hour=0, minute=0, second=0), tz_string_or_tz_obj)


def timedelta(datetime_obj, **kwargs):
    return datetime_obj + datetime.timedelta(**kwargs)


def in_time(**kwargs):
    return timedelta(now(), **kwargs)


def time_ago(**kwargs):
    return in_time(**{k: -1*v for k, v in kwargs.items()})


def date_parse(date_str):
    try:
        if date_str[4] == date_str[7] == '-':
            return datetime.date(int(date_str[:4]), int(date_str[5:7]), int(date_str[8:10]))
    except Exception:
        pass

    return dateutil_parser.parse(date_str).date()


def ensure_tz_info(datetime_obj, default_tz):
    if datetime_obj.tzinfo:
        return datetime_obj
    else:
        return localize(datetime_obj, default_tz)


def ensure_datetime(datetime_or_datetime_str, default_tz=None):
    if type(datetime_or_datetime_str) == datetime.datetime:
        dt = datetime_or_datetime_str
    else:
        dt = datetime_parse(datetime_or_datetime_str)

    if default_tz:
        return ensure_tz_info(dt, default_tz)
    else:
        return dt


def _fromisoformat(datetime_str):
    # TODO: handle also cases where there is only date part or only hour in the time part
    if datetime_str[4] == datetime_str[7] == '-' and datetime_str[10] == 'T' and datetime_str[13] == ':':
        # YYYY-MM-DDThh:mm -part
        seconds = 0
        try:
            if datetime_str[16] == ':':  # has seconds: YYYY-MM-DDThh:mm:ss
                seconds = int(datetime_str[17:19])
        except IndexError:  # YYYY-MM-DDThh:mm
            pass

        ms = 0
        try:
            if datetime_str[19] == '.':  # has fragments: YYYY-MM-DDThh:mm:ss.fff[fff]
                fff = ''
                for f in datetime_str[20:]:
                    if f in '0123456789':
                        fff += f
                    else:
                        break
                if len(fff) == 3:
                    ms = int(fff) * 1000
                elif len(fff) == 6:
                    ms = int(fff)
                else:
                    raise ValueError("Invalid fragment size")

        except IndexError:  # YYYY-MM-DDThh:mm.ss
            pass

        if datetime_str[-1] == 'Z':  # 2017-11-23T12:40:11Z
            tzinfo = pytz.utc
        elif datetime_str[-6] in {'+', '-'}:  # 2017-11-23T12:40:11+03:00
            tzinfo = tzoffset(None, int(f'{datetime_str[-6]}1') * (int(f'{datetime_str[-5:-3]}') * 3600 + int(f'{datetime_str[-2:]}') * 60))
        elif datetime_str[-5] in {'+', '-'}:  # 2017-11-23T12:40:11-0600
            tzinfo = tzoffset(None, int(f'{datetime_str[-5]}1') * (int(f'{datetime_str[-4:-2]}') * 3600 + int(f'{datetime_str[-2:]}') * 60))
        else:  # 2017-11-23T12:40:11
            tzinfo = None
        return datetime.datetime(
            max(1, int(datetime_str[:4])),
            max(1, int(datetime_str[5:7])),
            max(1, int(datetime_str[8:10])),
            int(datetime_str[11:13]),
            int(datetime_str[14:16]),
            seconds,
            ms,
            tzinfo=tzinfo
        )
    else:
        raise ValueError(f'{datetime_str} is not in ISO 8601 format')


def datetime_parse(datetime_str, default_tz=None):
    try:  # ISO 8601
        if sys.version_info[0] == 3 and sys.version_info[1] > 6:
            try:
                dt = datetime.datetime.fromisoformat(datetime_str)
            except Exception:
                # pythons own isoformat parser doesn't support tz info marked with Z or without :
                # it also cannot handle 0000-00-00T00:00:00.000Z
                # TODO: create iso format fixer
                pass

        dt = _fromisoformat(datetime_str)
    except Exception:
        logger.debug(f'Could not use fast datetime parsing on "{datetime_str}" falling back for dateuil parser')
        dt = dateutil_parser.parse(datetime_str)

    if default_tz:
        return ensure_tz_info(dt, default_tz)
    else:
        return dt


def is_business_day(date_obj):
    # mon - fri
    iso_business_days = [1, 2, 3, 4, 5]
    return date_obj.isoweekday() in iso_business_days


def _get_next_timedelta(start_date_obj, increment_fn, predicate_fn):
    next_day = increment_fn(start_date_obj)
    while not predicate_fn(next_day):
        next_day = increment_fn(next_day)
    return next_day


def get_next_business_day(date_obj):
    return _get_next_timedelta(date_obj, partial(timedelta, days=1), is_business_day)


def get_previous_business_day(date_obj):
    return _get_next_timedelta(date_obj, partial(timedelta, days=-1), is_business_day)


def ceil_datetime(datetime_obj, delta=None, **delta_kwargs):
    delta = delta or datetime.timedelta(**delta_kwargs)
    min_datetime = datetime.datetime.min if not datetime_obj.tzinfo else datetime.datetime.min.replace(tzinfo=datetime_obj.tzinfo)
    return datetime_obj + (min_datetime - datetime_obj) % delta


def floor_datetime(datetime_obj, delta=None, **delta_kwargs):
    delta = delta or datetime.timedelta(**delta_kwargs)
    min_datetime = datetime.datetime.min if not datetime_obj.tzinfo else datetime.datetime.min.replace(tzinfo=datetime_obj.tzinfo)
    return datetime_obj - (datetime_obj - min_datetime) % delta


def get_next_even_15_minutes(datetime_obj):
    return ceil_datetime(datetime_obj, datetime.timedelta(minutes=15))


def first_moment_of_month(year, month, timezone):
    return beginning_of_day(datetime.date(year, month, 1), timezone)


def last_moment_of_month(year, month, timezone):
    day = calendar.monthrange(year, month)[1]
    return end_of_day(datetime.date(year, month, day), timezone)


def _parse_single_duration_value(val):
    if val is None:
        return 0
    else:
        # This decimal fraction may be specified with either a comma or a full stop, as in "P0,5Y" or "P0.5Y"
        return float(val[:-1].replace(',', '.'))


def _parse_duration_years(year_val):
    if year_val is None:
        return 0, 0
    else:
        val = _parse_single_duration_value(year_val)
        years = int(val)

        if years == val:
            return years, 0
        else:
            fracs = val - years
            months = fracs * 12
            if int(months) != months:
                raise ValueError(f'Decimal reprecentation "{year_val}" of year is ambiguous, and not supported')
            return years, months


def _parse_duration_months(month_val):
    if month_val is None:
        return 0
    else:
        val = _parse_single_duration_value(month_val)
        if int(val) != val:
            raise ValueError(f'Non-integer month "{month_val}" is ambiguous, and not supported.')
        else:
            return int(val)


def parse_iso_duration(duration_str):
    match = ISO8601_DURATION.match(duration_str)
    if not match:
        # case P<date>T<time>
        if duration_str.startswith('P'):
            try:
                dt = datetime_parse(duration_str[1:])
                return relativedelta(
                    years=dt.year,
                    months=dt.month,
                    days=dt.day,
                    hours=dt.hour,
                    minutes=dt.minute,
                    seconds=dt.second
                )
            except Exception:
                pass

        raise ValueError(f'Could not parse {duration_str}')

    matches = match.groupdict()

    if matches['sign'] == '-':
        sign = -1
    else:
        sign = 1

    years, extra_months = _parse_duration_years(matches['years'])

    return relativedelta(
        years=sign * years,
        months=sign * (_parse_duration_months(matches['months']) + extra_months),
        days=sign * _parse_single_duration_value(matches['days']),
        weeks=sign * _parse_single_duration_value(matches['weeks']),
        hours=sign * _parse_single_duration_value(matches['hours']),
        minutes=sign * _parse_single_duration_value(matches['minutes']),
        seconds=sign * _parse_single_duration_value(matches['seconds'])
    )


def relativedelta_to_timedelta(relativedelta_obj, reference_date=None):
    reference_date = reference_date or now()
    return reference_date + relativedelta_obj - reference_date
