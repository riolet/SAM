from spec.python import db_connection
import sam.models.filters

db = db_connection.db
sub_id = db_connection.default_sub
ds = db_connection.dsid_default
enabled = 1


def test_filter_connections():
    ftype = sam.models.filters.filterTypes.index(sam.models.filters.ConnectionsFilter)
    params = ["<",  # '<', '=', '>'
              "i",  # 'i', 'o'
              '1000']
    encoded = "ds{0}|{1};{2};{3}".format(ds, ftype, enabled, ";".join(params))
    dsid, filters = sam.models.filters.readEncoded(db, encoded)
    filter = filters[0]

    expected = sam.models.filters.ConnectionsFilter(enabled, *params)
    assert dsid == ds
    assert type(filter.where(db)) is str
    assert type(filter.having(db)) is str
    assert filter == expected


def test_filter_env():
    ftype = sam.models.filters.filterTypes.index(sam.models.filters.EnvFilter)
    params = ["dev"]
    encoded = "ds{0}|{1};{2};{3}".format(ds, ftype, enabled, ";".join(params))
    dsid, filters = sam.models.filters.readEncoded(db, encoded)
    filter = filters[0]

    expected = sam.models.filters.EnvFilter(enabled, *params)
    assert dsid == ds
    assert type(filter.where(db)) is str
    assert type(filter.having(db)) is str
    assert filter == expected


def test_filter_mask():
    ftype = sam.models.filters.filterTypes.index(sam.models.filters.MaskFilter)
    params = ["21.66.116"]
    encoded = "ds{0}|{1};{2};{3}".format(ds, ftype, enabled, ";".join(params))
    dsid, filters = sam.models.filters.readEncoded(db, encoded)
    filter = filters[0]

    expected = sam.models.filters.MaskFilter(enabled, *params)
    assert dsid == ds
    assert type(filter.where(db)) is str
    assert type(filter.having(db)) is str
    assert filter == expected


def test_filter_port():
    ftype = sam.models.filters.filterTypes.index(sam.models.filters.PortFilter)
    params = ["2",
              "443"]
    encoded = "ds{0}|{1};{2};{3}".format(ds, ftype, enabled, ";".join(params))
    dsid, filters = sam.models.filters.readEncoded(db, encoded)
    filter = filters[0]

    expected = sam.models.filters.PortFilter(enabled, *params)
    assert dsid == ds
    assert type(filter.where(db)) is str
    assert type(filter.having(db)) is str
    assert filter == expected


def test_filter_protocol():
    ftype = sam.models.filters.filterTypes.index(sam.models.filters.ProtocolFilter)
    params = ['2',  # direction/existence: '0','1','2','3'
              'UDP']  # protocol string: 'TCP', 'UDP', ...
    encoded = "ds{0}|{1};{2};{3}".format(ds, ftype, enabled, ";".join(params))
    dsid, filters = sam.models.filters.readEncoded(db, encoded)
    filter = filters[0]

    expected = sam.models.filters.ProtocolFilter(enabled, *params)
    assert dsid == ds
    assert type(filter.where(db)) is str
    assert type(filter.having(db)) is str
    assert filter == expected


def test_filter_role():
    ftype = sam.models.filters.filterTypes.index(sam.models.filters.RoleFilter)
    params = [">",
              "0.75"]
    encoded = "ds{0}|{1};{2};{3}".format(ds, ftype, enabled, ";".join(params))
    dsid, filters = sam.models.filters.readEncoded(db, encoded)
    filter = filters[0]

    expected = sam.models.filters.RoleFilter(enabled, *params)
    assert dsid == ds
    assert type(filter.where(db)) is str
    assert type(filter.having(db)) is str
    assert filter == expected


def test_filter_subnet():
    ftype = sam.models.filters.filterTypes.index(sam.models.filters.SubnetFilter)
    params = ["24"]
    encoded = "ds{0}|{1};{2};{3}".format(ds, ftype, enabled, ";".join(params))
    dsid, filters = sam.models.filters.readEncoded(db, encoded)
    filter = filters[0]

    expected = sam.models.filters.SubnetFilter(enabled, *params)
    assert dsid == ds
    assert type(filter.where(db)) is str
    assert type(filter.having(db)) is str
    assert filter == expected


def test_filter_tags():
    ftype = sam.models.filters.filterTypes.index(sam.models.filters.TagsFilter)
    params = ["1",
              "a,b,c"]
    encoded = "ds{0}|{1};{2};{3}".format(ds, ftype, enabled, ";".join(params))
    dsid, filters = sam.models.filters.readEncoded(db, encoded)
    filter = filters[0]

    expected = sam.models.filters.TagsFilter(enabled, *params)
    assert dsid == ds
    assert type(filter.where(db)) is str
    assert type(filter.having(db)) is str
    assert filter == expected


def test_filter_target():
    ftype = sam.models.filters.filterTypes.index(sam.models.filters.TargetFilter)
    params = ["21.66.116",
              "3"]
    encoded = "ds{0}|{1};{2};{3}".format(ds, ftype, enabled, ";".join(params))
    dsid, filters = sam.models.filters.readEncoded(db, encoded)
    filter = filters[0]

    expected = sam.models.filters.TargetFilter(enabled, *params)
    assert dsid == ds
    assert type(filter.where(db)) is str
    assert type(filter.having(db)) is str
    assert filter == expected


def test_multiple_filters():
    conn_f = sam.models.filters.filterTypes.index(sam.models.filters.ConnectionsFilter)
    env_f = sam.models.filters.filterTypes.index(sam.models.filters.EnvFilter)
    mask_f = sam.models.filters.filterTypes.index(sam.models.filters.MaskFilter)
    port_f = sam.models.filters.filterTypes.index(sam.models.filters.PortFilter)
    role_f = sam.models.filters.filterTypes.index(sam.models.filters.RoleFilter)
    subnet_f = sam.models.filters.filterTypes.index(sam.models.filters.SubnetFilter)
    tags_f = sam.models.filters.filterTypes.index(sam.models.filters.TagsFilter)
    target_f = sam.models.filters.filterTypes.index(sam.models.filters.TargetFilter)
    encoded = "|".join(["{conn};1;<;i;1000".format(conn=conn_f),
                        "{env};1;dev".format(env=env_f),
                        "{mask};1;21.66.116".format(mask=mask_f),
                        "{port};1;2;443".format(port=port_f),
                        "{role};1;>;0.75".format(role=role_f),
                        "{subnet};1;24".format(subnet=subnet_f),
                        "{tags};1;1;a,b,c".format(tags=tags_f),
                        "{target};1;21.66.116;3".format(target=target_f)])
    encoded = "ds{0}|{1}".format(ds, encoded)
    dsid, all_filters = sam.models.filters.readEncoded(db, encoded)
    assert dsid == ds
    assert len(all_filters) == 8
    for filter in all_filters:
        assert isinstance(filter, sam.models.filters.Filter)

def test_disabled():
    encoded = "ds1|1;0;production|7;0;1;48GB|3;0;2;443"
    dsid, all_filters = sam.models.filters.readEncoded(db, encoded)
    assert len(all_filters) == 3
    for filter in all_filters:
        assert isinstance(filter, sam.models.filters.Filter)
    assert all_filters[0].enabled == False
    assert all_filters[1].enabled == False
    assert all_filters[2].enabled == False


