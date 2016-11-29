import dbaccess
from datetime import datetime
import time
import common


def make_timestamp(ts):
    d = datetime.strptime(ts, "%Y-%m-%d %H:%M")
    ts = time.mktime(d.timetuple())
    return int(ts)


def test_get_details_summary():
    details = dbaccess.get_details_summary(*common.determine_range(21)[:2])
    assert details['unique_in'] == 13322L
    assert details['unique_out'] == 2398L
    assert details['unique_ports'] == 20370L

    details = dbaccess.get_details_summary(*common.determine_range(21, 66)[:2])
    assert details['unique_in'] == 13322L
    assert details['unique_out'] == 2398L
    assert details['unique_ports'] == 20370L

    details = dbaccess.get_details_summary(*common.determine_range(21, 66, 10)[:2])
    assert details['unique_in'] == 2798L
    assert details['unique_out'] == 1
    assert details['unique_ports'] == 3463L

    details = dbaccess.get_details_summary(*common.determine_range(21, 66, 10, 70)[:2])
    assert details['unique_in'] == 28
    assert details['unique_out'] == 0
    assert details['unique_ports'] == 29

    details = dbaccess.get_details_summary(*common.determine_range(21, 66, 40, 231)[:2])
    assert details['unique_in'] == 7
    assert details['unique_out'] == 30
    assert details['unique_ports'] == 1


def test_get_details_summary_ports():
    ip_start, ip_end, _ = common.determine_range(21, 66, 40, 231)
    details = dbaccess.get_details_summary(ip_start, ip_end, port=445)
    assert details['unique_in'] == 7
    assert details['unique_out'] == 0
    assert details['unique_ports'] == 1

    details = dbaccess.get_details_summary(ip_start, ip_end, port=80)
    assert details['unique_in'] == 0
    assert details['unique_out'] == 2
    assert details['unique_ports'] == 0

    details = dbaccess.get_details_summary(ip_start, ip_end, port=1)
    assert details['unique_in'] == 0
    assert details['unique_out'] == 0
    assert details['unique_ports'] == 0


def test_get_details_summary_timerange():
    time_all = (1, 2 ** 31 - 1)
    time_crop = (make_timestamp('2016-06-21 17:10'), make_timestamp('2016-06-21 18:05'))
    time_tiny = (make_timestamp('2016-06-21 17:45'), make_timestamp('2016-06-21 17:50'))
    ip_start, ip_end, _ = common.determine_range(21, 66, 40, 231)
    ip_start2, ip_end2, _ = common.determine_range(79, 35, 103, 221)

    details = dbaccess.get_details_summary(ip_start, ip_end, timestamp_range=time_all)
    assert details['unique_in'] == 7
    assert details['unique_out'] == 30
    assert details['unique_ports'] == 1

    details = dbaccess.get_details_summary(ip_start, ip_end, timestamp_range=time_crop)
    assert details['unique_in'] == 7
    assert details['unique_out'] == 30
    assert details['unique_ports'] == 1

    details = dbaccess.get_details_summary(ip_start2, ip_end2, timestamp_range=time_crop)
    assert details['unique_in'] == 1
    assert details['unique_out'] == 0
    assert details['unique_ports'] == 1

    details = dbaccess.get_details_summary(ip_start, ip_end, timestamp_range=time_tiny)
    assert details['unique_in'] == 3
    assert details['unique_out'] == 15
    assert details['unique_ports'] == 1


def test_get_details_conn():
    ipstart, ipend, _ = common.determine_range(21)
    details = dbaccess.get_details_connections(ipstart, ipend, True)
    assert len(details) == 50
    details = dbaccess.get_details_connections(ipstart, ipend, False)
    assert len(details) == 50

    ipstart, ipend, _ = common.determine_range(21, 66)
    details = dbaccess.get_details_connections(ipstart, ipend, True)
    assert len(details) == 50
    details = dbaccess.get_details_connections(ipstart, ipend, False)
    assert len(details) == 50

    ipstart, ipend, _ = common.determine_range(21, 66, 10)
    details = dbaccess.get_details_connections(ipstart, ipend, True)
    assert len(details) == 50
    details = dbaccess.get_details_connections(ipstart, ipend, False)
    assert len(details) == 1

    ipstart, ipend, _ = common.determine_range(21, 66, 10, 70)
    details = dbaccess.get_details_connections(ipstart, ipend, True)
    assert len(details) == 50
    details = dbaccess.get_details_connections(ipstart, ipend, False)
    assert len(details) == 0

    ipstart, ipend, _ = common.determine_range(21, 66, 40, 231)
    details = dbaccess.get_details_connections(ipstart, ipend, True)
    assert len(details) == 7
    details = dbaccess.get_details_connections(ipstart, ipend, False)
    assert len(details) == 50


