import models.filters

ds = 1
enabled = 1


def test_filter_connections():
    ftype = models.filters.filterTypes.index(models.filters.ConnectionsFilter)
    params = ["<",  # '<', '=', '>'
              "i",  # 'i', 'o'
              '1000']
    encoded = "ds{0}|{1};{2};{3}".format(ds, ftype, enabled, ";".join(params))
    dsid, filters = models.filters.readEncoded(encoded)
    filter = filters[0]

    expected = models.filters.ConnectionsFilter(enabled, *params)
    assert dsid == ds
    assert type(filter.where()) is str
    assert type(filter.having()) is str
    assert filter == expected


def test_filter_env():
    ftype = models.filters.filterTypes.index(models.filters.EnvFilter)
    params = ["dev"]
    encoded = "ds{0}|{1};{2};{3}".format(ds, ftype, enabled, ";".join(params))
    dsid, filters = models.filters.readEncoded(encoded)
    filter = filters[0]

    expected = models.filters.EnvFilter(enabled, *params)
    assert dsid == ds
    assert type(filter.where()) is str
    assert type(filter.having()) is str
    assert filter == expected



def test_filter_mask():
    ftype = models.filters.filterTypes.index(models.filters.MaskFilter)
    params = ["21.66.116"]
    encoded = "ds{0}|{1};{2};{3}".format(ds, ftype, enabled, ";".join(params))
    dsid, filters = models.filters.readEncoded(encoded)
    filter = filters[0]

    expected = models.filters.MaskFilter(enabled, *params)
    assert dsid == ds
    assert type(filter.where()) is str
    assert type(filter.having()) is str
    assert filter == expected


def test_filter_port():
    ftype = models.filters.filterTypes.index(models.filters.PortFilter)
    params = ["2",
              "443"]
    encoded = "ds{0}|{1};{2};{3}".format(ds, ftype, enabled, ";".join(params))
    dsid, filters = models.filters.readEncoded(encoded)
    filter = filters[0]

    expected = models.filters.PortFilter(enabled, *params)
    assert dsid == ds
    assert type(filter.where()) is str
    assert type(filter.having()) is str
    assert filter == expected


def test_filter_protocol():
    ftype = models.filters.filterTypes.index(models.filters.ProtocolFilter)
    params = ['2',  # direction/existence: '0','1','2','3'
              'UDP']  # protocol string: 'TCP', 'UDP', ...
    encoded = "ds{0}|{1};{2};{3}".format(ds, ftype, enabled, ";".join(params))
    dsid, filters = models.filters.readEncoded(encoded)
    filter = filters[0]

    expected = models.filters.ProtocolFilter(enabled, *params)
    assert dsid == ds
    assert type(filter.where()) is str
    assert type(filter.having()) is str
    assert filter == expected


def test_filter_role():
    ftype = models.filters.filterTypes.index(models.filters.RoleFilter)
    params = [">",
              "0.75"]
    encoded = "ds{0}|{1};{2};{3}".format(ds, ftype, enabled, ";".join(params))
    dsid, filters = models.filters.readEncoded(encoded)
    filter = filters[0]

    expected = models.filters.RoleFilter(enabled, *params)
    assert dsid == ds
    assert type(filter.where()) is str
    assert type(filter.having()) is str
    assert filter == expected


def test_filter_subnet():
    ftype = models.filters.filterTypes.index(models.filters.SubnetFilter)
    enabled = 1
    params = ["24"]
    encoded = "ds{0}|{1};{2};{3}".format(ds, ftype, enabled, ";".join(params))
    dsid, filters = models.filters.readEncoded(encoded)
    filter = filters[0]

    expected = models.filters.SubnetFilter(enabled, *params)
    assert dsid == ds
    assert type(filter.where()) is str
    assert type(filter.having()) is str
    assert filter == expected


def test_filter_tags():
    ftype = models.filters.filterTypes.index(models.filters.TagsFilter)
    params = ["1",
              "a,b,c"]
    encoded = "ds{0}|{1};{2};{3}".format(ds, ftype, enabled, ";".join(params))
    dsid, filters = models.filters.readEncoded(encoded)
    filter = filters[0]

    expected = models.filters.TagsFilter(enabled, *params)
    assert dsid == ds
    assert type(filter.where()) is str
    assert type(filter.having()) is str
    assert filter == expected


def test_filter_target():
    ftype = models.filters.filterTypes.index(models.filters.TargetFilter)
    params = ["21.66.116",
              "3"]
    encoded = "ds{0}|{1};{2};{3}".format(ds, ftype, enabled, ";".join(params))
    dsid, filters = models.filters.readEncoded(encoded)
    filter = filters[0]

    expected = models.filters.TargetFilter(enabled, *params)
    assert dsid == ds
    assert type(filter.where()) is str
    assert type(filter.having()) is str
    assert filter == expected


def test_multiple_filters():
    conn_f = models.filters.filterTypes.index(models.filters.ConnectionsFilter)
    env_f = models.filters.filterTypes.index(models.filters.EnvFilter)
    mask_f = models.filters.filterTypes.index(models.filters.MaskFilter)
    port_f = models.filters.filterTypes.index(models.filters.PortFilter)
    role_f = models.filters.filterTypes.index(models.filters.RoleFilter)
    subnet_f = models.filters.filterTypes.index(models.filters.SubnetFilter)
    tags_f = models.filters.filterTypes.index(models.filters.TagsFilter)
    target_f = models.filters.filterTypes.index(models.filters.TargetFilter)
    encoded = "|".join(["{conn};1;<;i;1000".format(conn=conn_f),
                        "{env};1;dev".format(env=env_f),
                        "{mask};1;21.66.116".format(mask=mask_f),
                        "{port};1;2;443".format(port=port_f),
                        "{role};1;>;0.75".format(role=role_f),
                        "{subnet};1;24".format(subnet=subnet_f),
                        "{tags};1;1;a,b,c".format(tags=tags_f),
                        "{target};1;21.66.116;3".format(target=target_f)])
    encoded = "ds{0}|{1}".format(ds, encoded)
    dsid, all_filters = models.filters.readEncoded(encoded)
    assert dsid == ds
    assert len(all_filters) == 8
    for filter in all_filters:
        assert isinstance(filter, models.filters.Filter)
