import filters


def test_filter_connections():
    ftype = filters.filterTypes.index(filters.ConnectionsFilter)
    enabled = 1
    params = ["<"  # '<', '=', '>'
             ,"i"  # 'i', 'o'
             ,'1000']
    encoded = "{0};{1};{2}".format(ftype, enabled, ";".join(params))
    filter = filters.readEncoded(encoded)[0]
    assert type(filter.where()) is str
    assert type(filter.having()) is str


def test_filter_env():
    ftype = filters.filterTypes.index(filters.EnvFilter)
    enabled = 1
    params = ["dev"]
    encoded = "{0};{1};{2}".format(ftype, enabled, ";".join(params))
    filter = filters.readEncoded(encoded)[0]
    assert type(filter.where()) is str
    assert type(filter.having()) is str


def test_filter_mask():
    ftype = filters.filterTypes.index(filters.MaskFilter)
    enabled = 1
    params = ["21.66.116"]
    encoded = "{0};{1};{2}".format(ftype, enabled, ";".join(params))
    filter = filters.readEncoded(encoded)[0]
    assert type(filter.where()) is str
    assert type(filter.having()) is str


def test_filter_port():
    ftype = filters.filterTypes.index(filters.PortFilter)
    enabled = 1
    params = ["2"
             ,"443"]
    encoded = "{0};{1};{2}".format(ftype, enabled, ";".join(params))
    filter = filters.readEncoded(encoded)[0]
    assert type(filter.where()) is str
    assert type(filter.having()) is str


def test_filter_role():
    ftype = filters.filterTypes.index(filters.RoleFilter)
    enabled = 1
    params = [">"
             ,"0.75"]
    encoded = "{0};{1};{2}".format(ftype, enabled, ";".join(params))
    filter = filters.readEncoded(encoded)[0]
    assert type(filter.where()) is str
    assert type(filter.having()) is str


def test_filter_subnet():
    ftype = filters.filterTypes.index(filters.SubnetFilter)
    enabled = 1
    params = ["24"]
    encoded = "{0};{1};{2}".format(ftype, enabled, ";".join(params))
    filter = filters.readEncoded(encoded)[0]
    assert type(filter.where()) is str
    assert type(filter.having()) is str


def test_filter_tags():
    ftype = filters.filterTypes.index(filters.TagsFilter)
    enabled = 1
    params = ["1"
             ,"a,b,c"]
    encoded = "{0};{1};{2}".format(ftype, enabled, ";".join(params))
    filter = filters.readEncoded(encoded)[0]
    assert type(filter.where()) is str
    assert type(filter.having()) is str


def test_filter_target():
    ftype = filters.filterTypes.index(filters.TargetFilter)
    enabled = 1
    params = ["21.66.116"
             ,"3"]
    encoded = "{0};{1};{2}".format(ftype, enabled, ";".join(params))
    filter = filters.readEncoded(encoded)[0]
    assert type(filter.where()) is str
    assert type(filter.having()) is str


def test_multiple_filters():
    encoded = "|".join(["0;1;<;i;1000", "1;1;dev", "2;1;21.66.116", "3;1;2;443", "4;1;>;0.75", "5;1;24", "6;1;1;a,b,c", "6;1;21.66.116;3"])
    all_filters = filters.readEncoded(encoded)