def test_get_details_conn_ports():
    ipstart, ipend, _ = common.determine_range(21, 66, 40, 231)
    details = dbaccess.get_details_connections(ipstart, ipend, True, port=445)
    assert len(details) == 7
    details = dbaccess.get_details_connections(ipstart, ipend, False, port=445)
    assert len(details) == 0

    details = dbaccess.get_details_connections(ipstart, ipend, True, port=80)
    assert len(details) == 0
    details = dbaccess.get_details_connections(ipstart, ipend, False, port=80)
    assert len(details) == 2

    details = dbaccess.get_details_connections(ipstart, ipend, True, port=1)
    assert len(details) == 0
    details = dbaccess.get_details_connections(ipstart, ipend, False, port=1)
    assert len(details) == 0


def test_get_details_conn_timerange():
    time_all = (1, 2 ** 31 - 1)
    time_crop = (make_timestamp('2016-06-21 17:10'), make_timestamp('2016-06-21 18:05'))
    time_tiny = (make_timestamp('2016-06-21 17:45'), make_timestamp('2016-06-21 17:50'))
    ipstart, ipend, _ = common.determine_range(21, 66, 40, 231)
    ipstart2, ipend2, _ = common.determine_range(79, 35, 103, 221)

    details = dbaccess.get_details_connections(ipstart, ipend, True, timestamp_range=time_all)
    assert len(details) == 7
    details = dbaccess.get_details_connections(ipstart, ipend, False, timestamp_range=time_all)
    assert len(details) == 50

    details = dbaccess.get_details_connections(ipstart, ipend, True, timestamp_range=time_crop)
    assert len(details) == 7
    details = dbaccess.get_details_connections(ipstart, ipend, False, timestamp_range=time_crop)
    assert len(details) == 50

    details = dbaccess.get_details_connections(ipstart, ipend, True, timestamp_range=time_tiny)
    assert len(details) == 3
    details = dbaccess.get_details_connections(ipstart, ipend, False, timestamp_range=time_tiny)
    assert len(details) == 27

    details = dbaccess.get_details_connections(ipstart2, ipend2, True, timestamp_range=time_crop)
    assert len(details) == 1
    details = dbaccess.get_details_connections(ipstart2, ipend2, False, timestamp_range=time_crop)
    assert len(details) == 0


def test_get_details_ports():
    time_all = (1, 2 ** 31 - 1)
    time_crop = (make_timestamp('2016-06-21 17:10'), make_timestamp('2016-06-21 18:05'))
    time_tiny = (make_timestamp('2016-06-21 17:45'), make_timestamp('2016-06-21 17:50'))
    ipstart1, ipend1, _ = common.determine_range(21, 66, 40, 231)
    ipstart2, ipend2, _ = common.determine_range(79, 35, 103, 221)

    ipstart, ipend, _ = common.determine_range(21)
    details = dbaccess.get_details_ports(ipstart, ipend)
    assert len(details) == 50
    ipstart, ipend, _ = common.determine_range(21, 66)
    details = dbaccess.get_details_ports(ipstart, ipend)
    assert len(details) == 50
    ipstart, ipend, _ = common.determine_range(21, 66, 10)
    details = dbaccess.get_details_ports(ipstart, ipend)
    assert len(details) == 50
    ipstart, ipend, _ = common.determine_range(21, 66, 10, 70)
    details = dbaccess.get_details_ports(ipstart, ipend)
    assert len(details) == 29
    details = dbaccess.get_details_ports(ipstart1, ipend1)
    assert len(details) == 1

    details = dbaccess.get_details_ports(ipstart1, ipend1, port=445)
    assert len(details) == 1
    details = dbaccess.get_details_ports(ipstart1, ipend1, port=80)
    assert len(details) == 0
    details = dbaccess.get_details_ports(ipstart1, ipend1, port=1)
    assert len(details) == 0

    details = dbaccess.get_details_ports(ipstart1, ipend1, timestamp_range=time_all)
    assert len(details) == 1
    details = dbaccess.get_details_ports(ipstart1, ipend1, timestamp_range=time_crop)
    assert len(details) == 1
    details = dbaccess.get_details_ports(ipstart1, ipend1, timestamp_range=time_tiny)
    assert len(details) == 1
    details = dbaccess.get_details_ports(ipstart2, ipend2, timestamp_range=time_crop)
    assert len(details) == 1


def test_get_details_children():
    ipstart1, ipend1, _ = common.determine_range(79)
    ipstart2, ipend2, _ = common.determine_range(79, 35)
    ipstart3, ipend3, _ = common.determine_range(79, 35, 103)
    details = dbaccess.get_details_children(ipstart1, ipend1, 1, 256, "ipstart")
    assert len(details) == 8
    details = dbaccess.get_details_children(ipstart2, ipend2, 1, 256, "ipstart")
    assert len(details) == 45
    details = dbaccess.get_details_children(ipstart3, ipend3, 1, 256, "ipstart")
    assert len(details) == 94
